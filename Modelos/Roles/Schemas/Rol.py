from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class RolBase(BaseModel):
    nombre: str = Field(
        min_length= 2,
        max_length= 50
    )
    descripcion: Optional[str] = Field(
        default= None,
        max_length= 255
    )

class RolCreate(RolBase):
    pass

class RolUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default= None,
        min_length= 2,
        max_length= 50
    )
    descripcion: Optional[str] = Field(
        default= None,
        max_length= 255
    )

class RolResponse(RolBase):
    id: int
    created_at: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
    