"""
TEO — Auth Service
Gerencia autenticação JWT, hashing de senhas e autorização por role.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.professional import Professional, ProfessionalRole

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def authenticate_professional(db: Session, email: str, password: str) -> Optional[Professional]:
    """Valida credenciais e retorna o profissional ou None."""
    prof = db.query(Professional).filter(Professional.email == email, Professional.ativo == True).first()
    if not prof or not verify_password(password, prof.hashed_password):
        return None
    return prof


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Professional:
    """Dependency FastAPI: extrai e valida o usuário do JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Professional).filter(Professional.email == email).first()
    if user is None or not user.ativo:
        raise credentials_exception
    return user


def require_role(*roles: ProfessionalRole):
    """
    Factory de dependency para exigir roles específicos.
    Uso: Depends(require_role(ProfessionalRole.NEUROPEDIATRA))
    """
    def role_checker(current_user: Professional = Depends(get_current_user)):
        if current_user.role not in roles and current_user.role != ProfessionalRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfis permitidos: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker
