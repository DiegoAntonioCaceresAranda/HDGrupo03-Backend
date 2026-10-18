import os 
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import JWTError, jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from Modelos.Usuarios.Models.usuario import Usuario

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    try:
        return password_hash.verify(
            password,
            hashed_password,
        )
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    if not SECRET_KEY:
        raise RuntimeError(
            "Falta configurar JWT_SECRET_KEY en .env"
        )

    payload = data.copy()

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=EXPIRE_MINUTES
    )

    payload["exp"] = expiration

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not SECRET_KEY:
        raise RuntimeError(
            "Falta configurar JWT_SECRET_KEY en .env"
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    usuario = (
        db.query(Usuario)
        .filter(Usuario.id_usuario == user_id)
        .first()
    )

    if not usuario:
        raise credentials_exception

    if (usuario.estado or "").strip().lower() != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está inactiva",
        )

    return usuario