"""
TEO — Router: Autenticação
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import Token, ProfessionalCreate, ProfessionalResponse
from app.services.auth_service import (
    authenticate_professional, create_access_token,
    get_password_hash, get_current_user, require_role
)
from app.models.professional import Professional, ProfessionalRole

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login com email/senha. Retorna JWT token."""
    user = authenticate_professional(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return Token(access_token=token, token_type="bearer", role=user.role, nome=user.nome)


@router.post("/register", response_model=ProfessionalResponse)
def register_professional(
    data: ProfessionalCreate,
    db: Session = Depends(get_db),
    current_user: Professional = Depends(require_role(ProfessionalRole.ADMIN))
):
    """Cadastra novo profissional. Apenas ADMIN."""
    existing = db.query(Professional).filter(Professional.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    prof = Professional(
        nome=data.nome,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        especialidade=data.especialidade,
        registro_conselho=data.registro_conselho,
        telefone=data.telefone,
    )
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


@router.get("/me", response_model=ProfessionalResponse)
def get_me(current_user: Professional = Depends(get_current_user)):
    """Retorna dados do usuário autenticado."""
    return current_user
