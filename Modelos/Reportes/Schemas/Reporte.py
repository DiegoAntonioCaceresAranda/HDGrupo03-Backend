from typing import List

from pydantic import BaseModel


class ResumenGanancia(BaseModel):
    total: float
    cambioPorcentaje: float


class ResumenPedidos(BaseModel):
    total: int
    cambioPorcentaje: float


class ResumenTicketPromedio(BaseModel):
    cantidad: float
    cambioPorcentaje: float


class ResumenDeliveryPendiente(BaseModel):
    contador: int


class ProductoDestacado(BaseModel):
    nombre: str
    valor: float
    alturaPcntj: int
    destacar: bool


class Transaccion(BaseModel):
    tiempo: str
    ordenId: str
    items: str
    estado: str
    cantidad: str


class ReporteVentasResponse(BaseModel):
    ganancia: ResumenGanancia
    pedidos: ResumenPedidos
    ticketPromedio: ResumenTicketPromedio
    deliveryPendiente: ResumenDeliveryPendiente
    productoDestacado: List[ProductoDestacado]
    transacciones: List[Transaccion]
