from app.services.download_service import DownloadService
from app.services.usage_service import UsageService

# Instancias únicas compartidas entre la web (Flask) y el bot de Telegram.
# Antes cada módulo creaba las suyas propias, duplicando la cola/el hilo
# trabajador y las conexiones a la base de límites diarios.
download_service = DownloadService()
usage_service = UsageService()
