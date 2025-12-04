SPOTREND 🎧🔥
Aplicación web para buscar artistas y canciones de Spotify, ver su información y experimentar con análisis básicos.
Versión en producción:
https://spotrend.onrender.com


---

🌐 TECNOLOGÍAS USADAS

🐍 Python 3.12

⚡ FastAPI

🎵 Spotify Web API

🎨 HTML + CSS + Bootstrap + Jinja2

🗄️ SQLite + SQLModel

🚀 Render (deploy)



---

💻 INSTALACIÓN EN LOCAL

1️⃣ Clonar el repositorio
git clone <URL-DE-TU-REPO>
cd SPOTREND

2️⃣ Crear el entorno virtual

En Git Bash (Windows):
python -m venv .venv
source .venv/Scripts/activate

En PowerShell:
.venv\Scripts\Activate.ps1

3️⃣ Instalar dependencias
pip install -r requirements.txt

Si no tienes ese archivo:
pip freeze > requirements.txt

4️⃣ Configurar las variables de entorno de Spotify
(Es obligatorio para que funcione la API)

Necesitas:
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET

En Git Bash:
export SPOTIFY_CLIENT_ID="tu_id"
export SPOTIFY_CLIENT_SECRET="tu_secret"

En PowerShell:
setx SPOTIFY_CLIENT_ID "tu_id"
setx SPOTIFY_CLIENT_SECRET "tu_secret"

(Después de setx toca reiniciar la terminal.)

5️⃣ Ejecutar el servidor
uvicorn main:app --reload

Luego abrir en el navegador:
http://localhost:8000


---

🚀 DESPLIEGUE EN RENDER

La versión en producción es:
https://spotrend.onrender.com

Para desplegar tú mismo:

Crear un nuevo Web Service en Render

Seleccionar ambiente: Python

Agregar las variables de entorno:
• SPOTIFY_CLIENT_ID
• SPOTIFY_CLIENT_SECRET

Comando de inicio:
uvicorn main:app --host 0.0.0.0 --port 10000


Render puede tardar un poco porque los servicios gratis “duermen”, es normal 😴⚡


---

📌 NOTAS IMPORTANTES

La aplicación pide un token a Spotify automáticamente con tu ID y Secret.

Si Render tarda en cargar, es por el “cold start” del plan gratuito.
