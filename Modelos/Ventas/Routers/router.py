from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from Modelos.Ventas.Models.venta import Venta, DetalleVenta

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])

ZONA = timezone(timedelta(hours=-5))


class ItemVentaCreate(BaseModel):
    productoId: int
    nombre: str
    precioUnitario: float
    cantidad: int


class VentaCreate(BaseModel):
    tipoOrden: str
    ubicacion: Optional[str] = None
    cliente: Optional[str] = None
    metodoPago: str
    items: List[ItemVentaCreate]
    subtotal: float
    descuentoPorcentaje: float = 0
    descuentoMonto: float = 0
    impuesto: float = 0
    total: float


@router.get("/")
def listar_ventas(db: Session = Depends(get_db)):
    ventas_db = db.query(Venta).order_by(Venta.id_venta.desc()).all()
    
    # Obtenemos los nombres de los productos para armar el detalle
    filas_prod = db.execute(text("SELECT id_producto, nombre FROM producto")).mappings().all()
    mapa_productos = {r["id_producto"]: r["nombre"] for r in filas_prod}

    resultado = []
    for v in ventas_db:
        resultado.append({
            "id": v.id_venta,
            "ticket": v.ticket,
            "fecha": v.fecha.isoformat() if v.fecha else "",
            "tipoOrden": v.tipo_orden,
            "ubicacion": v.ubicacion,
            "cliente": v.cliente,
            "metodoPago": v.metodo_pago,
            "subtotal": float(v.subtotal or 0),
            "descuentoPorcentaje": float(v.descuento_porcentaje or 0),
            "descuentoMonto": float(v.descuento_monto or 0),
            "impuesto": float(v.impuesto or 0),
            "total": float(v.total or 0),
            "items": [
                {
                    "productoId": d.producto_id,
                    "nombre": mapa_productos.get(d.producto_id, f"Producto #{d.producto_id}"),
                    "precioUnitario": float(d.precio_unitario or 0),
                    "cantidad": d.cantidad,
                }
                for d in v.detalles
            ],
        })
    return resultado


@router.post("/")
def registrar_venta(datos: VentaCreate, db: Session = Depends(get_db)):
    if not datos.items:
        raise HTTPException(status_code=400, detail="La venta debe incluir al menos un producto.")

    try:
        # 1. Verificar stock y descontarlo en la tabla producto
        for item in datos.items:
            prod = (
                db.execute(
                    text("SELECT id_producto, nombre, stock FROM producto WHERE id_producto = :id"),
                    {"id": item.productoId},
                )
                .mappings()
                .first()
            )
            if not prod:
                raise HTTPException(
                    status_code=404,
                    detail=f"El producto '{item.nombre}' no existe en la base de datos.",
                )
            if prod["stock"] < item.cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente de '{prod['nombre']}' (disponible: {prod['stock']}).",
                )

            db.execute(
                text("UPDATE producto SET stock = stock - :cant WHERE id_producto = :id"),
                {"cant": item.cantidad, "id": item.productoId},
            )

        # 2. Calcular id_venta manual (porque autoincrement=False en venta.py)
        max_id_venta = db.query(func.coalesce(func.max(Venta.id_venta), 0)).scalar()
        nuevo_id_venta = int(max_id_venta) + 1
        ticket = str(1000 + nuevo_id_venta)
        ahora = datetime.now(ZONA)

        nueva_venta = Venta(
            id_venta=nuevo_id_venta,
            ticket=ticket,
            fecha=ahora,
            tipo_orden=datos.tipoOrden,
            ubicacion=datos.ubicacion,
            cliente=datos.cliente,
            metodo_pago=datos.metodoPago,
            subtotal=datos.subtotal,
            descuento_porcentaje=datos.descuentoPorcentaje,
            descuento_monto=datos.descuentoMonto,
            impuesto=datos.impuesto,
            total=datos.total,
        )
        db.add(nueva_venta)

        # 3. Calcular id_detalle_venta manual e insertar cada ítem
        max_id_detalle = db.query(func.coalesce(func.max(DetalleVenta.id_detalle_venta), 0)).scalar()
        siguiente_id_detalle = int(max_id_detalle) + 1

        for item in datos.items:
            detalle = DetalleVenta(
                id_detalle_venta=siguiente_id_detalle,
                cantidad=item.cantidad,
                precio_unitario=item.precioUnitario,
                venta_id=nuevo_id_venta,
                producto_id=item.productoId,
            )
            db.add(detalle)
            siguiente_id_detalle += 1

        db.commit()
        db.refresh(nueva_venta)

        return {
            "id": nueva_venta.id_venta,
            "ticket": nueva_venta.ticket,
            "fecha": nueva_venta.fecha.isoformat(),
            **datos.model_dump(),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar la venta: {str(e)}")