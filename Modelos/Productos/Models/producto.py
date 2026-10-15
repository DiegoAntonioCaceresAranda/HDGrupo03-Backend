from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Producto(Base):
    __tablename__ = "producto"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, unique=True, nullable=False)
    precio_venta = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    imagen_url = Column(String, nullable=True)
    estado = Column(String, default="Activo", nullable=False)

    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"), nullable=False)