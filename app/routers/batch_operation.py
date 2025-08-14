
from fastapi import APIRouter, HTTPException, status, Depends, Header,Query,Body
from typing import Optional
from app.database import get_connection
from app.models.batch_operation import BulkStockAdjustment,BulkTransferApproval,BulkPriceUpdate,BulkMinStockUpdate,StockAdjustmentResponse,BatchResponse
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token

router = APIRouter(prefix="/batch_operation", tags=["batch_operation"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})



@router.post("/update-min-stock", response_model=BatchResponse, status_code=status.HTTP_200_OK)
async def bulk_update_min_stock(update_data: BulkMinStockUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # First get current values for items that will be updated
        cursor.execute(
            "SELECT item_id, item_name, minimum_stock_level as old_value FROM items WHERE category_id = %s",
            (update_data.category_id,)
        )
        items_before = cursor.fetchall()
        
        # Perform the update
        cursor.execute(
            "UPDATE items SET minimum_stock_level = %s WHERE category_id = %s",
            (update_data.minimum_stock_level, update_data.category_id)
        )
        affected_rows = cursor.rowcount
        
        # Get updated values
        cursor.execute(
            "SELECT item_id, item_name, minimum_stock_level as new_value FROM items WHERE category_id = %s",
            (update_data.category_id,)
        )
        items_after = cursor.fetchall()
        
        connection.commit()
        
        # Prepare response data
        updated_data = []
        for before, after in zip(items_before, items_after):
            updated_data.append({
                "item_id": before["item_id"],
                "item_name": before["item_name"],
                "old_min_stock": before["old_value"],
                "new_min_stock": after["new_value"]
            })
        
        return {
            "message": f"Minimum stock levels updated for {affected_rows} items in category {update_data.category_id}",
            "affected_rows": affected_rows,
            "updated_data": updated_data
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/update-prices", response_model=BatchResponse, status_code=status.HTTP_200_OK)
async def bulk_update_prices(update_data: BulkPriceUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get current prices
        cursor.execute(
            "SELECT item_id, item_name, unit_price as old_price FROM items WHERE category_id = %s",
            (update_data.category_id,)
        )
        items_before = cursor.fetchall()
        
        # Perform update
        cursor.execute(
            "UPDATE items SET unit_price = unit_price * (1 + %s / 100) WHERE category_id = %s",
            (update_data.percentage_change, update_data.category_id)
        )
        affected_rows = cursor.rowcount
        
        # Get new prices
        cursor.execute(
            "SELECT item_id, item_name, unit_price as new_price FROM items WHERE category_id = %s",
            (update_data.category_id,)
        )
        items_after = cursor.fetchall()
        
        connection.commit()
        
        # Prepare response data
        updated_data = []
        for before, after in zip(items_before, items_after):
            updated_data.append({
                "item_id": before["item_id"],
                "item_name": before["item_name"],
                "old_price": before["old_price"],
                "new_price": after["new_price"],
                "percentage_change": update_data.percentage_change
            })
        
        return {
            "message": f"Prices updated for {affected_rows} items in category {update_data.category_id}",
            "affected_rows": affected_rows,
            "updated_data": updated_data
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/approve-low-priority-transfers", response_model=BatchResponse, status_code=status.HTTP_200_OK)
async def bulk_approve_transfers(approval_data: BulkTransferApproval):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get transfers before approval (only header info since items are in separate table)
        cursor.execute(
            """SELECT transfer_id, from_branch_id, to_branch_id, status as old_status 
            FROM transfer_requests 
            WHERE status = 'PENDING' AND priority = 'LOW' AND from_branch_id = %s""",
            (approval_data.from_branch_id,)
        )
        transfers_before = cursor.fetchall()
        
        if not transfers_before:
            return {
                "message": "No pending low-priority transfers found for this branch",
                "affected_rows": 0,
                "updated_data": []
            }

        # Perform approval
        cursor.execute(
            """UPDATE transfer_requests 
            SET status = 'APPROVED', approved_by = %s, approval_date = NOW()
            WHERE status = 'PENDING' AND priority = 'LOW' AND from_branch_id = %s""",
            (approval_data.approved_by, approval_data.from_branch_id)
        )
        affected_rows = cursor.rowcount
        
        # Get updated transfers
        cursor.execute(
            """SELECT transfer_id, from_branch_id, to_branch_id, status as new_status, 
                  approved_by, approval_date
            FROM transfer_requests 
            WHERE status = 'APPROVED' AND priority = 'LOW' AND from_branch_id = %s
            AND approved_by = %s AND approval_date >= NOW() - INTERVAL 1 MINUTE""",
            (approval_data.from_branch_id, approval_data.approved_by)
        )
        transfers_after = cursor.fetchall()
        
        connection.commit()
        
        # Prepare response data (without item details)
        updated_data = []
        for before, after in zip(transfers_before, transfers_after):
            updated_data.append({
                "transfer_id": before["transfer_id"],
                "from_branch_id": before["from_branch_id"],
                "to_branch_id": before["to_branch_id"],
                "old_status": before["old_status"],
                "new_status": after["new_status"],
                "approved_by": after["approved_by"],
                "approval_date": after["approval_date"].isoformat() if after["approval_date"] else None
            })
        
        return {
            "message": f"Approved {affected_rows} low priority transfers from branch {approval_data.from_branch_id}",
            "affected_rows": affected_rows,
            "updated_data": updated_data
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/adjust-stock", response_model=StockAdjustmentResponse, status_code=status.HTTP_201_CREATED)
async def bulk_adjust_stock(adjustment: BulkStockAdjustment):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get current stock level
        cursor.execute(
            "SELECT current_stock FROM inventory WHERE item_id = %s AND branch_id = %s",
            (adjustment.item_id, adjustment.branch_id)
        )
        current_stock = cursor.fetchone()["current_stock"]
        
        # Insert stock movement record
        cursor.execute(
            """INSERT INTO stock_movements (item_id, branch_id, movement_type, quantity, 
                previous_stock, new_stock, reference_type, notes, created_by)
            VALUES (%s, %s, 'ADJUSTMENT', %s, %s, %s, 'ADJUSTMENT', 'Physical count adjustment', %s)""",
            (adjustment.item_id, adjustment.branch_id, 
             adjustment.new_stock_level - current_stock,
             current_stock, adjustment.new_stock_level,
             adjustment.created_by)
        )
        movement_id = cursor.lastrowid
        
        # Update inventory
        cursor.execute(
            """UPDATE inventory 
            SET current_stock = %s, updated_by = %s
            WHERE item_id = %s AND branch_id = %s""",
            (adjustment.new_stock_level, adjustment.created_by, 
             adjustment.item_id, adjustment.branch_id)
        )
        affected_rows = cursor.rowcount
        
        connection.commit()
        
        return {
            "message": "Stock adjustment completed successfully",
            "affected_rows": affected_rows,
            "movement_id": movement_id,
            "previous_stock": current_stock,
            "new_stock": adjustment.new_stock_level,
            "updated_data": [{
                "item_id": adjustment.item_id,
                "branch_id": adjustment.branch_id,
                "adjustment_amount": adjustment.new_stock_level - current_stock,
                "created_by": adjustment.created_by
            }]
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()