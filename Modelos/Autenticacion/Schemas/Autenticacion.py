from pydantic import BaseModel, ConfigDict, EmailStr

class LoginRequest(BaseModel):
    correo: EmailStr
    password: str

class UsuarioAutenticado(BaseModel):
    id_usuario: int
    codigo: str
    nombre: str
    correo: EmailStr
    estado: str
    id_rol: int

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioAutenticado

