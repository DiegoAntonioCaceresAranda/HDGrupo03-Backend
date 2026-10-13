from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from Models.rol import Rol
from ..Schemas.Rol import RolCreate, RolActualizar, RolResponse

router = APIRouter (
    prefix="/api/roles",
    tags=["Roles"]
)

# Listar roles
@router.get("/", response_model= list[RolResponse])
def listar_roles(db: Session = Depends(get_db)):
    return db.query(Rol).order_by(Rol.id_rol).all()

# Crear rol
@router.post(
    "/",
    response_model=RolResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_rol(datos: RolCreate, db: Session = Depends(get_db)):
    rol = Rol(
        nombre=datos.nombre.strip(),
        descripcion=datos.descripcion
    )

    if not rol.nombre:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El nombre del rol no puede estar vacío"
        )

    db.add(rol)

    try:
        db.commit()
        db.refresh(rol)
        return rol
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un rol con ese nombre"
        )

# Actualizar rol
@router.put("/{id_rol}", response_model=RolResponse)
def actualizar_rol(
    id_rol: int,
    datos: RolActualizar,
    db: Session = Depends(get_db)
):
    rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()

    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    cambios = datos.model_dump(exclude_unset=True)

    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar"
        )

    if "nombre" in cambios:
        if cambios["nombre"] is None or not cambios["nombre"].strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El nombre del rol no puede estar vacío"
            )
        cambios["nombre"] = cambios["nombre"].strip()

    for campo, valor in cambios.items():
        setattr(rol, campo, valor)

    try:
        db.commit()
        db.refresh(rol)
        return rol
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro rol con ese nombre"
        )

# Eliminar rol
@router.delete("/{id_rol}")
def eliminar_rol(id_rol: int, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id_rol == id_rol).first()

    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )

    db.delete(rol)

    try:
        db.commit()
        return {
            "mensaje": "Rol eliminado correctamente",
            "id_rol": id_rol
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar el rol porque está relacionado con otros registros"
        )

# Buscar por nombre
@router.get("/buscar", response_model=list[RolResponse])
def buscar_roles_por_nombre(
    nombre: str,
    db: Session = Depends(get_db)
):
    roles = db.query(Rol).filter(
        Rol.nombre.ilike(f"%{nombre.strip()}%")
    ).order_by(Rol.id_rol).all()

    return roles