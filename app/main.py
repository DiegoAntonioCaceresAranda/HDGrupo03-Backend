import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# 1. Cargamos las variables secretas que guardamos en el archivo .env
load_dotenv()

# 2. Configuramos Cloudinary utilizando las credenciales del servidor (¡Seguro!)
cloudinary.config(
    cloud_name=os.getenv("CLOUDBINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDBINARY_API_KEY"),
    api_secret=os.getenv("CLOUDBINARY_API_SECRET"),
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

@app.get("/")
def inicio():
  return {"mensaje": "¡Backend de Collins Café conectado y operativo!"}


# 3. Creamos la ruta POST para recibir el producto y su imagen
@app.post("/api/productos")
async def crear_producto(
    nombre: str = Form(...),  # Recibe el texto del nombre del producto
    imagen: UploadFile = File(
        ...
    ),  # Recibe el archivo de imagen enviado desde el cliente
):
  try:
    # 4. FastAPI toma el archivo y Python lo sube a Cloudinary de forma privada
    resultado = cloudinary.uploader.upload(imagen.file)

    # 5. Extraemos los datos clave que nos devuelve la nube
    public_id = resultado.get("public_id")
    secure_url = resultado.get("secure_url")

    # (Aquí más adelante conectaremos la base de datos para guardar 'nombre', 'public_id' y 'secure_url')

    return {
        "mensaje": "¡Imagen subida y procesada por el backend con éxito!",
        "producto": {
            "nombre": nombre,
            "public_id": public_id,
            "url": secure_url,
        },
    }

  except Exception as e:
    return {"error": f"Ocurrió un error al subir la imagen: {str(e)}"}