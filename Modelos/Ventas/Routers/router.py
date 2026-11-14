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

ESTADO_PENDIENTE = "pendiente"
ESTADO_COMPLETADA = "completada"


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
    # Si viene, es el pendiente que se retomó: se elimina al guardar/cobrar.
    pendienteId: Optional[int] = None


def _mapa_productos(db: Session) -> dict:
    filas = db.execute(text("SELECT id_producto, nombre FROM producto")).mappings().all()
    return {r["id_producto"]: r["nombre"] for r in filas}


def _serializar_venta(v: Venta, mapa_productos: dict) -> dict:
    return {
        "id": v.id_venta,
        "ticket": v.ticket,
        "fecha": v.fecha.isoformat() if v.fecha else "",
        "estado": v.estado,
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
    }


def _validar_y_descontar_stock(db: Session, items: List[ItemVentaCreate]) -> None:
    for item in items:
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


def _crear_venta(datos: VentaCreate, db: Session, estado: str) -> Venta:
    max_id_venta = db.query(func.coalesce(func.max(Venta.id_venta), 0)).scalar()
    nuevo_id_venta = int(max_id_venta) + 1
    ticket = str(1000 + nuevo_id_venta)

    nueva_venta = Venta(
        id_venta=nuevo_id_venta,
        ticket=ticket,
        fecha=datetime.now(ZONA),
        estado=estado,
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

    max_id_detalle = db.query(func.coalesce(func.max(DetalleVenta.id_detalle_venta), 0)).scalar()
    siguiente_id_detalle = int(max_id_detalle) + 1

    for item in datos.items:
        db.add(
            DetalleVenta(
                id_detalle_venta=siguiente_id_detalle,
                cantidad=item.cantidad,
                precio_unitario=item.precioUnitario,
                venta_id=nuevo_id_venta,
                producto_id=item.productoId,
            )
        )
        siguiente_id_detalle += 1

    return nueva_venta


def _eliminar_pendiente(db: Session, id_venta: Optional[int]) -> None:
    """Borra un pendiente (si existe y sigue pendiente). No toca ventas completadas."""
    if id_venta is None:
        return
    venta = (
        db.query(Venta)
        .filter(Venta.id_venta == id_venta, Venta.estado == ESTADO_PENDIENTE)
        .first()
    )
    if venta:
        db.delete(venta)  # cascade borra sus detalles


# ---------------------------------------------------------------
# Ventas completadas
# ---------------------------------------------------------------
@router.get("/")
def listar_ventas(db: Session = Depends(get_db)):
    ventas_db = (
        db.query(Venta)
        .filter(Venta.estado == ESTADO_COMPLETADA)
        .order_by(Venta.id_venta.desc())
        .all()
    )
    mapa = _mapa_productos(db)
    return [_serializar_venta(v, mapa) for v in ventas_db]


@router.post("/")
def registrar_venta(datos: VentaCreate, db: Session = Depends(get_db)):
    if not datos.items:
        raise HTTPException(status_code=400, detail="La venta debe incluir al menos un producto.")

    try:
        _validar_y_descontar_stock(db, datos.items)
        nueva_venta = _crear_venta(datos, db, ESTADO_COMPLETADA)
        _eliminar_pendiente(db, datos.pendienteId)
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


# ---------------------------------------------------------------
# Ventas pendientes
# ---------------------------------------------------------------
@router.get("/pendientes")
def listar_pendientes(db: Session = Depends(get_db)):
    ventas_db = (
        db.query(Venta)
        .filter(Venta.estado == ESTADO_PENDIENTE)
        .order_by(Venta.id_venta.desc())
        .all()
    )
    mapa = _mapa_productos(db)
    return [_serializar_venta(v, mapa) for v in ventas_db]


@router.post("/pendientes")
def guardar_pendiente(datos: VentaCreate, db: Session = Depends(get_db)):
    if not datos.items:
        raise HTTPException(status_code=400, detail="La orden debe incluir al menos un producto.")

    try:
        # Un pendiente NO descuenta stock.
        nueva_venta = _crear_venta(datos, db, ESTADO_PENDIENTE)
        # Si se retomó un pendiente y se vuelve a guardar, se reemplaza el anterior.
        _eliminar_pendiente(db, datos.pendienteId)
        db.commit()
        db.refresh(nueva_venta)
        return _serializar_venta(nueva_venta, _mapa_productos(db))

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar el pendiente: {str(e)}")


@router.delete("/{id_venta}")
def cancelar_pendiente(id_venta: int, db: Session = Depends(get_db)):
    venta = db.query(Venta).filter(Venta.id_venta == id_venta).first()
    if not venta:
        raise HTTPException(status_code=404, detail="La venta no existe.")
    if venta.estado != ESTADO_PENDIENTE:
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar ventas pendientes.")

    try:
        db.delete(venta)
        db.commit()
        return {"mensaje": "Pendiente cancelado."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cancelar el pendiente: {str(e)}")