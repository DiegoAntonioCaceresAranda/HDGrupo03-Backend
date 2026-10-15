from datetime import datetime, time, timedelta, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

from ..Schemas.Reporte import (
    ProductoDestacado,
    ReporteVentasResponse,
    ResumenDeliveryPendiente,
    ResumenGanancia,
    ResumenPedidos,
    ResumenTicketPromedio,
    Transaccion,
)

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])

# Perú no aplica horario de verano: offset fijo UTC-5.
ZONA = timezone(timedelta(hours=-5))
RANGOS_VALIDOS = ("Hoy", "Esta semana", "Este mes")


def _a_zona(fecha: datetime) -> datetime:
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc).astimezone(ZONA)
    return fecha.astimezone(ZONA)


def _formato_moneda(monto) -> str:
    return f"S/ {float(monto or 0):,.2f}"


def _hora(fecha: datetime) -> str:
    z = _a_zona(fecha)
    hora = z.hour % 12 or 12
    sufijo = "a. m." if z.hour < 12 else "p. m."
    return f"{hora:02d}:{z.minute:02d} {sufijo}"


def _cambio_porcentaje(actual: float, anterior: float) -> float:
    if anterior == 0:
        return 100.0 if actual > 0 else 0.0
    return round(((actual - anterior) / anterior) * 100, 1)


def _calcular_ventana(rango: str, ahora: datetime):
    inicio_dia = datetime.combine(ahora.date(), time.min, tzinfo=ZONA)
    fin_dia = inicio_dia + timedelta(days=1)

    if rango == "Hoy":
        inicio_anterior = inicio_dia - timedelta(days=1)
        return inicio_dia, fin_dia, inicio_anterior, inicio_dia

    if rango == "Esta semana":
        inicio = inicio_dia - timedelta(days=6)
        inicio_anterior = inicio - timedelta(days=7)
        return inicio, fin_dia, inicio_anterior, inicio

    # "Este mes"
    inicio = datetime(
        ahora.year, ahora.month, 1, tzinfo=ZONA
    )
    fin = datetime(
        ahora.year + (1 if ahora.month == 12 else 0),
        1 if ahora.month == 12 else ahora.month + 1,
        1,
        tzinfo=ZONA,
    )
    mes_anterior = ahora.month - 1 or 12
    anio_anterior = ahora.year if ahora.month > 1 else ahora.year - 1
    inicio_anterior = datetime(anio_anterior, mes_anterior, 1, tzinfo=ZONA)
    return inicio, fin, inicio_anterior, inicio


def _ventas_en_rango(db: Session, inicio: datetime, fin: datetime) -> List[Dict]:
    filas = (
        db.execute(
            text(
                "SELECT v.id_venta, v.ticket, v.fecha, v.tipo_orden, v.cliente, v.total, "
                "       dv.cantidad, dv.precio_unitario, p.nombre AS producto_nombre "
                "FROM venta v "
                "LEFT JOIN detalle_venta dv ON dv.venta_id = v.id_venta "
                "LEFT JOIN producto p ON p.id_producto = dv.producto_id "
                "WHERE v.fecha >= :inicio AND v.fecha < :fin "
                "ORDER BY v.fecha"
            ),
            {"inicio": inicio, "fin": fin},
        )
        .mappings()
        .all()
    )

    ventas: Dict[int, Dict] = {}
    for f in filas:
        venta = ventas.get(f["id_venta"])
        if venta is None:
            venta = {
                "id": f["id_venta"],
                "ticket": f["ticket"],
                "fecha": f["fecha"],
                "tipo_orden": f["tipo_orden"],
                "cliente": f["cliente"],
                "total": float(f["total"] or 0),
                "items": [],
            }
            ventas[f["id_venta"]] = venta
        if f["producto_nombre"] is not None:
            venta["items"].append(
                {
                    "nombre": f["producto_nombre"],
                    "precio_unitario": float(f["precio_unitario"] or 0),
                    "cantidad": int(f["cantidad"] or 0),
                }
            )
    return list(ventas.values())


def _productos_destacados(ventas: List[Dict]) -> List[ProductoDestacado]:
    totales: Dict[str, float] = {}
    for venta in ventas:
        for item in venta["items"]:
            totales[item["nombre"]] = totales.get(item["nombre"], 0.0) + (
                item["precio_unitario"] * item["cantidad"]
            )

    ordenados = sorted(totales.items(), key=lambda x: x[1], reverse=True)[:5]
    maximo = ordenados[0][1] if ordenados else 0.0

    return [
        ProductoDestacado(
            nombre=nombre,
            valor=round(valor, 2),
            alturaPcntj=round((valor / maximo) * 100) if maximo > 0 else 0,
            destacar=indice == 0,
        )
        for indice, (nombre, valor) in enumerate(ordenados)
    ]


def _transacciones(ventas: List[Dict]) -> List[Transaccion]:
    return [
        Transaccion(
            tiempo=_hora(v["fecha"]),
            ordenId=f"#{v['ticket']}",
            items=", ".join(
                f"{i['cantidad']}x {i['nombre']}" for i in v["items"]
            ),
            estado="Completado",
            cantidad=_formato_moneda(v["total"]),
        )
        for v in sorted(
            ventas, key=lambda x: x["fecha"], reverse=True
        )
    ]


@router.get("/ventas", response_model=ReporteVentasResponse)
def obtener_reporte_ventas(
    rango: str = Query(default="Esta semana"),
    db: Session = Depends(get_db),
):
    if rango not in RANGOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Rango inválido. Use uno de: {', '.join(RANGOS_VALIDOS)}",
        )

    ahora = datetime.now(ZONA)
    inicio, fin, inicio_anterior, fin_anterior = _calcular_ventana(rango, ahora)

    ventas_periodo = _ventas_en_rango(db, inicio, fin)
    ventas_anterior = _ventas_en_rango(db, inicio_anterior, fin_anterior)

    ganancia_total = sum(v["total"] for v in ventas_periodo)
    ganancia_anterior = sum(v["total"] for v in ventas_anterior)

    pedidos_total = len(ventas_periodo)
    pedidos_anterior = len(ventas_anterior)

    ticket_promedio = ganancia_total / pedidos_total if pedidos_total > 0 else 0.0
    ticket_promedio_anterior = (
        ganancia_anterior / pedidos_anterior if pedidos_anterior > 0 else 0.0
    )

    delivery_pendiente = sum(
        1 for v in ventas_periodo if v["tipo_orden"] == "Delivery"
    )

    return ReporteVentasResponse(
        ganancia=ResumenGanancia(
            total=round(ganancia_total, 2),
            cambioPorcentaje=_cambio_porcentaje(ganancia_total, ganancia_anterior),
        ),
        pedidos=ResumenPedidos(
            total=pedidos_total,
            cambioPorcentaje=_cambio_porcentaje(pedidos_total, pedidos_anterior),
        ),
        ticketPromedio=ResumenTicketPromedio(
            cantidad=round(ticket_promedio, 2),
            cambioPorcentaje=_cambio_porcentaje(
                ticket_promedio, ticket_promedio_anterior
            ),
        ),
        deliveryPendiente=ResumenDeliveryPendiente(contador=delivery_pendiente),
        productoDestacado=_productos_destacados(ventas_periodo),
        transacciones=_transacciones(ventas_periodo),
    )
