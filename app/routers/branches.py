from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.branches import BranchSummary,BranchResponse,BranchInDB,BranchUpdate,BranchCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/branches", tags=["branches"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# 1. Get all active branches
@router.get("/", response_model=List[BranchResponse])
async def get_all_branches():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM branches 
            WHERE is_active = TRUE 
            ORDER BY branch_name
        """)
        branches = cursor.fetchall()
        return branches
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 2. Get branch by ID
@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch_by_id(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM branches WHERE branch_id = %s", (branch_id,))
        branch = cursor.fetchone()
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
            
        return branch
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 3. Create new branch
@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(branch: BranchCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO branches 
            (branch_name, branch_code, city, address, phone, email, branch_manager_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            branch.branch_name,
            branch.branch_code,
            branch.city,
            branch.address,
            branch.phone,
            branch.email,
            branch.branch_manager_name
        ))
        connection.commit()
        
        branch_id = cursor.lastrowid
        cursor.execute("SELECT * FROM branches WHERE branch_id = %s", (branch_id,))
        new_branch = cursor.fetchone()
        
        return new_branch
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 4. Update branch
@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(branch_id: int, branch: BranchUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE branches 
            SET branch_name = %s, branch_code = %s, city = %s, 
                address = %s, phone = %s, email = %s, branch_manager_name = %s
            WHERE branch_id = %s
        """, (
            branch.branch_name,
            branch.branch_code,
            branch.city,
            branch.address,
            branch.phone,
            branch.email,
            branch.branch_manager_name,
            branch_id
        ))
        connection.commit()
        
        cursor.execute("SELECT * FROM branches WHERE branch_id = %s", (branch_id,))
        updated_branch = cursor.fetchone()
        
        return updated_branch
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 5. Deactivate branch
@router.delete("/{branch_id}", status_code=status.HTTP_200_OK)
async def deactivate_branch(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE branches 
            SET is_active = FALSE 
            WHERE branch_id = %s
        """, (branch_id,))
        connection.commit()
        
        return {"message": "Branch deactivated successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# 6. Get branches for dropdown
@router.get("/dropdown/{exclude_branch_id}", response_model=List[BranchSummary])
async def get_branches_for_dropdown(exclude_branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT branch_id, branch_name, branch_code
            FROM branches 
            WHERE is_active = TRUE AND branch_id != %s
            ORDER BY branch_name
        """, (exclude_branch_id,))
        branches = cursor.fetchall()
        return branches
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()