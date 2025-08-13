from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.dispatch_slip import  DispatchItemResponse,DispatchResponse,DispatchCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/dispatch_slip", tags=["dispatch_slip"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})



# 6.1 Create Dispatch Slip
@router.post("/", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
async def create_dispatch_slip(dispatch: DispatchCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # First get the count for dispatch number generation
        cursor.execute("""
            SELECT COUNT(*) + 1 as next_num 
            FROM dispatch_slips 
            WHERE DATE(dispatch_date) = CURDATE()
        """)
        count_result = cursor.fetchone()
        next_num = str(count_result['next_num']).zfill(4)
        
        # Generate dispatch number
        dispatch_number = f"DS-{datetime.now().strftime('%Y%m%d')}-{next_num}"
        
        # Create dispatch slip
        cursor.execute("""
            INSERT INTO dispatch_slips 
            (dispatch_number, transfer_id, dispatched_by, 
             loader_name, vehicle_info, expected_delivery_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            dispatch_number, dispatch.transfer_id, dispatch.dispatched_by,
            dispatch.loader_name, dispatch.vehicle_info,
            dispatch.expected_delivery_date, dispatch.notes
        ))
        dispatch_id = cursor.lastrowid

        # Update transfer status
        cursor.execute("""
            UPDATE transfer_requests 
            SET status = 'IN_TRANSIT', dispatch_date = NOW()
            WHERE transfer_id = %s
        """, (dispatch.transfer_id,))

        # Update dispatched quantities
        cursor.execute("""
            UPDATE transfer_request_items 
            SET dispatched_quantity = approved_quantity
            WHERE transfer_id = %s
        """, (dispatch.transfer_id,))

        # Reserve stock
        cursor.execute("""
            UPDATE inventory inv
            JOIN transfer_request_items tri ON inv.item_id = tri.item_id
            SET inv.reserved_stock = inv.reserved_stock + tri.approved_quantity
            WHERE inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = %s)
              AND tri.transfer_id = %s
        """, (dispatch.transfer_id, dispatch.transfer_id))

        connection.commit()

        # Return created dispatch slip
        cursor.execute("""
            SELECT ds.*, tr.transfer_number, 
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as dispatched_by_name
            FROM dispatch_slips ds
            JOIN transfer_requests tr ON ds.transfer_id = tr.transfer_id
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON ds.dispatched_by = u.user_id
            WHERE ds.dispatch_id = %s
        """, (dispatch_id,))
        return cursor.fetchone()
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 6.2 View Dispatch Information - Get all dispatch slips
@router.get("/", response_model=List[DispatchResponse])
async def get_all_dispatch_slips():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT ds.*, tr.transfer_number, tb.branch_name as to_branch, 
                   u.full_name as dispatched_by_name
            FROM dispatch_slips ds
            JOIN transfer_requests tr ON ds.transfer_id = tr.transfer_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON ds.dispatched_by = u.user_id
            ORDER BY ds.dispatch_date DESC
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

# Get dispatch details
@router.get("/{dispatch_id}", response_model=DispatchResponse)
async def get_dispatch_details(dispatch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT ds.*, tr.transfer_number, 
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as dispatched_by_name
            FROM dispatch_slips ds
            JOIN transfer_requests tr ON ds.transfer_id = tr.transfer_id
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON ds.dispatched_by = u.user_id
            WHERE ds.dispatch_id = %s
        """, (dispatch_id,))
        dispatch = cursor.fetchone()
        if not dispatch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispatch not found"
            )
        return dispatch
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get items in dispatch
@router.get("/{dispatch_id}/items", response_model=List[DispatchItemResponse])
async def get_dispatch_items(dispatch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT tri.item_id, i.item_name, i.item_code, 
                   tri.dispatched_quantity, i.unit_of_measure
            FROM transfer_request_items tri
            JOIN items i ON tri.item_id = i.item_id
            JOIN dispatch_slips ds ON tri.transfer_id = ds.transfer_id
            WHERE ds.dispatch_id = %s
        """, (dispatch_id,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/{dispatch_id}/update-stock")
async def update_stock_for_dispatch(dispatch_id: int, user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Get all items in the dispatch
        cursor.execute("""
            SELECT tri.item_id, tri.dispatched_quantity, tr.from_branch_id
            FROM transfer_request_items tri
            JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
            JOIN dispatch_slips ds ON tr.transfer_id = ds.transfer_id
            WHERE ds.dispatch_id = %s
        """, (dispatch_id,))
        items = cursor.fetchall()
        
        # Update stock for each item
        for item in items:
            cursor.callproc("update_stock", [
                item['item_id'],
                item['from_branch_id'],
                -item['dispatched_quantity'],  # Negative for OUT
                'TRANSFER_OUT',
                'TRANSFER',
                dispatch_id,
                user_id,
                'Dispatched to branch'
            ])
        
        connection.commit()
        return {"message": "Stock updated successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()