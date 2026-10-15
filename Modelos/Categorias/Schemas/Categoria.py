from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoriaCreate(BaseModel):
    nombre: str

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None

class CategoriaResponse(BaseModel):
    id_categoria: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)