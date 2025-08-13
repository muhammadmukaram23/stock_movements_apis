from fastapi import APIRouter, HTTPException, status, Depends, Header,Query
from typing import Optional
from app.database import get_connection
from app.models.reports import SystemLogResponse,UserActivityResponse,TransferPerformanceResponse,MostRequestedItemsResponse,TransferSummaryResponse,StockAgingResponse,StockValuationResponse,StockSummaryResponse
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# 9.1 Stock Reports
# Then update your endpoint
@router.get("/stock/summary", response_model=List[StockSummaryResponse])
async def get_stock_summary():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                b.branch_name, 
                COUNT(DISTINCT inv.item_id) as total_items,
                COALESCE(SUM(inv.current_stock), 0) as total_stock,
                COALESCE(SUM(inv.reserved_stock), 0) as total_reserved,
                COALESCE(SUM(inv.available_stock), 0) as total_available,
                COALESCE(SUM(CASE WHEN inv.available_stock <= i.minimum_stock_level THEN 1 ELSE 0 END), 0) as low_stock_items,
                COALESCE(SUM(CASE WHEN inv.available_stock = 0 THEN 1 ELSE 0 END), 0) as out_of_stock_items
            FROM branches b
            LEFT JOIN inventory inv ON b.branch_id = inv.branch_id
            LEFT JOIN items i ON inv.item_id = i.item_id AND i.is_active = TRUE
            WHERE b.is_active = TRUE
            GROUP BY b.branch_id, b.branch_name
            ORDER BY b.branch_name
        """)
        results = cursor.fetchall()
        
        # Debug: Print the results to see what's coming from the database
        print("Database results:", results)
        
        return results
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/stock/valuation", response_model=List[StockValuationResponse])
async def get_stock_valuation():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT b.branch_name, i.item_name, inv.current_stock, i.unit_price,
                   (inv.current_stock * i.unit_price) as total_value
            FROM inventory inv
            JOIN items i ON inv.item_id = i.item_id
            JOIN branches b ON inv.branch_id = b.branch_id
            WHERE i.is_active = TRUE AND b.is_active = TRUE
            ORDER BY total_value DESC
        """)
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/stock/aging", response_model=List[StockAgingResponse])
async def get_stock_aging():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, b.branch_name, inv.current_stock,
                   COALESCE(MAX(sm.created_at), inv.last_updated) as last_movement,
                   DATEDIFF(NOW(), COALESCE(MAX(sm.created_at), inv.last_updated)) as days_since_movement
            FROM inventory inv
            JOIN items i ON inv.item_id = i.item_id
            JOIN branches b ON inv.branch_id = b.branch_id
            LEFT JOIN stock_movements sm ON inv.item_id = sm.item_id AND inv.branch_id = sm.branch_id
            WHERE i.is_active = TRUE AND inv.current_stock > 0
            GROUP BY inv.item_id, inv.branch_id
            HAVING days_since_movement > 90
            ORDER BY days_since_movement DESC
        """)
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 9.2 Transfer Reports
@router.get("/transfer/summary", response_model=List[TransferSummaryResponse])
async def get_transfer_summary(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD format")
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT DATE(tr.request_date) as request_date,
                   COUNT(*) as total_requests,
                   SUM(CASE WHEN tr.status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN tr.status = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN tr.status = 'DELIVERED' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN tr.status = 'REJECTED' THEN 1 ELSE 0 END) as rejected
            FROM transfer_requests tr
            WHERE tr.request_date BETWEEN %s AND %s
            GROUP BY DATE(tr.request_date)
            ORDER BY request_date DESC
        """, (start_date, end_date))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/transfer/most-requested", response_model=List[MostRequestedItemsResponse])
async def get_most_requested_items(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD format")
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, COUNT(*) as request_count, SUM(tri.requested_quantity) as total_requested
            FROM transfer_request_items tri
            JOIN items i ON tri.item_id = i.item_id
            JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
            WHERE tr.request_date BETWEEN %s AND %s
            GROUP BY i.item_id, i.item_name
            ORDER BY request_count DESC, total_requested DESC
        """, (start_date, end_date))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/transfer/performance", response_model=List[TransferPerformanceResponse])
async def get_transfer_performance(
    start_date: date = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: date = Query(..., description="End date in YYYY-MM-DD format")
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT fb.branch_name as from_branch, tb.branch_name as to_branch,
                   COUNT(*) as total_transfers,
                   AVG(DATEDIFF(tr.approval_date, tr.request_date)) as avg_approval_days,
                   AVG(DATEDIFF(tr.dispatch_date, tr.approval_date)) as avg_dispatch_days,
                   AVG(DATEDIFF(tr.delivery_date, tr.dispatch_date)) as avg_delivery_days,
                   AVG(DATEDIFF(tr.delivery_date, tr.request_date)) as avg_total_days
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            WHERE tr.status = 'DELIVERED' 
              AND tr.request_date BETWEEN %s AND %s
            GROUP BY tr.from_branch_id, tr.to_branch_id
            ORDER BY avg_total_days DESC
        """, (start_date, end_date))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 9.3 User Activity Reports
@router.get("/user-activity", response_model=List[UserActivityResponse])
async def get_user_activity():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.full_name, b.branch_name, r.role_name,
                   COUNT(DISTINCT tr.transfer_id) as transfer_requests,
                   COUNT(DISTINCT ds.dispatch_id) as dispatches,
                   COUNT(DISTINCT rs.receiving_id) as receipts,
                   COUNT(DISTINCT sm.movement_id) as stock_movements
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            LEFT JOIN transfer_requests tr ON u.user_id = tr.requested_by
            LEFT JOIN dispatch_slips ds ON u.user_id = ds.dispatched_by
            LEFT JOIN receiving_slips rs ON u.user_id = rs.received_by
            LEFT JOIN stock_movements sm ON u.user_id = sm.created_by
            WHERE u.is_active = TRUE
            GROUP BY u.user_id
            ORDER BY b.branch_name, u.full_name
        """)
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/system-logs", response_model=List[SystemLogResponse])
async def get_system_logs(
    start_date: datetime = Query(..., description="Start datetime in ISO format"),
    end_date: datetime = Query(..., description="End datetime in ISO format"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sl.*, u.full_name as user_name
            FROM system_logs sl
            LEFT JOIN users u ON sl.user_id = u.user_id
            WHERE sl.created_at BETWEEN %s AND %s
            ORDER BY sl.created_at DESC
            LIMIT %s OFFSET %s
        """, (start_date, end_date, limit, offset))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

