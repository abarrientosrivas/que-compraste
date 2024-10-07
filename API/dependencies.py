from . import database
from .models import NodeToken
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_403_FORBIDDEN
from sqlalchemy.orm import Session
import hashlib

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def get_client_ip(request: Request):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    else:
        return request.client.host

async def get_node_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="No Token provided"
        )
    
    token = credentials.credentials
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    node_token = db.query(NodeToken).filter(NodeToken.key_hash == hashed_token).first()
    
    if not node_token:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid Token"
        )
    
    return node_token