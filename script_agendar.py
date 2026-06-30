import os
import time
from datetime import datetime
from models import db, Cliente

from playwright.sync_api import sync_playwright

def reservar_cita_individual(cliente):
    """Reserva una cita para un cliente individual usando Playwright en modo headless"""
    
    print(f"📌 Iniciando reserva para {cliente.nombre}...")
    
    with sync_playwright() as p:
        # Lanzar Chromium en modo headless (sin interfaz gráfica)
        navegador = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pagina = navegador.new_page()
        
        try:
            print(f"📌 Entrando a la página para {cliente.nombre}...")
            url_visado = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            
            pagina.goto(url_visado, timeout=60000)
            pagina.wait_for_load_state("networkidle", timeout=60000)
            
            print("   ✅ Página cargada")
            
            # Buscar el enlace RFX
            print("📌 Buscando enlace 'Reservar cita de visados RFX'...")
            
            try:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=30000)
                print("   ✅ Enlace encontrado")
                enlace.click()
                print("   ✅ Click en enlace RFX")
            except:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados", timeout=30000)
                enlace.click()
                print("   ✅ Click en enlace por texto parcial")
            
            # Esperar a que se abra la nueva ventana
            time.sleep(5)
            
            # Obtener todas las páginas (ventanas) - CORREGIDO
            paginas = navegador.pages  # <--- CAMBIO CLAVE
            if len(paginas) > 1:
                pagina = paginas[-1]  # Cambiar a la última página abierta
                print("   ✅ Cambiado a la nueva ventana")
            
            # Esperar a que cargue la nueva página
            pagina.wait_for_load_state("networkidle", timeout=60000)
            
            # Buscar y hacer clic en "Continuar"
            print("📌 Buscando botón Continuar...")
            try:
                continuar = pagina.wait_for_selector("text=Continuar", timeout=10000)
                continuar.click()
                print("   ✅ Click en Continuar")
            except:
                continuar = pagina.wait_for_selector("text=Continue", timeout=10000)
                continuar.click()
                print("   ✅ Click en Continue")
            
            time.sleep(3)
            
            # Buscar horarios disponibles
            print("📌 Buscando horarios disponibles...")
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            
            if len(horarios) == 0:
                print("❌ No hay citas disponibles")
                cliente.cita_reservada = False
                db.session.commit()
                navegador.close()
                return False, "No hay citas disponibles"
            
            print(f"✅ Horarios encontrados: {len(horarios)}")
            horarios[0].click()
            print("   ✅ Horario seleccionado")
            
            time.sleep(2)
            
            # Rellenar pasaporte y contraseña
            print("📌 Rellenando datos...")
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 1:
                inputs[0].fill(cliente.pasaporte)
                print(f"   ✅ Pasaporte: {cliente.pasaporte}")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente.contrasena_cita)
                print("   ✅ Contraseña ingresada")
            elif len(inputs) >= 2:
                inputs[1].fill(cliente.contrasena_cita)
                print("   ✅ Contraseña ingresada (como texto)")
            
            # Confirmar
            try:
                confirmar = pagina.wait_for_selector("text=Confirmar", timeout=5000)
                confirmar.click()
                print("   ✅ Click en Confirmar")
            except:
                pass
            
            time.sleep(3)
            
            # Verificar confirmación
            print("📌 Verificando confirmación...")
            try:
                pagina.wait_for_selector("text=Su reserva se ha realizado con éxito", timeout=10000)
                print("✅ Confirmación encontrada")
                
                # Guardar comprobante
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                archivo = f"comprobantes/cita_{cliente.pasaporte}_{fecha}.png"
                os.makedirs("comprobantes", exist_ok=True)
                pagina.screenshot(path=archivo)
                
                cliente.cita_reservada = True
                cliente.fecha_cita = datetime.now()
                cliente.comprobante = archivo
                db.session.commit()
                
                print(f"🎉 ¡CITA CONFIRMADA para {cliente.nombre}!")
                print(f"📸 Captura guardada: {archivo}")
                
                navegador.close()
                return True, "Cita reservada exitosamente"
            except:
                print("❌ No se encontró confirmación")
                navegador.close()
                return False, "No se encontró confirmación"
                
        except Exception as e:
            print(f"❌ Error con {cliente.nombre}: {e}")
            try:
                pagina.screenshot(path=f"error_{cliente.pasaporte}.png")
            except:
                pass
            try:
                cliente.cita_reservada = False
                db.session.commit()
            except:
                pass
            navegador.close()
            return False, str(e)

def reservar_citas_para_usuario(usuario_id):
    """Reserva todas las citas pendientes de un usuario"""
    print(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    
    from app import app
    
    with app.app_context():
        clientes = Cliente.query.filter_by(
            usuario_id=usuario_id,
            cita_reservada=False
        ).all()
        
        if not clientes:
            print("❌ No hay clientes pendientes")
            return []
        
        print(f"📋 Clientes a procesar: {len(clientes)}")
        resultados = []
        
        for cliente in clientes:
            print(f"\n🔄 Procesando: {cliente.nombre}")
            exito, mensaje = reservar_cita_individual(cliente)
            resultados.append({
                'cliente': cliente.nombre,
                'exito': exito,
                'mensaje': mensaje
            })
            time.sleep(5)
        
        print("\n🏁 Proceso completado")
        return resultados