from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    contraseña = Column(String, nullable=False)
    estado = Column(String, default="Activo", nullable=False)

    id_rol = Column(Integer, ForeignKey("rol.id_rol"), nullable=False)