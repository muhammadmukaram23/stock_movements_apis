from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.inventory import StockStatus, InventoryCreate, InventoryUpdate, BranchStockResponse, ItemStockAcrossBranches,ItemStockResponse,OutOfStockItem,LowStockItem,StockAdjustment,StockReservation
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# Get current stock for all items in a branch
@router.get("/branch/{branch_id}", response_model=List[BranchStockResponse])
async def get_branch_stock(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_id, i.item_name, i.item_code, c.category_name,
                   COALESCE(inv.current_stock, 0) as current_stock,
                   COALESCE(inv.reserved_stock, 0) as reserved_stock,
                   COALESCE(inv.available_stock, 0) as available_stock,
                   i.minimum_stock_level,
                   CASE 
                       WHEN COALESCE(inv.available_stock, 0) = 0 THEN 'OUT_OF_STOCK'
                       WHEN COALESCE(inv.available_stock, 0) <= i.minimum_stock_level THEN 'LOW_STOCK'
                       ELSE 'NORMAL'
                   END as stock_status,
                   inv.last_updated
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = %s
            WHERE i.is_active = TRUE
            ORDER BY i.item_name
        """, (branch_id,))
        
        # Convert NULL datetimes to None
        items = []
        for row in cursor.fetchall():
            if row['last_updated'] is None:
                row['last_updated'] = None
            items.append(row)
            
        return items
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Check specific item stock in specific branch
@router.get("/item/{item_id}/branch/{branch_id}", response_model=ItemStockResponse)
async def get_item_stock(item_id: int, branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, i.item_code, b.branch_name,
                   COALESCE(inv.current_stock, 0) as current_stock,
                   COALESCE(inv.reserved_stock, 0) as reserved_stock,
                   COALESCE(inv.available_stock, 0) as available_stock
            FROM items i
            CROSS JOIN branches b
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND b.branch_id = inv.branch_id
            WHERE i.item_id = %s AND b.branch_id = %s
        """, (item_id, branch_id))
        stock = cursor.fetchone()
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock record not found"
            )
        return stock
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get stock across all branches for an item
@router.get("/item/{item_id}/branches", response_model=List[ItemStockAcrossBranches])
async def get_item_stock_across_branches(item_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, i.item_code, b.branch_name, b.branch_code,
                   COALESCE(inv.current_stock, 0) as current_stock,
                   COALESCE(inv.available_stock, 0) as available_stock
            FROM items i
            CROSS JOIN branches b
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND b.branch_id = inv.branch_id
            WHERE i.item_id = %s AND b.is_active = TRUE
            ORDER BY b.branch_name
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

# Get low stock items for a branch
@router.get("/branch/{branch_id}/low-stock", response_model=List[LowStockItem])
async def get_low_stock_items(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, i.item_code, inv.available_stock, i.minimum_stock_level,
                   (i.minimum_stock_level - inv.available_stock) as shortage
            FROM inventory inv
            JOIN items i ON inv.item_id = i.item_id
            WHERE inv.branch_id = %s 
              AND inv.available_stock <= i.minimum_stock_level
              AND i.is_active = TRUE
            ORDER BY shortage DESC
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

# Get out of stock items for a branch
@router.get("/branch/{branch_id}/out-of-stock", response_model=List[OutOfStockItem])
async def get_out_of_stock_items(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_name, i.item_code, i.minimum_stock_level
            FROM items i
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = %s
            WHERE (inv.available_stock IS NULL OR inv.available_stock = 0)
              AND i.is_active = TRUE
            ORDER BY i.item_name
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

# Stock Updates
@router.post("/adjust", status_code=status.HTTP_200_OK)
async def adjust_stock(adjustment: StockAdjustment):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.callproc("update_stock", [
            adjustment.item_id,
            adjustment.branch_id,
            adjustment.quantity,
            adjustment.adjustment_type,
            adjustment.reference_type,
            adjustment.reference_id,
            adjustment.updated_by,
            adjustment.notes
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

# Reserve stock
@router.post("/reserve", status_code=status.HTTP_200_OK)
async def reserve_stock(reservation: StockReservation):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE inventory 
            SET reserved_stock = reserved_stock + %s
            WHERE item_id = %s AND branch_id = %s
        """, (reservation.quantity, reservation.item_id, reservation.branch_id))
        connection.commit()
        return {"message": "Stock reserved successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Release reserved stock
@router.post("/release", status_code=status.HTTP_200_OK)
async def release_stock(reservation: StockReservation):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE inventory 
            SET reserved_stock = GREATEST(0, reserved_stock - %s)
            WHERE item_id = %s AND branch_id = %s
        """, (reservation.quantity, reservation.item_id, reservation.branch_id))
        connection.commit()
        return {"message": "Stock reservation released successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()