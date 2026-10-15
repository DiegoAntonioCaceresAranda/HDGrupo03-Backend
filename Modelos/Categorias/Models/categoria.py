from sqlalchemy import Column, Integer, String
from app.database import Base

class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, unique=True, nullable=False)
    estado = Column(String, default="Activo", nullable=False)