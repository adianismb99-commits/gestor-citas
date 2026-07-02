import os
import sys
from app import app
from models import db, Usuario, Cliente
from script_agendar import reservar_citas_para_usuario

def main():
    print("🕒 Ejecutando tarea programada...")
    
    with app.app_context():
        usuarios = Usuario.query.all()
        print(f"📋 Usuarios encontrados: {len(usuarios)}")
        
        for usuario in usuarios:
            clientes_pendientes = Cliente.query.filter_by(
                usuario_id=usuario.id,
                cita_reservada=False
            ).count()
            
            if clientes_pendientes > 0:
                print(f"🔄 Procesando usuario: {usuario.username}")
                reservar_citas_para_usuario(usuario.id)
            else:
                print(f"⏭️ Usuario {usuario.username} sin clientes pendientes")
        
    print("✅ Tarea programada completada")

if __name__ == "__main__":
    main()