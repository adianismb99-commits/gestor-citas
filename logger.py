# logger.py
import json
import os
from datetime import datetime

LOG_FILE = "logs_actuales.json"

def guardar_logs(log_data):
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(log_data, f, indent=2)
    except:
        pass

def leer_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def agregar_paso(mensaje, tipo="info", paso_numero=None):
    logs = leer_logs()
    if not logs:
        logs = {
            "inicio": datetime.now().isoformat(),
            "pasos": [],
            "finalizado": False,
            "resultado": ""
        }
    
    paso = {
        "mensaje": mensaje,
        "tipo": tipo,
        "timestamp": datetime.now().isoformat(),
        "paso": paso_numero
    }
    logs["pasos"].append(paso)
    guardar_logs(logs)

def log_info(mensaje, paso=None):
    agregar_paso(mensaje, "info", paso)

def log_success(mensaje, paso=None):
    agregar_paso(mensaje, "success", paso)

def log_warning(mensaje, paso=None):
    agregar_paso(mensaje, "warning", paso)

def log_error(mensaje, paso=None):
    agregar_paso(mensaje, "error", paso)

def finalizar_logs(resultado):
    logs = leer_logs()
    if logs:
        logs["finalizado"] = True
        logs["resultado"] = resultado
        logs["fin"] = datetime.now().isoformat()
        guardar_logs(logs)

def limpiar_logs():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)