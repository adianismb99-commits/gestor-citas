# logger.py
import time
from datetime import datetime
from flask import session
import json
import os

LOG_FILE = "logs_actuales.json"

def iniciar_logs():
    """Inicia un nuevo registro de logs"""
    log_data = {
        "inicio": datetime.now().isoformat(),
        "pasos": [],
        "finalizado": False,
        "resultado": ""
    }
    guardar_logs(log_data)
    return log_data

def guardar_logs(log_data):
    """Guarda los logs en un archivo JSON"""
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

def leer_logs():
    """Lee los logs actuales"""
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def agregar_paso(mensaje, tipo="info", paso_numero=None):
    """Agrega un paso a los logs"""
    logs = leer_logs()
    if not logs:
        logs = iniciar_logs()
    
    paso = {
        "mensaje": mensaje,
        "tipo": tipo,  # info, success, warning, error
        "timestamp": datetime.now().isoformat(),
        "paso": paso_numero
    }
    logs["pasos"].append(paso)
    guardar_logs(logs)
    
    # También imprimir en consola para Render
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {mensaje}")

def log_info(mensaje, paso=None):
    agregar_paso(mensaje, "info", paso)

def log_success(mensaje, paso=None):
    agregar_paso(mensaje, "success", paso)

def log_warning(mensaje, paso=None):
    agregar_paso(mensaje, "warning", paso)

def log_error(mensaje, paso=None):
    agregar_paso(mensaje, "error", paso)

def finalizar_logs(resultado):
    """Marca los logs como finalizados"""
    logs = leer_logs()
    if logs:
        logs["finalizado"] = True
        logs["resultado"] = resultado
        logs["fin"] = datetime.now().isoformat()
        guardar_logs(logs)

def limpiar_logs():
    """Limpia los logs antiguos"""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)