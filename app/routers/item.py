from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.item import ItemCategoryResponse,ItemDetailResponse, ItemSummary,ItemResponse,ItemUpdate,ItemCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/item", tags=["item"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# Get all items with category info
@router.get("/", response_model=List[ItemResponse])
async def get_all_items():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_id, i.item_name, i.item_code, i.category_id, c.category_name, 
                   i.description, i.unit_of_measure, i.minimum_stock_level,
                   i.maximum_stock_level, i.unit_price, i.is_active,
                   i.created_at, i.updated_at
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            ORDER BY i.item_name
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

# Get active items only
@router.get("/active", response_model=List[ItemSummary])
async def get_active_items():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_id, i.item_name, i.item_code, c.category_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            WHERE i.is_active = TRUE
            ORDER BY i.item_name
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

# Get item by ID
@router.get("/{item_id}", response_model=ItemDetailResponse)
async def get_item(item_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.*, c.category_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            WHERE i.item_id = %s
        """, (item_id,))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return item
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Search items
@router.get("/search/{query}", response_model=List[ItemSummary])
async def search_items(query: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT i.item_id, i.item_name, i.item_code, c.category_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            WHERE i.is_active = TRUE 
              AND (i.item_name LIKE CONCAT('%', %s, '%') 
                   OR i.item_code LIKE CONCAT('%', %s, '%'))
            ORDER BY i.item_name
        """, (query, query))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Create new item
@router.post("/", response_model=ItemDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO items 
            (item_name, item_code, category_id, description, 
             unit_of_measure, minimum_stock_level, maximum_stock_level, unit_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            item.item_name, item.item_code, item.category_id, item.description,
            item.unit_of_measure, item.minimum_stock_level, 
            item.maximum_stock_level, item.unit_price
        ))
        connection.commit()
        
        item_id = cursor.lastrowid
        cursor.execute("""
            SELECT i.*, c.category_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            WHERE i.item_id = %s
        """, (item_id,))
        new_item = cursor.fetchone()
        
        return new_item
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Update item
@router.put("/{item_id}", response_model=ItemDetailResponse)
async def update_item(item_id: int, item: ItemUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE items 
            SET item_name = %s, item_code = %s, category_id = %s, description = %s,
                unit_of_measure = %s, minimum_stock_level = %s, 
                maximum_stock_level = %s, unit_price = %s
            WHERE item_id = %s
        """, (
            item.item_name, item.item_code, item.category_id, item.description,
            item.unit_of_measure, item.minimum_stock_level,
            item.maximum_stock_level, item.unit_price, item_id
        ))
        connection.commit()
        
        cursor.execute("""
            SELECT i.*, c.category_name
            FROM items i
            JOIN categories c ON i.category_id = c.category_id
            WHERE i.item_id = %s
        """, (item_id,))
        updated_item = cursor.fetchone()
        
        return updated_item
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Deactivate item
@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def deactivate_item(item_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE items 
            SET is_active = FALSE 
            WHERE item_id = %s
        """, (item_id,))
        connection.commit()
        return {"message": "Item deactivated successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# Get items by category
@router.get("/category/{category_id}", response_model=List[ItemCategoryResponse])
async def get_items_by_category(category_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT item_id, item_name, item_code, unit_of_measure
            FROM items 
            WHERE category_id = %s AND is_active = TRUE
            ORDER BY item_name
        """, (category_id,))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()