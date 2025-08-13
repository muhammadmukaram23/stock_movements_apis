from fastapi import APIRouter, HTTPException, status, Depends, Header,Query
from typing import Optional
from app.database import get_connection
from app.models.dashboard_activity import RecentActivityResponse, DashboardSummaryResponse
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/dashboard_activity", tags=["dashboard_activity"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# Endpoint for dashboard summary
@router.get("/summary/{branch_id}", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM inventory WHERE branch_id = %s AND available_stock > 0) as items_in_stock,
                (SELECT COUNT(*) FROM inventory inv JOIN items i ON inv.item_id = i.item_id 
                 WHERE inv.branch_id = %s AND inv.available_stock <= i.minimum_stock_level) as low_stock_items,
                (SELECT COUNT(*) FROM transfer_requests WHERE to_branch_id = %s AND status = 'PENDING') as pending_requests,
                (SELECT COUNT(*) FROM transfer_requests WHERE from_branch_id = %s AND status = 'APPROVED') as pending_dispatches,
                (SELECT COUNT(*) FROM transfer_requests WHERE to_branch_id = %s AND status = 'IN_TRANSIT') as incoming_shipments
        """, (branch_id, branch_id, branch_id, branch_id, branch_id))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found or no data available"
            )
            
        # Convert None values to 0
        for key in result:
            if result[key] is None:
                result[key] = 0
                
        return result
        
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Endpoint for recent activities
@router.get("/activities/{branch_id}", response_model=List[RecentActivityResponse])
async def get_recent_activities(branch_id: int, limit: int = Query(10, ge=1, le=50)):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 'TRANSFER_REQUEST' as activity_type, tr.transfer_number as reference,
                   CONCAT('Transfer request from ', fb.branch_name, ' to ', tb.branch_name) as description,
                   tr.request_date as activity_date
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            WHERE tr.from_branch_id = %s OR tr.to_branch_id = %s
            UNION ALL
            SELECT 'STOCK_MOVEMENT' as activity_type, CONCAT('SM-', sm.movement_id) as reference,
                   CONCAT(sm.movement_type, ' - ', i.item_name, ' (', sm.quantity, ')') as description,
                   sm.created_at as activity_date
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            WHERE sm.branch_id = %s
            ORDER BY activity_date DESC
            LIMIT %s
        """, (branch_id, branch_id, branch_id, limit))
        
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recent activities found"
            )
            
        return results
        
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()