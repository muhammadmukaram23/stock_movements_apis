from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.receiving_slips import ReceivedItemResponse,ReceivingSlipResponse,ReceivingSlipItem,ReceivingSlipCreate,ConditionOnArrival
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/receiving_slips", tags=["receiving_slips"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# 7.1 Create Receiving Slip
@router.post("/", response_model=ReceivingSlipResponse, status_code=status.HTTP_201_CREATED)
async def create_receiving_slip(
    receiving: ReceivingSlipCreate,
    items: List[ReceivingSlipItem],
    user_id: int
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # First get the count for receiving number generation
        cursor.execute("""
            SELECT COUNT(*) + 1 as next_num 
            FROM receiving_slips 
            WHERE DATE(receiving_date) = CURDATE()
        """)
        count_result = cursor.fetchone()
        next_num = str(count_result['next_num']).zfill(4)
        
        # Generate receiving number
        receiving_number = f"RS-{datetime.now().strftime('%Y%m%d')}-{next_num}"
        
        # Create receiving slip
        cursor.execute("""
            INSERT INTO receiving_slips 
            (receiving_number, transfer_id, dispatch_id, received_by, 
             condition_on_arrival, notes, photo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            receiving_number, receiving.transfer_id, receiving.dispatch_id,
            receiving.received_by, receiving.condition_on_arrival.value,
            receiving.notes, receiving.photo_path
        ))
        receiving_id = cursor.lastrowid

        # Add received items
        for item in items:
            cursor.execute("""
                INSERT INTO receiving_slip_items 
                (receiving_id, item_id, dispatched_quantity, 
                 received_quantity, damaged_quantity, condition_notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                receiving_id, item.item_id, item.dispatched_quantity,
                item.received_quantity, item.damaged_quantity, item.condition_notes
            ))
            
            # Update received quantities in transfer request
            cursor.execute("""
                UPDATE transfer_request_items 
                SET received_quantity = %s
                WHERE transfer_id = %s AND item_id = %s
            """, (item.received_quantity, receiving.transfer_id, item.item_id))
            
            # Add stock to receiving branch
            cursor.callproc("update_stock", [
                item.item_id,
                receiving.transfer_id,  # Will need to get to_branch_id
                item.received_quantity,
                'TRANSFER_IN',
                'TRANSFER',
                receiving.transfer_id,
                user_id,
                'Received from branch'
            ])

        # Update transfer status
        cursor.execute("""
            UPDATE transfer_requests 
            SET status = 'DELIVERED', delivery_date = NOW()
            WHERE transfer_id = %s
        """, (receiving.transfer_id,))

        # Release reserved stock from sending branch
        cursor.execute("""
            UPDATE inventory inv
            JOIN transfer_request_items tri ON inv.item_id = tri.item_id
            SET inv.reserved_stock = GREATEST(0, inv.reserved_stock - tri.received_quantity)
            WHERE inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = %s)
              AND tri.transfer_id = %s
        """, (receiving.transfer_id, receiving.transfer_id))

        connection.commit()

        # Return created receiving slip with details
        cursor.execute("""
            SELECT rs.*, tr.transfer_number, ds.dispatch_number,
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as received_by_name
            FROM receiving_slips rs
            JOIN transfer_requests tr ON rs.transfer_id = tr.transfer_id
            JOIN dispatch_slips ds ON rs.dispatch_id = ds.dispatch_id
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON rs.received_by = u.user_id
            WHERE rs.receiving_id = %s
        """, (receiving_id,))
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

# 7.2 View Receiving Information - Get all receiving slips
@router.get("/", response_model=List[ReceivingSlipResponse])
async def get_all_receiving_slips():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT rs.*, tr.transfer_number, fb.branch_name as from_branch, 
                   u.full_name as received_by_name
            FROM receiving_slips rs
            JOIN transfer_requests tr ON rs.transfer_id = tr.transfer_id
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN users u ON rs.received_by = u.user_id
            ORDER BY rs.receiving_date DESC
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

# Get receiving details
@router.get("/{receiving_id}", response_model=ReceivingSlipResponse)
async def get_receiving_details(receiving_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT rs.*, tr.transfer_number, ds.dispatch_number,
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as received_by_name
            FROM receiving_slips rs
            JOIN transfer_requests tr ON rs.transfer_id = tr.transfer_id
            JOIN dispatch_slips ds ON rs.dispatch_id = ds.dispatch_id
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON rs.received_by = u.user_id
            WHERE rs.receiving_id = %s
        """, (receiving_id,))
        receiving_slip = cursor.fetchone()
        if not receiving_slip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiving slip not found"
            )
        return receiving_slip
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get received items details
@router.get("/{receiving_id}/items", response_model=List[ReceivedItemResponse])
async def get_received_items(receiving_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT rsi.*, i.item_name, i.item_code, i.unit_of_measure
            FROM receiving_slip_items rsi
            JOIN items i ON rsi.item_id = i.item_id
            WHERE rsi.receiving_id = %s
        """, (receiving_id,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()