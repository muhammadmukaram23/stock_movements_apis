
from fastapi import APIRouter, HTTPException, status, Depends, Header,Query,Body
from typing import Optional
from app.database import get_connection
from app.models.additionals_reporting import  TableSize,StockMismatch,NegativeStock,InactiveUser,PendingApproval,OverdueTransfer,ReorderAlert,StockTurnover,SeasonalDemand,ItemDemand,BranchPerformance,MonthlyStockMovement,BranchItemPair,TimeRange
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token

router = APIRouter(prefix="/batch_operation", tags=["batch_operation"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# Reporting Endpoints
@router.get("/monthly-stock-movement", response_model=List[MonthlyStockMovement])
async def get_monthly_stock_movement(time_range: TimeRange):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT YEAR(sm.created_at) as year, MONTH(sm.created_at) as month,
                  sm.movement_type, COUNT(*) as movement_count, SUM(sm.quantity) as total_quantity
            FROM stock_movements sm
            WHERE sm.created_at BETWEEN %s AND %s
            GROUP BY YEAR(sm.created_at), MONTH(sm.created_at), sm.movement_type
            ORDER BY year DESC, month DESC, sm.movement_type""",
            (time_range.start_date, time_range.end_date)
        )
        results = cursor.fetchall()
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/branch-performance", response_model=List[BranchPerformance])
async def get_branch_performance():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT b.branch_name,
                  COUNT(DISTINCT tr_out.transfer_id) as transfers_sent,
                  COUNT(DISTINCT tr_in.transfer_id) as transfers_received,
                  AVG(CASE WHEN tr_out.status = 'DELIVERED' 
                      THEN DATEDIFF(tr_out.delivery_date, tr_out.request_date) END) as avg_fulfillment_days,
                  SUM(CASE WHEN tr_out.status = 'REJECTED' THEN 1 ELSE 0 END) as rejections_sent
            FROM branches b
            LEFT JOIN transfer_requests tr_out ON b.branch_id = tr_out.from_branch_id
            LEFT JOIN transfer_requests tr_in ON b.branch_id = tr_in.to_branch_id
            WHERE b.is_active = TRUE
            GROUP BY b.branch_id, b.branch_name
            ORDER BY avg_fulfillment_days""")
        results = cursor.fetchall()
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

# Notification Endpoints
@router.get("/reorder-alerts", response_model=List[ReorderAlert])
async def get_reorder_alerts():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT i.item_name, i.item_code, b.branch_name, 
                  inv.available_stock, i.minimum_stock_level,
                  (i.minimum_stock_level - inv.available_stock) as reorder_quantity
            FROM inventory inv
            JOIN items i ON inv.item_id = i.item_id
            JOIN branches b ON inv.branch_id = b.branch_id
            WHERE inv.available_stock < i.minimum_stock_level
              AND i.is_active = TRUE
            ORDER BY reorder_quantity DESC""")
        results = cursor.fetchall()
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/overdue-transfers", response_model=List[OverdueTransfer])
async def get_overdue_transfers():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT tr.transfer_number, fb.branch_name as from_branch, tb.branch_name as to_branch,
                  tr.request_date, ds.expected_delivery_date,
                  DATEDIFF(NOW(), ds.expected_delivery_date) as days_overdue
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN dispatch_slips ds ON tr.transfer_id = ds.transfer_id
            WHERE tr.status = 'IN_TRANSIT' 
              AND ds.expected_delivery_date < CURDATE()
            ORDER BY days_overdue DESC""")
        results = cursor.fetchall()
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

# Maintenance Endpoints
@router.get("/table-sizes", response_model=List[TableSize])
async def get_table_sizes():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT 'branches' as table_name, COUNT(*) as row_count FROM branches
            UNION ALL SELECT 'users', COUNT(*) FROM users
            UNION ALL SELECT 'items', COUNT(*) FROM items
            UNION ALL SELECT 'inventory', COUNT(*) FROM inventory
            UNION ALL SELECT 'transfer_requests', COUNT(*) FROM transfer_requests
            UNION ALL SELECT 'transfer_request_items', COUNT(*) FROM transfer_request_items
            UNION ALL SELECT 'stock_movements', COUNT(*) FROM stock_movements
            UNION ALL SELECT 'dispatch_slips', COUNT(*) FROM dispatch_slips
            UNION ALL SELECT 'receiving_slips', COUNT(*) FROM receiving_slips
            UNION ALL SELECT 'system_logs', COUNT(*) FROM system_logs""")
        results = cursor.fetchall()
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/reconcile-inventory", status_code=status.HTTP_200_OK)
async def reconcile_inventory(pair: BranchItemPair):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            """UPDATE inventory inv
            SET current_stock = (
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN sm.movement_type IN ('IN', 'TRANSFER_IN') THEN sm.quantity
                        WHEN sm.movement_type IN ('OUT', 'TRANSFER_OUT') THEN -sm.quantity
                        WHEN sm.movement_type = 'ADJUSTMENT' THEN sm.quantity
                        ELSE 0
                    END
                ), 0)
                FROM stock_movements sm
                WHERE sm.item_id = inv.item_id AND sm.branch_id = inv.branch_id
            )
            WHERE inv.item_id = %s AND inv.branch_id = %s""",
            (pair.item_id, pair.branch_id)
        )
        connection.commit()
        return {"message": "Inventory reconciled successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()