from fastapi import APIRouter, HTTPException, status, Depends, Header,Query
from typing import Optional
from app.database import get_connection
from app.models.utility_query import SystemStatisticsResponse,ItemAvailabilityResponse,NextTransferNumberResponse
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/utility_query", tags=["utility_query"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# 1. Generate next transfer number
@router.get("/next-transfer-number", response_model=NextTransferNumberResponse)
async def get_next_transfer_number():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT generate_transfer_number() as next_transfer_number")
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not generate transfer number"
            )
            
        return result
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 2. Check item availability before transfer
@router.get("/check-item-availability", response_model=ItemAvailabilityResponse)
async def check_item_availability(
    item_id: int = Query(..., description="ID of the item to check"),
    branch_id: int = Query(..., description="ID of the branch to check"),
    required_quantity: int = Query(..., description="Quantity needed for transfer")
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, i.item_code, inv.available_stock,
                   CASE WHEN inv.available_stock >= %s THEN 'AVAILABLE' ELSE 'INSUFFICIENT' END as availability_status
            FROM items i
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = %s
            WHERE i.item_id = %s
        """, (required_quantity, branch_id, item_id))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Item not found in specified branch"
            )
            
        return result
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 3. Get system statistics
@router.get("/system-statistics", response_model=SystemStatisticsResponse)
async def get_system_statistics():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM branches WHERE is_active = TRUE) as total_branches,
                (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
                (SELECT COUNT(*) FROM items WHERE is_active = TRUE) as total_items,
                (SELECT COUNT(*) FROM transfer_requests WHERE status = 'PENDING') as pending_transfers,
                (SELECT SUM(current_stock) FROM inventory) as total_stock_units
        """)
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not retrieve system statistics"
            )
            
        # Convert None values to 0 for statistics
        for key in result:
            if result[key] is None:
                result[key] = 0
                
        return result
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 4. Database cleanup (Admin-only endpoint)
@router.delete("/cleanup-system-logs")
async def cleanup_system_logs(
    older_than_days: int = Query(365, description="Delete logs older than this many days", ge=1)
):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM system_logs 
            WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (older_than_days,))
        
        connection.commit()
        
        return {
            "message": f"Successfully cleaned up system logs older than {older_than_days} days",
            "rows_affected": cursor.rowcount
        }
        
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error during cleanup: {e}"
        )
    finally:
        cursor.close()
        connection.close()