from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash
from app.database import get_db
from Modelos.Usuarios.Models.usuario import Usuario
from Modelos.Roles.Models.rol import Rol
from ..Schemas.Usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter (
    prefix= "/api/usuarios",
    tags= ["Usuarios"]
)

password_hash = PasswordHash.recommended()

# Listar usuarios
@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(
        Usuario.id_usuario
    ).all()

# Crear usuario
@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=201
)
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db)
):
    duplicado = db.query(Usuario).filter(
        (Usuario.codigo == datos.codigo) |
        (Usuario.correo == str(datos.correo))
    ).first()

    if duplicado:
        raise HTTPException(
            status_code=409,
            detail="El código o correo ya está registrado"
        )

    rol = db.query(Rol).filter(
        Rol.id_rol == datos.id_rol
    ).first()

    if rol is None:
        raise HTTPException(
            status_code=400,
            detail="El rol seleccionado no existe"
        )

    nuevo_usuario = Usuario(
        codigo=datos.codigo,
        nombre=datos.nombre,
        correo=str(datos.correo),
        password=password_hash.hash(datos.password),
        estado=datos.estado,
        id_rol=datos.id_rol
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El código o correo ya está registrado"
        )

# Actualizar usuario
@router.put(
    "/{id_usuario}",
    response_model=UsuarioResponse
)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    cambios = datos.model_dump(exclude_unset=True)

    # No guardar cadenas vacías como contraseña
    if "password" in cambios:
        if not cambios["password"]:
            cambios.pop("password")
        else:
            cambios["password"] = password_hash.hash(
                cambios["password"]
            )

    if "id_rol" in cambios:
        rol = db.query(Rol).filter(
            Rol.id_rol == cambios["id_rol"]
        ).first()

        if rol is None:
            raise HTTPException(
                status_code=400,
                detail="El rol seleccionado no existe"
            )

    for campo in ("codigo", "correo"):
        if campo in cambios:
            valor = str(cambios[campo])

            duplicado = db.query(Usuario).filter(
                getattr(Usuario, campo) == valor,
                Usuario.id_usuario != id_usuario
            ).first()

            if duplicado:
                raise HTTPException(
                    status_code=409,
                    detail=f"El {campo} ya está registrado"
                )

            cambios[campo] = valor

    try:
        for campo, valor in cambios.items():
            setattr(usuario, campo, valor)

        db.commit()
        db.refresh(usuario)
        return usuario

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar: existe un dato duplicado"
        )

# ELIMINAR USUARIO
@router.delete("/{id_usuario}")
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    db.delete(usuario)
    db.commit()

    return {
        "mensaje": "Usuario eliminado correctamente"
    }