from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from Modelos.Usuarios.Models.usuario import Usuario
from Modelos.Autenticacion.Schemas.Autenticacion import LoginRequest, TokenResponse, UsuarioAutenticado
from Modelos.Autenticacion.Models.security import verify_password, create_access_token, get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación"],
)

@router.post("/login", response_model=TokenResponse)
def login(
    datos: LoginRequest,
    db: Session = Depends(get_db),
):
    correo = str(datos.correo).strip().lower()

    usuario = (
        db.query(Usuario)
        .filter(func.lower(Usuario.correo) == correo)
        .first()
    )

    if not usuario or not verify_password(
        datos.password,
        usuario.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    if (usuario.estado or "").strip().lower() != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está inactiva",
        )

    token = create_access_token({
        "sub": str(usuario.id_usuario),
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario,
    }

@router.get("/me", response_model=UsuarioAutenticado)
def obtener_usuario_actual(
    usuario: Usuario = Depends(get_current_user),
):
    return usuario