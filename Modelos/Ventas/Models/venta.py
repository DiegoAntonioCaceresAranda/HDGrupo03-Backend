from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Venta(Base):
    __tablename__ = "venta"

    id_venta = Column(Integer, primary_key=True, index=True, autoincrement=False)
    ticket = Column(String(50), nullable=False)
    fecha = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    tipo_orden = Column(String(50), nullable=False)
    ubicacion = Column(String(255), nullable=True)
    cliente = Column(String(255), nullable=True)
    metodo_pago = Column(String(50), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, server_default="0")
    descuento_porcentaje = Column(Numeric(5, 2), nullable=False, server_default="0")
    descuento_monto = Column(Numeric(12, 2), nullable=False, server_default="0")
    impuesto = Column(Numeric(12, 2), nullable=False, server_default="0")
    total = Column(Numeric(12, 2), nullable=False, server_default="0")

    # usuario.id_usuario no se declara como ForeignKey para no acoplar el
    # modulo de Ventas con el modulo de Usuarios (evita conflictos al mergear).
    id_usuario = Column(Integer, nullable=True)

    detalles = relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
    )


class DetalleVenta(Base):
    __tablename__ = "detalle_venta"

    id_detalle_venta = Column(
        Integer, primary_key=True, index=True, autoincrement=False
    )
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    venta_id = Column(Integer, ForeignKey("venta.id_venta"), nullable=False)
    # producto.id_producto se maneja como entero simple para no acoplar
    # el modulo de Ventas con el modulo de Productos.
    producto_id = Column(Integer, nullable=False)

    venta = relationship("Venta", back_populates="detalles")
