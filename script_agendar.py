import os
import sys
import time
from datetime import datetime
from models import db, Cliente

from playwright.sync_api import sync_playwright

def log(mensaje):
    """Función para imprimir y forzar el flush de los logs"""
    print(mensaje)
    sys.stdout.flush()

def reservar_cita_individual(cliente):
    """Reserva una cita para un cliente individual usando Playwright en modo headless"""
    
    log(f"📌 Iniciando reserva para {cliente.nombre}...")
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pagina = navegador.new_page()
        
        try:
            log(f"📌 Entrando a la página para {cliente.nombre}...")
            url_visado = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            
            pagina.goto(url_visado, timeout=60000)
            pagina.wait_for_load_state("networkidle", timeout=60000)
            
            log("   ✅ Página cargada")
            
            # Buscar el enlace RFX
            log("📌 Buscando enlace 'Reservar cita de visados RFX'...")
            
            try:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=30000)
                log("   ✅ Enlace encontrado")
                enlace.click()
                log("   ✅ Click en enlace RFX")
            except:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados", timeout=30000)
                enlace.click()
                log("   ✅ Click en enlace por texto parcial")
            
            # Esperar a que se abra la nueva ventana
            time.sleep(5)
            
            # Obtener todas las páginas (ventanas) de forma compatible
            log("📊 Obteniendo páginas del navegador...")
            try:
                paginas = navegador.context.pages
                log(f"   ✅ Páginas obtenidas con context.pages: {len(paginas)}")
            except AttributeError:
                try:
                    paginas = navegador.contexts[0].pages
                    log(f"   ✅ Páginas obtenidas con contexts[0].pages: {len(paginas)}")
                except:
                    log("   ⚠️ Usando fallback manual...")
                    paginas = []
                    for context in navegador.contexts:
                        paginas.extend(context.pages)
                    log(f"   ✅ Páginas obtenidas manualmente: {len(paginas)}")

            if len(paginas) > 1:
                pagina = paginas[-1]
                log("   ✅ Cambiado a la nueva ventana")
            else:
                log("   ⚠️ No se detectó nueva ventana, continuando en la misma...")
            
            pagina.wait_for_load_state("networkidle", timeout=60000)
            
            # Buscar y hacer clic en "Continuar"
            log("📌 Buscando botón Continuar...")
            try:
                continuar = pagina.wait_for_selector("text=Continuar", timeout=10000)
                continuar.click()
                log("   ✅ Click en Continuar")
            except:
                try:
                    continuar = pagina.wait_for_selector("text=Continue", timeout=10000)
                    continuar.click()
                    log("   ✅ Click en Continue")
                except:
                    log("   ⚠️ No se encontró el botón Continuar, intentando con selector genérico...")
                    continuar = pagina.wait_for_selector("button:has-text('Continuar')", timeout=10000)
                    continuar.click()
                    log("   ✅ Click en Continuar (genérico)")
            
            time.sleep(3)
            
            # Buscar horarios disponibles
            log("📌 Buscando horarios disponibles...")
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            
            if len(horarios) == 0:
                log("❌ No hay citas disponibles")
                cliente.cita_reservada = False
                db.session.commit()
                navegador.close()
                return False, "No hay citas disponibles"
            
            log(f"✅ Horarios encontrados: {len(horarios)}")
            horarios[0].click()
            log("   ✅ Horario seleccionado")
            
            time.sleep(2)
            
            # Rellenar pasaporte y contraseña
            log("📌 Rellenando datos...")
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 1:
                inputs[0].fill(cliente.pasaporte)
                log(f"   ✅ Pasaporte: {cliente.pasaporte}")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada")
            elif len(inputs) >= 2:
                inputs[1].fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada (como texto)")
            
            try:
                confirmar = pagina.wait_for_selector("text=Confirmar", timeout=5000)
                confirmar.click()
                log("   ✅ Click en Confirmar")
            except:
                try:
                    confirmar = pagina.wait_for_selector("button:has-text('Confirmar')", timeout=5000)
                    confirmar.click()
                    log("   ✅ Click en Confirmar (genérico)")
                except:
                    log("   ⚠️ No se encontró el botón Confirmar")
            
            time.sleep(3)
            
            log("📌 Verificando confirmación...")
            try:
                pagina.wait_for_selector("text=Su reserva se ha realizado con éxito", timeout=10000)
                log("✅ Confirmación encontrada")
                
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                archivo = f"static/cita_{cliente.pasaporte}_{fecha}.png"
                os.makedirs("static", exist_ok=True)
                pagina.screenshot(path=archivo)
                
                cliente.cita_reservada = True
                cliente.fecha_cita = datetime.now()
                cliente.comprobante = archivo
                db.session.commit()
                
                log(f"🎉 ¡CITA CONFIRMADA para {cliente.nombre}!")
                log(f"📸 Captura guardada: {archivo}")
                
                navegador.close()
                return True, "Cita reservada exitosamente"
            except:
                log("❌ No se encontró confirmación")
                navegador.close()
                return False, "No se encontró confirmación"
                
        except Exception as e:
            log(f"❌ Error con {cliente.nombre}: {e}")
            try:
                os.makedirs("static", exist_ok=True)
                archivo_error = f"static/error_{cliente.pasaporte}.png"
                pagina.screenshot(path=archivo_error)
                log(f"📸 Captura de error guardada: {archivo_error}")
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
    log(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    
    from app import app
    
    with app.app_context():
        clientes = Cliente.query.filter_by(
            usuario_id=usuario_id,
            cita_reservada=False
        ).all()
        
        if not clientes:
            log("❌ No hay clientes pendientes")
            return []
        
        log(f"📋 Clientes a procesar: {len(clientes)}")
        resultados = []
        
        for cliente in clientes:
            log(f"\n🔄 Procesando: {cliente.nombre}")
            exito, mensaje = reservar_cita_individual(cliente)
            resultados.append({
                'cliente': cliente.nombre,
                'exito': exito,
                'mensaje': mensaje
            })
            time.sleep(5)
        
        log("\n🏁 Proceso completado")
        return resultados