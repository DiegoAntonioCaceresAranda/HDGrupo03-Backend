from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductoCreate(BaseModel):
    nombre: str
    precio_venta: float
    stock: int = 0
    id_categoria: Optional[int] = None

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio_venta: Optional[float] = None
    stock: Optional[int] = None
    id_categoria: Optional[int] = None

class ProductoResponse(BaseModel):
    id_producto: int
    codigo: str
    nombre: str
    precio_venta: float
    stock: int
    id_categoria: Optional[int] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)