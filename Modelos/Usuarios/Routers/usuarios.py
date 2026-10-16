from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash
from app.database import get_db
from Modelos.Autenticacion.Models.security import hash_password
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
    # Verificar si el correo ya existe
    existente = db.query(Usuario).filter(
        Usuario.correo == str(datos.correo)
    ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado"
        )

    # Verificar que el rol exista
    rol = db.query(Rol).filter(
        Rol.id_rol == datos.id_rol
    ).first()

    if rol is None:
        raise HTTPException(
            status_code=400,
            detail="El rol seleccionado no existe"
        )

    try:
        # Obtener el siguiente ID de PostgreSQL
        nuevo_id = db.execute(
            text("""
                SELECT nextval(
                    pg_get_serial_sequence(
                        'public.usuario',
                        'id_usuario'
                    )
                )
            """)
        ).scalar_one()

        # Generar el código a partir del ID
        codigo = f"USR-{nuevo_id:03d}"

        nuevo_usuario = Usuario(
            id_usuario=nuevo_id,
            codigo=codigo,
            nombre=datos.nombre,
            correo=str(datos.correo),
            password=hash_password(datos.password),
            estado=datos.estado,
            id_rol=datos.id_rol
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)

        return nuevo_usuario

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear el usuario. "
                   "Verifica que el correo y el código sean únicos."
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
            cambios["password"] = hash_password(
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