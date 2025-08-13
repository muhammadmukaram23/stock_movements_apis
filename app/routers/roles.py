from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.database import get_connection
from app.models.roles import RoleSummary,RoleResponse,RoleInDB,RoleUpdate,RoleCreate
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token
router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

@router.get("/", response_model=List[RoleResponse])
async def get_all_roles():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        return roles
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_by_id(role_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
        role = cursor.fetchone()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
            
        return role
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "INSERT INTO roles (role_name, role_description) VALUES (%s, %s)",
            (role.role_name, role.role_description)
        )
        connection.commit()
        
        role_id = cursor.lastrowid
        cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
        new_role = cursor.fetchone()
        
        return new_role
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: RoleUpdate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Check if role exists
        cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if role.role_name is not None:
            update_fields.append("role_name = %s")
            params.append(role.role_name)
            
        if role.role_description is not None:
            update_fields.append("role_description = %s")
            params.append(role.role_description)
            
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
            
        query = f"UPDATE roles SET {', '.join(update_fields)} WHERE role_id = %s"
        params.append(role_id)
        
        cursor.execute(query, tuple(params))
        connection.commit()
        
        # Return updated role
        cursor.execute("SELECT * FROM roles WHERE role_id = %s", (role_id,))
        updated_role = cursor.fetchone()
        
        return updated_role
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(role_id: int):
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        # Check if role exists
        cursor.execute("SELECT 1 FROM roles WHERE role_id = %s", (role_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
            
        cursor.execute("DELETE FROM roles WHERE role_id = %s", (role_id,))
        connection.commit()
        
        return {"message": "Role deleted successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()