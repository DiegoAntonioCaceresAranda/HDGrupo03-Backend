import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from Modelos.Autenticacion.Routers.auth import router as auth_router
from Modelos.Roles.Routers.roles import router as roles_router
from Modelos.Usuarios.Routers.usuarios import router as usuarios_router
from Modelos.Categorias.Routers.router import router as categorias_router
from Modelos.Productos.Routers.router import router as productos_router
from Modelos.Dashboard.Routers.dashboard import router as dashboard_router
from Modelos.Reportes.Routers.reportes import router as reportes_router

# 1. Cargamos las variables secretas que guardamos en el archivo .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# 2. Configuramos Cloudinary utilizando las credenciales del servidor
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# Inicializamos la aplicación de FastAPI
app = FastAPI(
    title="Collins Café API",
    description="Backend oficial con FastAPI, PostgreSQL y Cloudinary",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(roles_router)
app.include_router(usuarios_router)
app.include_router(categorias_router)
app.include_router(productos_router)
app.include_router(dashboard_router)
app.include_router(reportes_router)

@app.get("/")
def inicio():
    return {"mensaje": "¡Backend de Collins Café conectado y operativo!"}