from fastapi import APIRouter, HTTPException, status, Depends, Header,Query
from typing import Optional
from app.database import get_connection
from app.models.filter_query import StockMovementSearchResult,TransferRequestSearchResult,MovementType,PriorityLevel,TransferStatus
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/filters", tags=["filters"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# Endpoint for searching transfer requests
# Endpoint for searching transfer requests
@router.get("/transfer-requests", response_model=List[TransferRequestSearchResult])
async def search_transfer_requests(
    status: Optional[TransferStatus] = Query(None),
    from_branch_id: Optional[int] = Query(None),
    to_branch_id: Optional[int] = Query(None),
    priority: Optional[PriorityLevel] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        query = """
            SELECT tr.transfer_id, tr.transfer_number, tr.status, tr.priority,
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as requested_by, tr.request_date
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON tr.requested_by = u.user_id
            WHERE (%s IS NULL OR tr.status = %s)
              AND (%s IS NULL OR tr.from_branch_id = %s)
              AND (%s IS NULL OR tr.to_branch_id = %s)
              AND (%s IS NULL OR tr.priority = %s)
              AND (%s IS NULL OR tr.request_date >= %s)
              AND (%s IS NULL OR tr.request_date <= %s)
            ORDER BY tr.request_date DESC
            LIMIT %s OFFSET %s
        """
        
        # Convert enum values to strings if they exist
        status_str = status.value if status else None
        priority_str = priority.value if priority else None
        
        params = (
            status_str, status_str,
            from_branch_id, from_branch_id,
            to_branch_id, to_branch_id,
            priority_str, priority_str,
            start_date, start_date,
            end_date, end_date,
            limit, offset
        )
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No transfer requests found matching the criteria"
            )
            
        return results
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Endpoint for searching stock movements
@router.get("/stock-movements", response_model=List[StockMovementSearchResult])
async def search_stock_movements(
    item_id: Optional[int] = Query(None),
    branch_id: Optional[int] = Query(None),
    movement_type: Optional[MovementType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        query = """
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE (%s IS NULL OR sm.item_id = %s)
              AND (%s IS NULL OR sm.branch_id = %s)
              AND (%s IS NULL OR sm.movement_type = %s)
              AND (%s IS NULL OR sm.created_at >= %s)
              AND (%s IS NULL OR sm.created_at <= %s)
            ORDER BY sm.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        # Convert enum values to strings if they exist
        movement_type_str = movement_type.value if movement_type else None
        
        params = (
            item_id, item_id,
            branch_id, branch_id,
            movement_type_str, movement_type_str,
            start_date, start_date,
            end_date, end_date,
            limit, offset
        )
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No stock movements found matching the criteria"
            )
            
        return results
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()