from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from Modelos.Categorias.Models.categoria import Categoria
from ..Schemas.Categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse

router = APIRouter(
    prefix="/api/categorias",
    tags=["Categorías"]
)

# Listar categorías
@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.id_categoria).all()

# Create (Crear) categoría
@router.post("/", response_model=CategoriaResponse, status_code=201)
def crear_categoria(datos: CategoriaCreate, db: Session = Depends(get_db)):
    existente = db.query(Categoria).filter(Categoria.nombre == datos.nombre).first()
    if existente:
        raise HTTPException(status_code=409, detail="La categoría ya está registrada")

    try:
        nuevo_id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('public.categoria', 'id_categoria'))")
        ).scalar_one()

        codigo = f"CAT-{nuevo_id:03d}"

        nueva_categoria = Categoria(
            id_categoria=nuevo_id,
            codigo=codigo,
            nombre=datos.nombre,
            estado=datos.estado
        )

        db.add(nueva_categoria)
        db.commit()
        db.refresh(nueva_categoria)
        return nueva_categoria

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear la categoría. Verifica que el nombre y código sean únicos."
        )

# Update (Actualizar) categoría
@router.put("/{id_categoria}", response_model=CategoriaResponse)
def actualizar_categoria(id_categoria: int, datos: CategoriaUpdate, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    cambios = datos.model_dump(exclude_unset=True)

    if "nombre" in cambios:
        duplicado = db.query(Categoria).filter(
            Categoria.nombre == cambios["nombre"],
            Categoria.id_categoria != id_categoria
        ).first()
        if duplicado:
            raise HTTPException(status_code=409, detail="El nombre de la categoría ya está registrado")

    try:
        for campo, valor in cambios.items():
            setattr(categoria, campo, valor)
        db.commit()
        db.refresh(categoria)
        return categoria

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo actualizar: existe un dato duplicado")

# Delete (Eliminar) categoría
@router.delete("/{id_categoria}")
def eliminar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada correctamente"}