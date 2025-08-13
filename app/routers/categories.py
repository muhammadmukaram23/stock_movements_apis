from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.categories import CategorySummary,CategoryResponse,CategoryInDB,CategoryUpdate,CategoryCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# 1. Get all categories
@router.get("/", response_model=List[CategoryResponse])
async def get_all_categories():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        return categories
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 2. Create category
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "INSERT INTO categories (category_name, category_code, description) VALUES (%s, %s, %s)",
            (category.category_name, category.category_code, category.description)
        )
        connection.commit()
        
        category_id = cursor.lastrowid
        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
        new_category = cursor.fetchone()
        
        return new_category
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 3. Update category
@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category: CategoryUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "UPDATE categories SET category_name = %s, description = %s WHERE category_id = %s",
            (category.category_name, category.description, category_id)
        )
        connection.commit()
        
        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
        updated_category = cursor.fetchone()
        
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
            
        return updated_category
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()


# Get category by ID
@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_by_id(category_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
            
        return category
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()


# Delete category
@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
        connection.commit()
        
        return {"message": "Category deleted successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()