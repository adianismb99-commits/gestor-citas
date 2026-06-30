# run_agendamiento.py
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(__file__))

from app import app
from models import db, Usuario, Cliente
from script_agendar import reservar_citas_para_usuario
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--usuario_id', type=int, required=True, help='ID del usuario')
    args = parser.parse_args()
    
    with app.app_context():
        print(f"🚀 Iniciando agendamiento para usuario {args.usuario_id}")
        reservar_citas_para_usuario(args.usuario_id)
        print("🏁 Proceso completado")

if __name__ == "__main__":
    main()