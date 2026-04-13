from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, UserRole
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == str(body.email)).first():
        raise HTTPException(status_code=400, detail="البريد مستخدم")
    u = User(
        email=str(body.email),
        hashed_password=hash_password(body.password),
        full_name_ar=body.full_name_ar,
        role=UserRole(body.role.value),
        department_id=body.department_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.post("/token", response_model=Token)
def token(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="بيانات الدخول غير صحيحة")
    return Token(access_token=create_access_token(user.email))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
