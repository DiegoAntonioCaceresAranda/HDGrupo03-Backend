from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional

class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    estado: str = "Activo"
    id_rol: int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    estado: Optional[str] = None
    id_rol: Optional[int] = None


class UsuarioResponse(BaseModel):
    id_usuario: int
    codigo: str
    nombre: str
    correo: EmailStr
    estado: str
    id_rol: int
    model_config = ConfigDict(from_attributes=True)