from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()
# HARDCODED_TOKEN = "h9F!8xZ$1a@P0rT#Q3vN^y7Ljz2W*mR6uE4bKsDcGx1ZwVp8H"
HARDCODED_TOKEN = "1"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if credentials.credentials != HARDCODED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
   