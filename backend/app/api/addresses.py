from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user.users import User
from app.models.user.user_address import UserAddress

router = APIRouter(prefix="/addresses", tags=["Addresses"])

class AddressCreate(BaseModel):
    address_type: str = "home"
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    postal_code: str
    is_default: bool = False

class AddressResponse(BaseModel):
    id: uuid.UUID
    address_type: str
    line1: str
    line2: Optional[str]
    city: str
    state: str
    country: str
    postal_code: str
    is_default: bool

    class Config:
        from_attributes = True

@router.get("", response_model=list[AddressResponse])
def list_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserAddress).filter(UserAddress.user_id == current_user.id).all()

@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(req: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.is_default:
        db.query(UserAddress).filter(UserAddress.user_id == current_user.id).update({"is_default": False})
    addr = UserAddress(
        id=uuid.uuid4(),
        user_id=current_user.id,
        address_type=req.address_type,
        line1=req.line1,
        line2=req.line2,
        city=req.city,
        state=req.state,
        country=req.country,
        postal_code=req.postal_code,
        is_default=req.is_default,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr

@router.put("/{addr_id}", response_model=AddressResponse)
def update_address(addr_id: str, req: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addr = db.query(UserAddress).filter(UserAddress.id == addr_id, UserAddress.user_id == current_user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    if req.is_default:
        db.query(UserAddress).filter(UserAddress.user_id == current_user.id).update({"is_default": False})
    for k, v in req.model_dump().items():
        setattr(addr, k, v)
    db.commit()
    db.refresh(addr)
    return addr

@router.delete("/{addr_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(addr_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addr = db.query(UserAddress).filter(UserAddress.id == addr_id, UserAddress.user_id == current_user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return None

@router.post("/{addr_id}/default", response_model=AddressResponse)
def set_default(addr_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addr = db.query(UserAddress).filter(UserAddress.id == addr_id, UserAddress.user_id == current_user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.query(UserAddress).filter(UserAddress.user_id == current_user.id).update({"is_default": False})
    addr.is_default = True
    db.commit()
    db.refresh(addr)
    return addr
