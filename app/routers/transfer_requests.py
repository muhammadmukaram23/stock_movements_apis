from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.transfer_requests import TransferRequestSummary,TransferRequestItemResponse,TransferRequestResponse,TransferRequestUpdate,TransferRequestItem,TransferRequestCreate,TransferPriority,TransferStatus
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/transfer_requests", tags=["transfer_rquests"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# Create transfer request
@router.post("/", response_model=TransferRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer_request(
    request: TransferRequestCreate,
    items: List[TransferRequestItem]
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Create transfer request header
        cursor.execute("""
            INSERT INTO transfer_requests 
            (transfer_number, from_branch_id, to_branch_id, 
             requested_by, priority, notes)
            VALUES (generate_transfer_number(), %s, %s, %s, %s, %s)
        """, (
            request.from_branch_id, request.to_branch_id,
            request.requested_by, request.priority.value, request.notes
        ))
        transfer_id = cursor.lastrowid
        
        # Add transfer request items
        for item in items:
            cursor.execute("""
                INSERT INTO transfer_request_items 
                (transfer_id, item_id, requested_quantity, notes)
                VALUES (%s, %s, %s, %s)
            """, (transfer_id, item.item_id, item.requested_quantity, item.notes))
        
        connection.commit()
        
        # Get the created transfer request with details
        cursor.execute("""
            SELECT tr.*, fb.branch_name as from_branch_name, 
                   tb.branch_name as to_branch_name,
                   u.full_name as requested_by_name
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON tr.requested_by = u.user_id
            WHERE tr.transfer_id = %s
        """, (transfer_id,))
        transfer_request = cursor.fetchone()
        
        return transfer_request
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get all transfer requests
@router.get("/", response_model=List[TransferRequestSummary])
async def get_all_transfer_requests(limit: int = 10, offset: int = 0):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT tr.transfer_id, tr.transfer_number, 
                   fb.branch_name as from_branch, tb.branch_name as to_branch,
                   u.full_name as requested_by, tr.status, tr.priority,
                   tr.request_date, tr.approval_date,
                   COUNT(tri.request_item_id) as total_items
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u ON tr.requested_by = u.user_id
            LEFT JOIN transfer_request_items tri ON tr.transfer_id = tri.transfer_id
            GROUP BY tr.transfer_id
            ORDER BY tr.request_date DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get pending transfer requests for approval
@router.get("/pending/{branch_id}", response_model=List[TransferRequestSummary])
async def get_pending_transfer_requests(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
    SELECT tr.transfer_id, tr.transfer_number, 
           fb.branch_name as from_branch,
           tb.branch_name as to_branch, 
           u.full_name as requested_by,
           tr.status, tr.priority, tr.request_date, tr.notes,
           COUNT(tri.request_item_id) as total_items
    FROM transfer_requests tr
    JOIN branches fb ON tr.from_branch_id = fb.branch_id
    JOIN branches tb ON tr.to_branch_id = tb.branch_id
    JOIN users u ON tr.requested_by = u.user_id
    LEFT JOIN transfer_request_items tri ON tr.transfer_id = tri.transfer_id
    WHERE tr.from_branch_id = %s AND tr.status = 'PENDING'
    GROUP BY tr.transfer_id
    ORDER BY 
        CASE tr.priority
            WHEN 'URGENT' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
        END,
        tr.request_date
""", (branch_id,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get transfer request details
@router.get("/{transfer_id}", response_model=TransferRequestResponse)
async def get_transfer_request(transfer_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT tr.*, fb.branch_name as from_branch_name, 
                   tb.branch_name as to_branch_name,
                   u1.full_name as requested_by_name, 
                   u2.full_name as approved_by_name
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u1 ON tr.requested_by = u1.user_id
            LEFT JOIN users u2 ON tr.approved_by = u2.user_id
            WHERE tr.transfer_id = %s
        """, (transfer_id,))
        transfer_request = cursor.fetchone()
        
        if not transfer_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer request not found"
            )
            
        return transfer_request
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get transfer request items
@router.get("/{transfer_id}/items", response_model=List[TransferRequestItemResponse])
async def get_transfer_request_items(transfer_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT tri.*, i.item_name, i.item_code, i.unit_of_measure,
                   COALESCE(inv.available_stock, 0) as available_stock
            FROM transfer_request_items tri
            JOIN items i ON tri.item_id = i.item_id
            LEFT JOIN inventory inv ON i.item_id = inv.item_id 
                AND inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = %s)
            WHERE tri.transfer_id = %s
        """, (transfer_id, transfer_id))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Approve transfer request
@router.post("/{transfer_id}/approve", response_model=TransferRequestResponse)
async def approve_transfer_request(
    transfer_id: int, 
    approved_by: int,
    items: List[TransferRequestItem]  # List of approved quantities
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Update transfer request status
        cursor.execute("""
            UPDATE transfer_requests 
            SET status = 'APPROVED', approved_by = %s, approval_date = NOW()
            WHERE transfer_id = %s AND status = 'PENDING'
        """, (approved_by, transfer_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer request not found or not pending approval"
            )
        
        # Update approved quantities for items
        for item in items:
            cursor.execute("""
                UPDATE transfer_request_items 
                SET approved_quantity = %s
                WHERE transfer_id = %s AND item_id = %s
            """, (item.requested_quantity, transfer_id, item.item_id))
        
        connection.commit()
        
        # Return updated transfer request
        cursor.execute("""
            SELECT tr.*, fb.branch_name as from_branch_name, 
                   tb.branch_name as to_branch_name,
                   u1.full_name as requested_by_name, 
                   u2.full_name as approved_by_name
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u1 ON tr.requested_by = u1.user_id
            LEFT JOIN users u2 ON tr.approved_by = u2.user_id
            WHERE tr.transfer_id = %s
        """, (transfer_id,))
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

# Reject transfer request
@router.post("/{transfer_id}/reject", response_model=TransferRequestResponse)
async def reject_transfer_request(
    transfer_id: int, 
    approved_by: int,
    rejection_reason: str
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE transfer_requests 
            SET status = 'REJECTED', approved_by = %s, 
                approval_date = NOW(), rejection_reason = %s
            WHERE transfer_id = %s AND status = 'PENDING'
        """, (approved_by, rejection_reason, transfer_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer request not found or not pending approval"
            )
        
        connection.commit()
        
        # Return updated transfer request
        cursor.execute("""
            SELECT tr.*, fb.branch_name as from_branch_name, 
                   tb.branch_name as to_branch_name,
                   u1.full_name as requested_by_name, 
                   u2.full_name as approved_by_name
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u1 ON tr.requested_by = u1.user_id
            LEFT JOIN users u2 ON tr.approved_by = u2.user_id
            WHERE tr.transfer_id = %s
        """, (transfer_id,))
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

# Cancel transfer request
@router.post("/{transfer_id}/cancel", response_model=TransferRequestResponse)
async def cancel_transfer_request(transfer_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE transfer_requests 
            SET status = 'CANCELLED'
            WHERE transfer_id = %s AND status IN ('PENDING', 'APPROVED')
        """, (transfer_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer request not found or cannot be cancelled"
            )
        
        connection.commit()
        
        # Return updated transfer request
        cursor.execute("""
            SELECT tr.*, fb.branch_name as from_branch_name, 
                   tb.branch_name as to_branch_name,
                   u1.full_name as requested_by_name, 
                   u2.full_name as approved_by_name
            FROM transfer_requests tr
            JOIN branches fb ON tr.from_branch_id = fb.branch_id
            JOIN branches tb ON tr.to_branch_id = tb.branch_id
            JOIN users u1 ON tr.requested_by = u1.user_id
            LEFT JOIN users u2 ON tr.approved_by = u2.user_id
            WHERE tr.transfer_id = %s
        """, (transfer_id,))
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