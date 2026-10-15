import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from Modelos.Productos.Models.producto import Producto  
from Modelos.Categorias.Models.categoria import Categoria
from ..Schemas.Producto import ProductoCreate, ProductoUpdate, ProductoResponse



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
def crear_producto(datos: ProductoCreate, db: Session = Depends(get_db)):
    # Verificar si el nombre del producto ya existe
    existente = db.query(Producto).filter(Producto.nombre == datos.nombre). first()
    if existente:
        raise HTTPException(status_code=409, detail="El producto ya está registrado")

    # Verificar que la categoria exista
    categoria = db.query(Categoria).filter(Categoria.id_categoria == datos.id_Categoria).first()
    if categoria is None:
        raise HTTPException(status_code=400, detail="La categoría seleccionada no existe")

    try:
        # Obtener el siguiente ID de PostgreSQL
        nuevo_id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('public.producto', 'id_producto'))")
        ).scalar_one()

        # Generar el código a partir del ID
        codigo = f"PROD-{nuevo_id:03d}"

        nuevo_producto = Producto(
            id_producto=nuevo_id,
            codigo=codigo,
            nombre=datos.nombre,
            precio_venta=datos.precio_venta,
            stock=datos.stock,
            imagen_url=datos.imagen_url,
            estado=datos.estado,
            id_categoria=datos.id_categoria
        )

        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        return nuevo_producto

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo crear el producto. Verifica que el nombre y código sean únicos."
        )

# Subir imagen de un producto a Cloudinary
@router.post("/{id_producto}/imagen", response_model=ProductoResponse)
def subir_imagen_producto(
    id_producto: int,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    try:
        resultado = cloudinary.uploader.upload(imagen.file)
        producto.imagen_url = resultado.get("secure_url")
        db.commit()
        db.refresh(producto)
        return producto
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen a Cloudinary: {str(e)}")

# Actualizar producto
@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(id_producto: int, datos: ProductoUpdate, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    cambios = datos.model_dump(exclude_unset=True)

    if "id_categoria" in cambios:
        categoria = db.query(Categoria).filter(Categoria.id_categoria == cambios["id_categoria"]).first()
        if categoria is None:
            raise HTTPException(status_code=400, detail="La categoría seleccionada no existe")

    if "nombre" in cambios:
        duplicado = db.query(Producto).filter(
            Producto.nombre == cambios["nombre"],
            Producto.id_producto != id_producto
        ).first()
        if duplicado:
            raise HTTPException(status_code=409, detail="El nombre del producto ya está registrado")

    try:
        for campo, valor in cambios.items():
            setattr(producto, campo, valor)
        db.commit()
        db.refresh(producto)
        return producto

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo actualizar: existe un dato duplicado")

# Eliminar producto
@router.delete("/{id_producto}")
def eliminar_producto(id_producto: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(producto)
    db.commit()
    return {"mensaje": "Producto eliminado correctamente"}