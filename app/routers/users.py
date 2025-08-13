from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.users import  UserPermissions,UserSummary,UserDetailResponse,UserResponse,UserLoginResponse,PasswordChange, UserUpdate,UserCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# Authentication
@router.post("/login", response_model=UserLoginResponse)
async def login_user(username: str, password_hash: str):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, u.full_name, u.phone, 
                   u.branch_id, b.branch_name, b.branch_code, u.role_id, r.role_name,
                   u.is_active, u.last_login
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.username = %s AND u.password_hash = %s AND u.is_active = TRUE
        """, (username, password_hash))
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or inactive account"
            )
        
        # Update last login
        cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user['user_id'],))
        connection.commit()
        
        return user
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

# CRUD Operations
@router.post("/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO users 
            (username, email, password_hash, full_name, phone, branch_id, role_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user.username, user.email, user.password_hash, user.full_name,
            user.phone, user.branch_id, user.role_id
        ))
        connection.commit()
        
        user_id = cursor.lastrowid
        cursor.execute("""
            SELECT u.*, b.branch_name, r.role_name
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (user_id,))
        new_user = cursor.fetchone()
        
        return new_user
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/", response_model=List[UserResponse])
async def get_all_users():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, u.full_name, u.phone,
                   b.branch_name, r.role_name, u.is_active, u.created_at
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.full_name
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

@router.get("/branch/{branch_id}", response_model=List[UserSummary])
async def get_users_by_branch(branch_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.full_name, r.role_name, u.is_active
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.branch_id = %s
            ORDER BY r.role_name, u.full_name
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

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT u.*, b.branch_name, r.role_name
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(user_id: int, user: UserUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE users 
            SET username = %s, email = %s, full_name = %s, phone = %s, 
                branch_id = %s, role_id = %s, is_active = %s
            WHERE user_id = %s
        """, (
            user.username, user.email, user.full_name, user.phone,
            user.branch_id, user.role_id, user.is_active, user_id
        ))
        connection.commit()
        
        cursor.execute("""
            SELECT u.*, b.branch_name, r.role_name
            FROM users u
            JOIN branches b ON u.branch_id = b.branch_id
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (user_id,))
        updated_user = cursor.fetchone()
        
        return updated_user
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.patch("/{user_id}/password", status_code=status.HTTP_200_OK)
async def change_password(user_id: int, password: PasswordChange):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE user_id = %s
        """, (password.new_password_hash, user_id))
        connection.commit()
        return {"message": "Password updated successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user(user_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET is_active = FALSE 
            WHERE user_id = %s
        """, (user_id,))
        connection.commit()
        return {"message": "User deactivated successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/{user_id}/permissions", response_model=UserPermissions)
async def get_user_permissions(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT r.role_name, r.role_description
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (user_id,))
        permissions = cursor.fetchone()
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return permissions
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()