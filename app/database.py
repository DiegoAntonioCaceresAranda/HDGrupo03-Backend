import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Aquí se leerá la URL de tu base de datos PostgreSQL desde tu archivo .env
# Ejemplo: postgresql://usuario:contraseña@localhost:5432/nombre_base_datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "No se encontró DATABASE_URL en el archivo .env"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Función para obtener la sesión de la base de datos en cada petición
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()