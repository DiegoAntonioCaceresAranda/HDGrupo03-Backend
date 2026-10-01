import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Aquí se leerá la URL de tu base de datos PostgreSQL desde tu archivo .env
# Ejemplo: postgresql://usuario:contraseña@localhost:5432/nombre_base_datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/collinscafe"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Función para obtener la sesión de la base de datos en cada petición
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()