from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductoCreate(BaseModel):
    nombre: str
    precio_venta: float
    stock: int = 0
    imagen_url: Optional[str] = None
    estado: str = "Activo"
    id_categoria: int

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio_venta: Optional[float] = None
    stock: Optional[int] = None
    imagen_url: Optional[str] = None
    estado: Optional[str] = None
    id_categoria: Optional[int] = None

class ProductoResponse(BaseModel):
    id_producto: int
    codigo: str
    nombre: str
    precio_venta: float
    stock: int
    imagen_url: Optional[str] = None
    estado: str
    id_categoria: int
    model_config = ConfigDict(from_attributes=True)