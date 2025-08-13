from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.stock_movement import MovementFilter,StockMovementResponse,StockMovementCreate,ReferenceType,MovementType
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/stock_movement", tags=["stock_movement"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


 # Create new stock movement
@router.post("/", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(movement: StockMovementCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO stock_movements 
            (item_id, branch_id, movement_type, quantity, previous_stock, 
             new_stock, reference_type, reference_id, notes, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            movement.item_id, movement.branch_id, movement.movement_type.value,
            movement.quantity, movement.previous_stock, movement.new_stock,
            movement.reference_type.value, movement.reference_id,
            movement.notes, movement.created_by
        ))
        connection.commit()
        
        movement_id = cursor.lastrowid
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.movement_id = %s
        """, (movement_id,))
        new_movement = cursor.fetchone()
        
        return new_movement
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get stock movement by ID
@router.get("/{movement_id}", response_model=StockMovementResponse)
async def get_stock_movement(movement_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.movement_id = %s
        """, (movement_id,))
        movement = cursor.fetchone()
        
        if not movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock movement not found"
            )
            
        return movement
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get filtered stock movements
@router.get("/", response_model=List[StockMovementResponse])
async def get_stock_movements(
    item_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    reference_type: Optional[ReferenceType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
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
            WHERE 1=1
        """
        params = []
        
        if item_id:
            query += " AND sm.item_id = %s"
            params.append(item_id)
        if branch_id:
            query += " AND sm.branch_id = %s"
            params.append(branch_id)
        if movement_type:
            query += " AND sm.movement_type = %s"
            params.append(movement_type.value)
        if reference_type:
            query += " AND sm.reference_type = %s"
            params.append(reference_type.value)
        if start_date:
            query += " AND sm.created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND sm.created_at <= %s"
            params.append(end_date)
            
        query += " ORDER BY sm.created_at DESC"
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get stock movements for an item
@router.get("/item/{item_id}", response_model=List[StockMovementResponse])
async def get_item_movements(item_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.item_id = %s
            ORDER BY sm.created_at DESC
        """, (item_id,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get stock movements for a branch
@router.get("/branch/{branch_id}", response_model=List[StockMovementResponse])
async def get_branch_movements(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.branch_id = %s
            ORDER BY sm.created_at DESC
        """, (branch_id,))
        
        # Clean the data before returning
        movements = []
        for row in cursor.fetchall():
            # Handle empty reference_type
            if row['reference_type'] == '':
                row['reference_type'] = None
            movements.append(row)
            
        return movements
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get stock movements by date range
@router.get("/date-range", response_model=List[StockMovementResponse])
async def get_stock_movements_by_date_range(
    start_date: datetime,
    end_date: datetime
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.created_at BETWEEN %s AND %s
            ORDER BY sm.created_at DESC
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

# Get stock movements by type
@router.get("/type/{movement_type}", response_model=List[StockMovementResponse])
async def get_stock_movements_by_type(movement_type: MovementType):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.item_id
            JOIN branches b ON sm.branch_id = b.branch_id
            JOIN users u ON sm.created_by = u.user_id
            WHERE sm.movement_type = %s
            ORDER BY sm.created_at DESC
        """, (movement_type.value,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()