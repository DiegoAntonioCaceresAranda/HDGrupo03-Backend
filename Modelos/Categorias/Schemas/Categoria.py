from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoriaCreate(BaseModel):
    nombre: str
    estado: str = "Activo"

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    estado: Optional[str] = None

class CategoriaResponse(BaseModel):
    id_categoria: int
    codigo: str
    nombre: str
    estado: str
    model_config = ConfigDict(from_attributes=True)