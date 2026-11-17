from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

TipoOrden = Literal["En Local", "Para Llevar", "Delivery"]
MetodoPago = Literal["Efectivo", "Tarjeta", "QR / Transferencia"]


class ItemVentaCreate(BaseModel):
    productoId: int
    cantidad: int = Field(gt=0)


class VentaCreate(BaseModel):
    tipoOrden: TipoOrden
    ubicacion: Optional[str] = None
    cliente: Optional[str] = None
    metodoPago: MetodoPago
    items: List[ItemVentaCreate] = Field(min_length=1)
    descuentoPorcentaje: float = Field(0, ge=0, le=100)
    impuesto: float = Field(0, ge=0)


class ItemVentaResponse(BaseModel):
    productoId: int
    nombre: str
    precioUnitario: float
    cantidad: int


class VentaResponse(BaseModel):
    id: int
    ticket: str
    fecha: datetime
    tipoOrden: str
    ubicacion: Optional[str] = None
    cliente: Optional[str] = None
    metodoPago: str
    items: List[ItemVentaResponse]
    subtotal: float
    descuentoPorcentaje: float
    descuentoMonto: float
    impuesto: float
    total: float