from typing import Optional
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from Modelos.Productos.Models.producto import Producto
from Modelos.Categorias.Models.categoria import Categoria
from ..Schemas.Producto import ProductoResponse



router = APIRouter(
    prefix="/api/productos",
    tags=["Productos"]
)


# Listar productos (GET)
@router.get("/", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).order_by(Producto.id_producto).all()


# Crrear producto (POST)
@router.post("/", response_model=ProductoResponse, status_code=201)
def crear_producto(
    nombre: str = Form(...),
    precio_venta: float = Form(...),
    stock: int = Form(0),
    id_categoria: Optional[int] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Verificar que la categoría exista si se envió una
    if id_categoria is not None:
        categoria = db.query(Categoria).filter(
            Categoria.id_categoria == id_categoria
        ).first()
        if categoria is None:
            raise HTTPException(status_code=400, detail="La categoría seleccionada no existe")

    try:
        # Subir imagen a Cloudinary si el usuario adjuntó un archivo
        image_url = None
        image_public_id = None

        if imagen is not None and imagen.filename:
            resultado = cloudinary.uploader.upload(imagen.file)
            image_public_id = resultado.get("public_id")
            image_url = resultado.get("secure_url")

        # Obtener el siguiente ID de PostgreSQL y generar el código PROD-001
        nuevo_id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('public.producto', 'id_producto'))")
        ).scalar_one()

        codigo = f"PROD-{nuevo_id:03d}"

        nuevo_producto = Producto(
            id_producto=nuevo_id,
            codigo=codigo,
            nombre=nombre,
            precio_venta=precio_venta,
            stock=stock,
            id_categoria=id_categoria,
            image_url=image_url,
            image_public_id=image_public_id
        )

        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        return nuevo_producto

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear el producto. Verifica que el código sea único."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar el producto o subir la imagen: {str(e)}"
        )

    
@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    nombre: Optional[str] = Form(None),
    precio_venta: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    id_categoria: Optional[int] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if id_categoria is not None:
        categoria = db.query(Categoria).filter(
            Categoria.id_categoria == id_categoria
        ).first()
        if categoria is None:
            raise HTTPException(status_code=400, detail="La categoría seleccionada no existe")
        producto.id_categoria = id_categoria

    if nombre is not None:
        producto.nombre = nombre
    if precio_venta is not None:
        producto.precio_venta = precio_venta
    if stock is not None:
        producto.stock = stock

    try:
        # Si envían una nueva imagen, borramos la anterior de Cloudinary y subimos la nueva
        if imagen is not None and imagen.filename:
            if producto.image_public_id:
                cloudinary.uploader.destroy(producto.image_public_id)
            resultado = cloudinary.uploader.upload(imagen.file)
            producto.image_public_id = resultado.get("public_id")
            producto.image_url = resultado.get("secure_url")

        db.commit()
        db.refresh(producto)
        return producto

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo actualizar: dato duplicado")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el producto: {str(e)}")

    
# 4. Eliminar producto (y borrar su imagen de Cloudinary si tenía una)
@router.delete("/{id_producto}")
def eliminar_producto(id_producto: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if producto.image_public_id:
        try:
            cloudinary.uploader.destroy(producto.image_public_id)
        except Exception:
            pass

    db.delete(producto)
    db.commit()
    return {"mensaje": "Producto eliminado correctamente"}