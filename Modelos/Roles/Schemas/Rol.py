from pydantic import BaseModel, Field, ConfigDict

class RolBase(BaseModel):
    nombre: str = Field(
        min_length= 1,
        max_length= 100
    )
    descripcion: str | None = None

class RolCreate(RolBase):
    pass

class RolActualizar(BaseModel):
    nombre: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    descripcion: str | None = None

class RolResponse(RolBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    