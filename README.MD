<h1 align="center">🎧🔥 <b>SPOTREND — Buscador y analizador de música con Spotify API</b></h1>
<p align="center"> Aplicación web para buscar artistas y canciones desde Spotify, ver su información, compararlas y analizar tendencias. </p>
<h2 align="center">📌 Versión en producción</h2>
<p align="center"> 👉 <a href="https://spotrend.onrender.com" target="_blank"><b>https://spotrend.onrender.com</b></a> </p>
<h2 align="center">🚀 Tecnologías utilizadas</h2>

Tecnología	Uso

🐍 Python 3.12	Backend

⚡ FastAPI	API y servidor web

🎵 Spotify Web API	Fuente de datos

🎨 HTML + CSS + Bootstrap + Jinja2	Frontend

🗄️ SQLite + SQLModel	Base de datos

☁️ Render.com	Hosting

<h2 align="center">🗂️ Estructura del proyecto</h2>
📁 routers/

 ├── analisis.py

 ├── artista.py

 ├── benchmark.py

 ├── cancion.py

 ├── comparacion_local.py

 ├── comparar_spotify.py

 ├── dashboard.py

 ├── eliminados.py

 ├── recomendaciones.py

 ├── spotify_auth.py

 └── spotify_data.py


📁 services/

 ├── analisis_service.py

 └── spotify_service.py

📁 templates/

 ├── analisis/

 ├── artistas/

 ├── benchmarks/

 ├── canciones/

 ├── comparacion/

 ├── comparacion_spotify/

 ├── eliminados/

 ├── recomendaciones/

 ├── spotify/

 ├── base.html

 ├── dashboard.html

 ├── error.html

 └── index.html

.gitignore  
README.md  
database.py  
main.py  
models.py  
requirements.txt  
supabase_service.py

<h2 align="center">💻 Instalación en local</h2>
1️⃣ Clonar el repositorio
git clone <tu-repo>
cd SPOTREND

2️⃣ Crear entorno virtual

🔹 Git Bash (Windows):

python -m venv .venv
source .venv/Scripts/activate


🔹 PowerShell:

.venv\Scripts\Activate.ps1

3️⃣ Instalar dependencias
pip install -r requirements.txt


Si no existe el archivo:

pip freeze > requirements.txt

4️⃣ Configurar variables de entorno de Spotify

⚠️ Obligatorio para usar la API

Necesitas:

SPOTIFY_CLIENT_ID  
SPOTIFY_CLIENT_SECRET


🔹 Git Bash:

export SPOTIFY_CLIENT_ID="tu_id"
export SPOTIFY_CLIENT_SECRET="tu_secret"


🔹 PowerShell:

setx SPOTIFY_CLIENT_ID "tu_id"
setx SPOTIFY_CLIENT_SECRET "tu_secret"


⚠️ Después de setx debes reiniciar la terminal.

5️⃣ Ejecutar el servidor
uvicorn main:app --reload


Abrir en el navegador:

👉 http://localhost:8000

<h2 align="center">🚀 Despliegue en Render</h2>

📌 Versión desplegada:

👉 https://spotrend.onrender.com

Cómo desplegar tu copia

Crear un nuevo Web Service en Render

Elegir stack: Python

Agregar variables de entorno:

SPOTIFY_CLIENT_ID

SPOTIFY_CLIENT_SECRET

Definir comando de inicio:

uvicorn main:app --host 0.0.0.0 --port 10000


💡 Render puede tardar unos segundos al iniciar proyectos gratuitos — es normal 😴⚡

<h2 align="center">📌 Notas importantes</h2>

✔ La app obtiene automáticamente un token de Spotify usando tu Client ID y Client Secret.
✔ El arranque puede ser lento en Render por el cold start del plan gratuito.
