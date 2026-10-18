from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from Modelos.Ventas.Models.venta import Venta

from ..Schemas.Dashboard import (
    ActivityItem,
    AttentionOrder,
    HomeDashboardResponse,
    LowStockProduct,
    QuickStats,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Perú no aplica horario de verano: offset fijo UTC-5.
ZONA = timezone(timedelta(hours=-5))
UMBRAL_STOCK_BAJO = 15


def _a_zona(fecha: datetime) -> datetime:
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc).astimezone(ZONA)
    return fecha.astimezone(ZONA)


def _formato_moneda(monto) -> str:
    return f"S/ {float(monto or 0):,.2f}"


def _tiempo_relativo(fecha: datetime, ahora: datetime) -> str:
    minutos = max(0, round((ahora - _a_zona(fecha)).total_seconds() / 60))
    if minutos < 1:
        return "Justo ahora"
    if minutos < 60:
        return f"Hace {minutos} min"
    horas = round(minutos / 60)
    if horas < 24:
        return f"Hace {horas} h"
    return f"Hace {round(horas / 24)} d"


@router.get("", response_model=HomeDashboardResponse)
def obtener_resumen_dashboard(db: Session = Depends(get_db)):
    ahora = datetime.now(ZONA)
    inicio_dia = datetime.combine(ahora.date(), time.min, tzinfo=ZONA)
    fin_dia = inicio_dia + timedelta(days=1)

    ventas_hoy = (
        db.query(Venta)
        .filter(Venta.fecha >= inicio_dia, Venta.fecha < fin_dia)
        .order_by(Venta.fecha)
        .all()
    )

    today_sales = sum(float(v.total or 0) for v in ventas_hoy)
    today_orders = len(ventas_hoy)
    new_customers_today = len(
        {
            v.cliente.strip().lower()
            for v in ventas_hoy
            if v.cliente and v.cliente.strip()
        }
    )

    delivery_hoy = [v for v in ventas_hoy if v.tipo_orden == "Delivery"]
    attention_orders = [
        AttentionOrder(
            orderId=f"#{v.ticket}",
            customerName=(
                v.cliente.strip()
                if v.cliente and v.cliente.strip()
                else "Cliente de mostrador"
            ),
            reason="Por despachar",
            amount=_formato_moneda(v.total),
        )
        for v in reversed(delivery_hoy[-5:])
    ]

    filas_stock = (
        db.execute(
            text(
                "SELECT id_producto, nombre, stock FROM producto "
                "WHERE stock < :umbral ORDER BY stock ASC LIMIT 5"
            ),
            {"umbral": UMBRAL_STOCK_BAJO},
        )
        .mappings()
        .all()
    )
    low_stock_products = [
        LowStockProduct(
            productId=str(f["id_producto"]),
            name=f["nombre"],
            stock=f["stock"],
            threshold=UMBRAL_STOCK_BAJO,
        )
        for f in filas_stock
    ]

    recientes = db.query(Venta).order_by(Venta.fecha.desc()).limit(5).all()
    actividad_ventas = [
        ActivityItem(
            id=f"venta-{v.id_venta}",
            type="order",
            message=(
                f"Venta #{v.ticket} registrada"
                f"{' para ' + v.cliente.strip() if v.cliente and v.cliente.strip() else ''}"
                f" ({_formato_moneda(v.total)})"
            ),
            time=_tiempo_relativo(v.fecha, ahora),
        )
        for v in recientes
    ]
    actividad_stock = [
        ActivityItem(
            id=f"stock-{p.productId}",
            type="stock",
            message=f"{p.name} quedó con stock bajo ({p.stock} uds.)",
            time="Actualizado ahora",
        )
        for p in low_stock_products[:3]
    ]
    activity = (actividad_ventas + actividad_stock)[:8]

    return HomeDashboardResponse(
        quickStats=QuickStats(
            todaySales=today_sales,
            todayOrders=today_orders,
            newCustomersToday=new_customers_today,
        ),
        attentionOrders=attention_orders,
        lowStockProducts=low_stock_products,
        activity=activity,
    )
