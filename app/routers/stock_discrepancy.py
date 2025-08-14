from fastapi import APIRouter, HTTPException, status, Depends, Header,Query,Body
from typing import Optional
from app.database import get_connection
from app.models.stock_discrepancy import StockDiscrepancyResponse,StockDiscrepancyResolution,StockDiscrepancyUpdate,StockDiscrepancyCreate,StockDiscrepancyBase,DiscrepancyType,DiscrepancyStatus
from datetime import datetime,date
from typing import List
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import Error 
from app.auth.auth import verify_token

router = APIRouter(prefix="/stock_discrepancy", tags=["stock_discrepancy"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

# 1. Report stock discrepancy
@router.post("/", response_model=StockDiscrepancyResponse, status_code=status.HTTP_201_CREATED)
async def report_discrepancy(discrepancy: StockDiscrepancyCreate):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Calculate difference
        difference = discrepancy.actual_stock - discrepancy.expected_stock
        
        cursor.execute("""
            INSERT INTO stock_discrepancies 
            (branch_id, item_id, expected_stock, actual_stock, difference, 
             discrepancy_type, reported_by, investigation_notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'REPORTED')
        """, (
            discrepancy.branch_id,
            discrepancy.item_id,
            discrepancy.expected_stock,
            discrepancy.actual_stock,
            difference,
            discrepancy.discrepancy_type.value,
            discrepancy.reported_by,
            discrepancy.investigation_notes
        ))
        
        discrepancy_id = cursor.lastrowid
        connection.commit()
        
        cursor.execute("""
            SELECT 
                sd.*, 
                i.item_name, i.item_code,
                b.branch_name,
                u.full_name as reported_by_name,
                COALESCE(sd.discrepancy_type, 'OTHER') as discrepancy_type
            FROM stock_discrepancies sd
            JOIN items i ON sd.item_id = i.item_id
            JOIN branches b ON sd.branch_id = b.branch_id
            JOIN users u ON sd.reported_by = u.user_id
            WHERE sd.discrepancy_id = %s
        """, (discrepancy_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discrepancy not found after creation"
            )
            
        return StockDiscrepancyResponse(**result)
        
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/", response_model=List[StockDiscrepancyResponse])
async def get_all_discrepancies():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                sd.*,
                i.item_name, i.item_code,
                b.branch_name,
                u.full_name as reported_by_name,
                COALESCE(sd.discrepancy_type, 'OTHER') as discrepancy_type
            FROM stock_discrepancies sd
            JOIN items i ON sd.item_id = i.item_id
            JOIN branches b ON sd.branch_id = b.branch_id
            JOIN users u ON sd.reported_by = u.user_id
            ORDER BY sd.reported_date DESC
        """)
        
        results = cursor.fetchall()
        return [StockDiscrepancyResponse(**row) for row in results]
        
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.get("/pending", response_model=List[StockDiscrepancyResponse])
async def get_pending_discrepancies():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                sd.*,
                i.item_name, i.item_code,
                b.branch_name,
                u.full_name as reported_by_name,
                COALESCE(sd.discrepancy_type, 'OTHER') as discrepancy_type
            FROM stock_discrepancies sd
            JOIN items i ON sd.item_id = i.item_id
            JOIN branches b ON sd.branch_id = b.branch_id
            JOIN users u ON sd.reported_by = u.user_id
            WHERE sd.status = 'REPORTED'
            ORDER BY ABS(sd.difference) DESC
        """)
        
        results = cursor.fetchall()
        return [StockDiscrepancyResponse(**row) for row in results]
        
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.patch("/{discrepancy_id}/investigate", response_model=StockDiscrepancyResponse)
async def update_investigation(
    discrepancy_id: int,
    update_data: StockDiscrepancyUpdate
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE stock_discrepancies 
            SET 
                status = COALESCE(%s, status),
                investigation_notes = COALESCE(%s, investigation_notes)
            WHERE discrepancy_id = %s
        """, (
            update_data.status.value if update_data.status else None,
            update_data.investigation_notes,
            discrepancy_id
        ))
        
        connection.commit()
        
        cursor.execute("""
            SELECT 
                sd.*,
                i.item_name, i.item_code,
                b.branch_name,
                u.full_name as reported_by_name,
                COALESCE(sd.discrepancy_type, 'OTHER') as discrepancy_type
            FROM stock_discrepancies sd
            JOIN items i ON sd.item_id = i.item_id
            JOIN branches b ON sd.branch_id = b.branch_id
            JOIN users u ON sd.reported_by = u.user_id
            WHERE sd.discrepancy_id = %s
        """, (discrepancy_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discrepancy not found"
            )
            
        return StockDiscrepancyResponse(**result)
        
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()

@router.patch("/{discrepancy_id}/resolve", response_model=StockDiscrepancyResponse)
async def resolve_discrepancy(
    discrepancy_id: int,
    resolution: StockDiscrepancyResolution
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            UPDATE stock_discrepancies 
            SET 
                status = 'RESOLVED',
                resolution_notes = %s,
                resolved_date = NOW()
            WHERE discrepancy_id = %s
        """, (
            resolution.resolution_notes,
            discrepancy_id
        ))
        
        connection.commit()
        
        cursor.execute("""
            SELECT 
                sd.*,
                i.item_name, i.item_code,
                b.branch_name,
                u.full_name as reported_by_name,
                COALESCE(sd.discrepancy_type, 'OTHER') as discrepancy_type
            FROM stock_discrepancies sd
            JOIN items i ON sd.item_id = i.item_id
            JOIN branches b ON sd.branch_id = b.branch_id
            JOIN users u ON sd.reported_by = u.user_id
            WHERE sd.discrepancy_id = %s
        """, (discrepancy_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discrepancy not found"
            )
            
        return StockDiscrepancyResponse(**result)
        
    except Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()