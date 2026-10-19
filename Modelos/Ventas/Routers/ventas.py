from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from Modelos.Productos.Models.producto import Producto
from Modelos.Ventas.Models.venta import Venta, DetalleVenta
from ..Schemas.venta import VentaCreate, VentaResponse, ItemVentaResponse

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])


def _dos_decimales(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _siguiente_id(db: Session, tabla: str, columna: str) -> int:
    """Tus modelos tienen autoincrement=False, así que el ID lo pedimos aquí.
    Usa la secuencia de PostgreSQL si existe; si no, MAX + 1."""
    secuencia = db.execute(
        text("SELECT pg_get_serial_sequence(:tabla, :columna)"),
        {"tabla": f"public.{tabla}", "columna": columna},
    ).scalar()
    if secuencia:
        return db.execute(
            text("SELECT nextval(CAST(:s AS regclass))"), {"s": secuencia}
        ).scalar_one()
    return db.execute(
        text(f"SELECT COALESCE(MAX({columna}), 0) + 1 FROM {tabla}")
    ).scalar_one()


def _armar_respuesta(venta: Venta, nombres: dict[int, str]) -> VentaResponse:
    return VentaResponse(
        id=venta.id_venta,
        ticket=venta.ticket,
        fecha=venta.fecha,
        tipoOrden=venta.tipo_orden,
        ubicacion=venta.ubicacion,
        cliente=venta.cliente,
        metodoPago=venta.metodo_pago,
        items=[
            ItemVentaResponse(
                productoId=d.producto_id,
                nombre=nombres.get(d.producto_id, "Producto eliminado"),
                precioUnitario=float(d.precio_unitario),
                cantidad=d.cantidad,
            )
            for d in venta.detalles
        ],
        subtotal=float(venta.subtotal),
        descuentoPorcentaje=float(venta.descuento_porcentaje),
        descuentoMonto=float(venta.descuento_monto),
        impuesto=float(venta.impuesto),
        total=float(venta.total),
    )


@router.get("/", response_model=list[VentaResponse])
def listar_ventas(limite: int = 100, db: Session = Depends(get_db)):
    ventas = db.query(Venta).order_by(Venta.fecha.desc()).limit(limite).all()

    ids = {d.producto_id for v in ventas for d in v.detalles}
    nombres = {}
    if ids:
        nombres = {
            p.id_producto: p.nombre
            for p in db.query(Producto).filter(Producto.id_producto.in_(ids)).all()
        }
    return [_armar_respuesta(v, nombres) for v in ventas]


@router.post("/", response_model=VentaResponse, status_code=201)
def registrar_venta(datos: VentaCreate, db: Session = Depends(get_db)):
    # Si el mismo producto viene dos veces, se suman las cantidades
    cantidades: dict[int, int] = {}
    for item in datos.items:
        cantidades[item.productoId] = cantidades.get(item.productoId, 0) + item.cantidad

    try:
        # Bloquea las filas para que dos ventas simultáneas no vendan el mismo stock
        productos = {
            p.id_producto: p
            for p in db.query(Producto)
            .filter(Producto.id_producto.in_(list(cantidades)))
            .order_by(Producto.id_producto)
            .with_for_update()
            .all()
        }

        for pid, cantidad in cantidades.items():
            producto = productos.get(pid)
            if producto is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"El producto con id {pid} ya no existe en el catálogo.",
                )
            if producto.stock < cantidad:
                raise HTTPException(
                    status_code=409,
                    detail=f'Stock insuficiente de "{producto.nombre}" (disponible: {producto.stock}).',
                )

        # Los precios salen de la base de datos, no del navegador
        subtotal = _dos_decimales(
            sum(
                Decimal(str(productos[pid].precio_venta)) * cantidad
                for pid, cantidad in cantidades.items()
            )
        )
        porcentaje = Decimal(str(datos.descuentoPorcentaje))
        descuento = _dos_decimales(subtotal * porcentaje / 100)
        impuesto = _dos_decimales(Decimal(str(datos.impuesto)))
        total = subtotal - descuento + impuesto

        id_venta = _siguiente_id(db, "venta", "id_venta")
        cliente = datos.cliente.strip() if datos.cliente else None
        ubicacion = datos.ubicacion.strip() if datos.ubicacion else None

        venta = Venta(
            id_venta=id_venta,
            ticket=str(1000 + id_venta),
            tipo_orden=datos.tipoOrden,
            ubicacion=ubicacion or None,
            cliente=cliente or None,
            metodo_pago=datos.metodoPago,
            subtotal=subtotal,
            descuento_porcentaje=porcentaje,
            descuento_monto=descuento,
            impuesto=impuesto,
            total=total,
        )
        db.add(venta)
        db.flush()  # la venta debe existir antes que sus detalles

        for pid, cantidad in cantidades.items():
            producto = productos[pid]
            db.add(
                DetalleVenta(
                    id_detalle_venta=_siguiente_id(db, "detalle_venta", "id_detalle_venta"),
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                    venta_id=id_venta,
                    producto_id=pid,
                )
            )
            db.flush()
            producto.stock -= cantidad

        db.commit()
        db.refresh(venta)
        nombres = {pid: p.nombre for pid, p in productos.items()}
        return _armar_respuesta(venta, nombres)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        print("ERROR DE INTEGRIDAD AL REGISTRAR VENTA:", e.orig)
        raise HTTPException(status_code=409, detail="No se pudo registrar la venta por un conflicto de datos.")
    except Exception as e:
        db.rollback()
        print("ERROR AL REGISTRAR VENTA:", repr(e))
        raise HTTPException(status_code=500, detail=f"Error al registrar la venta: {str(e)}")