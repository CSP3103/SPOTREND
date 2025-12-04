🎧🔥 SPOTREND — Buscador y analizador de música con Spotify API

Aplicación web para buscar artistas y canciones desde Spotify, ver su información, compararlas y analizar tendencias.

📌 Versión en producción:
👉 https://spotrend.onrender.com

🚀 Tecnologías utilizadas
Tecnología	Uso
🐍 Python 3.12	Backend
⚡ FastAPI	API y servidor web
🎵 Spotify Web API	Fuente de datos musicales
🎨 HTML + CSS + Bootstrap + Jinja2	Frontend
🗄️ SQLite + SQLModel	Base de datos local
☁️ Render.com	Hosting en producción
🗂️ Estructura del proyecto
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

💻 Instalación en local
1️⃣ Clonar el repositorio
git clone <tu-repo>
cd SPOTREND

2️⃣ Crear entorno virtual
🔹 Git Bash (Windows)
python -m venv .venv
source .venv/Scripts/activate

🔹 PowerShell
.venv\Scripts\Activate.ps1

3️⃣ Instalar dependencias
pip install -r requirements.txt


Si no existe el archivo:

pip freeze > requirements.txt

4️⃣ Configurar variables de entorno de Spotify

(Obligatorio para usar la API)

Necesitas:

SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET

Git Bash
export SPOTIFY_CLIENT_ID="tu_id"
export SPOTIFY_CLIENT_SECRET="tu_secret"

PowerShell
setx SPOTIFY_CLIENT_ID "tu_id"
setx SPOTIFY_CLIENT_SECRET "tu_secret"


⚠️ Después de usar setx debes reiniciar la terminal.

5️⃣ Ejecutar el servidor
uvicorn main:app --reload


Luego abre:

👉 http://localhost:8000

🚀 Despliegue en Render

📌 Versión desplegada:
https://spotrend.onrender.com

Cómo desplegar tu copia:
Crear un nuevo Web Service en Render
Elegir Stack: Python
Agregar variables de entorno:
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
Colocar comando de inicio:
uvicorn main:app --host 0.0.0.0 --port 10000

💡 Render puede tardar en despertar los servicios gratuitos — totalmente normal 😴⚡

📌 Notas importantes

✔ La app obtiene automáticamente un token de Spotify usando tu client ID y secret.
✔ El “cold start” de Render puede tardar unos segundos al cargar.
