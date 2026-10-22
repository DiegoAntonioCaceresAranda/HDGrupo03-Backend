# ☕ Collins Café — Backend API
Backend oficial del sistema web Collins Café, una aplicación diseñada para facilitar la administración y gestión de una cafetería mediante una API REST.

El sistema está desarrollado con FastAPI y Python, utiliza PostgreSQL para la persistencia de datos, SQLAlchemy para el acceso a la base de datos y Cloudinary para la gestión de imágenes.

---

## 📋 Tabla de Contenidos
-

---

## 🌐 Enlaces del sistema
| Recurso | Enlace |
| :--- | :--- |
| **Menú  Principal** | https://hd-grupo03-fronted.vercel.app/ |
| **Carta Principal** | https://hd-grupo03-fronted.vercel.app/carta-principal |
| **Login** | https://hd-grupo03-fronted.vercel.app/login |
| **Dashboard** | https://hd-grupo03-fronted.vercel.app/admin |

---

## 👨‍🏫 Acceso para el docente
Se proporciona una cuenta de demostración para que el docente pueda ingresar al aplicativo y evaluar sus funcionalidades.

| Dato | Enlace |
| :--- | :--- |
| **Correo Electronico** | admin@collinscafe.com |
| **Contraseña** | admin123 |
| **Rol** | Administrador |

---

## 🚀 Funcionalidades del backend

* **Autenticación:** inicio de sesión y validación del acceso de los usuarios.
* **Roles:** administración de los roles del sistema.
* **Usuarios:** registro y gestión de las cuentas de usuario.
* **Categorías:** organización de las categorías de productos.
* **Productos:** administración de los productos de la cafetería.
* **Dashboard:** acceso a la información necesaria para el panel principal.
* **Reportes:** consulta de información para los reportes del sistema.

---

## 🛠️ Tecnologías utilizadas

* **Python**
* **FastAPI**
* **SQLAlchemy**
* **PostgreSQL**
* **Supabase**
* **Cloudinary**
* **JWT mediante python-jose**
* **Hash de contraseñas con pwdlib y Argon2**
* **Pydantic**
* **Uvicorn**
* **Render**
* **React y TypeScript para el frontend integrado**

## 📋 Requisitos previos
Para ejecutar el backend localmente se necesita:

* **Python compatible con las versiones de las dependencias instaladas.**
* **pip.**
* **Git.**
* **Una base de datos PostgreSQL accesible.**
* **Credenciales de Cloudinary si se utilizará la gestión de imágenes.**

## 📥 Instalación
1. **Clonar el repositorio**
```bash
git clone [https://github.com/DiegoAntonioCaceresAranda/HDGrupo03-Backend.git]
```

2. **Crear un entorno virtual**
```bash
"python -m venv venv"
```

Activar el entorno virtual en Windows:
```bash
"venv\Scripts\activate"
```

3. **Instalar las dependencias**
```bash
"pip install -r requirements.txt"
``` 

## ⚙️ Configuración de variables de entorno
El backend carga las variables de entorno desde un archivo .env ubicado en la carpeta donde se encuentra main.py, según la configuración actual.

Crear el archivo con las variables requeridas por la implementación:
```text
DATABASE_URL=URL_DE_CONEXION_POSTGRESQL

CLOUDINARY_CLOUD_NAME=TU_CLOUD_NAME
CLOUDINARY_API_KEY=TU_API_KEY
CLOUDINARY_API_SECRET=TU_API_SECRET

# Agregar las variables de autenticación JWT
# con los nombres que utiliza el código del proyecto.
```
Los nombres y valores de las variables relacionadas con JWT deben coincidir con los definidos en el módulo de autenticación.

Seguridad: no subir el archivo .env al repositorio. En Render, configurar las variables desde el apartado de variables de entorno del servicio.

## ▶️ Ejecutar el backend localmente
Desde la raíz del proyecto:
```bash
"uvicorn app.main:app --reload"
```

Este comando corresponde a la estructura app/main.py. Si el archivo main.py está directamente en la raíz o tiene otra ubicación, el comando debe ajustarse.

Al iniciar el servidor, se puede acceder a:

* **API local:** http://127.0.0.1:8000/
* **Swagger:** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

La ruta raíz devuelve un mensaje que indica que el backend está operativo.

## 🔌 Endpoints y documentación de la API
La aplicación registra los routers de los siguientes módulos:

| Módulo | Router registrado |
| :--- | :--- |
| **Autenticación** | auth_router |
| **Roles** | roles_router |
| **Usuarios** | usuarios_router |
| **Categorías** | categorias_router |
| **Productos** | productos_router |
| **Dashboard** | dashboard_router |
| **Reportes** | reportes_router |

Las rutas exactas, los métodos HTTP, los parámetros y los esquemas de respuesta se pueden consultar en Swagger. Los prefijos de cada router dependen de su implementación.

## 🗄️ Base de datos
El sistema utiliza PostgreSQL para almacenar la información y SQLAlchemy como herramienta de acceso a los datos. Supabase proporciona el servicio de base de datos en el entorno desplegado.

## 🖼️ Almacenamiento de imágenes
Cloudinary se utiliza para configurar el servicio de almacenamiento y gestión de imágenes desde el backend.

## 🔐 Seguridad y autenticación
El backend incorpora un módulo de autenticación y utiliza JWT para gestionar los tokens de acceso, según la implementación del proyecto.

Las contraseñas deben almacenarse mediante hash y nunca exponerse en las respuestas de la API. Las rutas protegidas requieren las credenciales o el token correspondiente.

La cuenta de demostración debe tener únicamente los permisos necesarios para la evaluación.

## 🌍 Despliegue en Render
El backend puede desplegarse en Render con la siguiente configuración, siempre que la estructura del repositorio corresponda a app/main.py.

### Build Command ###
```bash
"pip install -r requirements.txt"
```

### Start Command ###
```bash
"uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

Las variables de entorno necesarias deben configurarse en Render antes de ejecutar el servicio.

## 🔗 Integración con el frontend ##
El frontend se encuentra desplegado en Vercel:

https://hd-grupo03-fronted.vercel.app/

El backend permite solicitudes CORS desde los siguientes orígenes configurados en main.py:

* http://localhost:5173
* https://hd-grupo03-fronted.vercel.app

## 📌 Estado del proyecto ##
Proyecto académico en desarrollo para la gestión integral de una cafetería.

Collins Café — Sistema web de gestión para cafeterías.