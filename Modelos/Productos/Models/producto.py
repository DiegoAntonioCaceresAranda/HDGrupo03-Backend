from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey
from app.database import Base

class Producto(Base):
    __tablename__ = "producto"

    id_producto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    precio_venta = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"), nullable=True)
    image_url = Column(Text, nullable=True)
    image_public_id = Column(Text, nullable=True)
