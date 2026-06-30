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

def aceptar_cookies(pagina):
    """Acepta el banner de cookies si aparece"""
    log("🍪 Buscando banner de cookies...")
    
    # Lista de selectores comunes para botones de cookies
    selectores = [
        "text=Aceptar",
        "button:has-text('Aceptar')",
        "text=Entendido",
        "button:has-text('Entendido')",
        "text=Acepto",
        "button:has-text('Acepto')",
        "#cookie-accept",
        ".cookie-accept",
        "button[class*='cookie']",
        "a[class*='cookie']",
        "button:has-text('Aceptar todas')",
        "button:has-text('Aceptar cookies')"
    ]
    
    for selector in selectores:
        try:
            boton = pagina.wait_for_selector(selector, timeout=2000)
            if boton:
                boton.click()
                log(f"   ✅ Cookies aceptadas con selector: {selector}")
                time.sleep(1)
                return True
        except:
            continue
    
    log("   ⚠️ No se encontró banner de cookies, continuando...")
    return False

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
            
            # ==========================================
            # ✅ ACEPTAR COOKIES ANTES DE SEGUIR
            # ==========================================
            aceptar_cookies(pagina)
            # ==========================================
            
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
            
            # ==========================================
            # ✅ ESPERAR NUEVA VENTANA O CAMBIO DE URL
            # ==========================================
            log("📊 Esperando nueva página o cambio de URL...")
            
            # Método 1: Esperar a que la URL cambie (si es la misma página)
            url_actual = pagina.url
            try:
                pagina.wait_for_url(lambda url: "citaconsular" in url, timeout=15000)
                log("   ✅ URL cambió a citaconsular")
            except:
                log("   ⚠️ La URL no cambió, intentando detectar nueva página...")
            
            # Método 2: Esperar a que haya más de 1 página
            time.sleep(3)
            try:
                paginas = navegador.contexts[0].pages
                log(f"   📊 Páginas actuales: {len(paginas)}")
                
                if len(paginas) > 1:
                    pagina = paginas[-1]
                    log("   ✅ Cambiado a la nueva ventana")
                else:
                    # Método 3: Reintentar clic con expect_page
                    log("   ⏳ Usando expect_page para detectar nueva ventana...")
                    try:
                        with navegador.context.expect_page(timeout=10000) as nueva_pagina_info:
                            # Reintentar clic en el enlace
                            enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=5000)
                            enlace.click()
                            log("   🔄 Reintentando clic en enlace RFX...")
                        pagina = nueva_pagina_info.value
                        log("   ✅ Nueva página detectada con expect_page")
                    except:
                        log("   ❌ No se detectó nueva página")
                        # Método 4: Navegación directa al href
                        try:
                            href = enlace.get_attribute('href')
                            if href:
                                log(f"   🔄 Navegando directamente a: {href}")
                                pagina.goto(href, timeout=30000)
                                log("   ✅ Navegación directa exitosa")
                        except Exception as e2:
                            log(f"   ❌ Error en navegación directa: {e2}")
            except Exception as e:
                log(f"   ⚠️ Error detectando páginas: {e}")
            
            # ==========================================
            # CONTINUAR CON EL PROCESO
            # ==========================================
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
                    try:
                        continuar = pagina.wait_for_selector("button:has-text('Continuar')", timeout=10000)
                        continuar.click()
                        log("   ✅ Click en Continuar (genérico)")
                    except:
                        log("   ❌ No se encontró el botón Continuar en ninguna forma")
            
            time.sleep(3)
            
            # Buscar horarios disponibles
            log("📌 Buscando horarios disponibles...")
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/9:[0-9]{2}/")
            
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
            else:
                log("   ⚠️ No se encontró campo de pasaporte")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada")
            elif len(inputs) >= 2:
                inputs[1].fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada (como texto)")
            else:
                log("   ⚠️ No se encontró campo de contraseña")
            
            # Click en Confirmar
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
            
            # Verificar confirmación
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