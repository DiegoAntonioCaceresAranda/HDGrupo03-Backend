from sqlalchemy import Column, Integer, String
from app.database import Base

class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    nombre = Column(String, unique=True, nullable=False)
    