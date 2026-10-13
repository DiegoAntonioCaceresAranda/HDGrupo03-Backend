from sqlalchemy import Column, BigInteger, String, Text, Boolean
from app.database import Base

class Rol(Base):
    __tablename__ = "rol"

    id_rol = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)