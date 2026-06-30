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

def capturar_pantalla(pagina, nombre, cliente_pasaporte=""):
    """Guarda una captura de pantalla en la carpeta static/"""
    try:
        os.makedirs("static", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"static/paso_{nombre}_{cliente_pasaporte}_{timestamp}.png"
        pagina.screenshot(path=archivo, full_page=True)
        log(f"   📸 Captura guardada: {archivo}")
        return archivo
    except Exception as e:
        log(f"   ⚠️ Error al guardar captura: {e}")
        return None

def aceptar_cookies(pagina, cliente_pasaporte=""):
    """Acepta el banner de cookies si aparece"""
    log("🍪 Buscando banner de cookies...")
    
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
                capturar_pantalla(pagina, "01_cookies_aceptadas", cliente_pasaporte)
                return True
        except:
            continue
    
    log("   ⚠️ No se encontró banner de cookies, continuando...")
    capturar_pantalla(pagina, "01_sin_cookies", cliente_pasaporte)
    return False

def reservar_cita_individual(cliente):
    """Reserva una cita para un cliente individual usando Playwright en modo headless"""
    
    log(f"📌 Iniciando reserva para {cliente.nombre}...")
    pasaporte = cliente.pasaporte
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pagina = navegador.new_page()
        
        try:
            # ==========================================
            # PASO 1: Cargar página principal
            # ==========================================
            log(f"📌 Entrando a la página para {cliente.nombre}...")
            url_visado = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            
            pagina.goto(url_visado, timeout=60000)
            pagina.wait_for_load_state("networkidle", timeout=60000)
            
            log("   ✅ Página cargada")
            capturar_pantalla(pagina, "02_pagina_principal_cargada", pasaporte)
            
            # ==========================================
            # PASO 2: Aceptar cookies
            # ==========================================
            aceptar_cookies(pagina, pasaporte)
            
            # ==========================================
            # PASO 3: Buscar y hacer clic en RFX
            # ==========================================
            log("📌 Buscando enlace 'Reservar cita de visados RFX'...")
            
            try:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=30000)
                log("   ✅ Enlace encontrado")
                capturar_pantalla(pagina, "03_enlace_rfx_encontrado", pasaporte)
                enlace.click()
                log("   ✅ Click en enlace RFX")
                capturar_pantalla(pagina, "04_click_rfx", pasaporte)
            except:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados", timeout=30000)
                log("   ✅ Enlace encontrado (texto parcial)")
                capturar_pantalla(pagina, "03_enlace_rfx_parcial", pasaporte)
                enlace.click()
                log("   ✅ Click en enlace por texto parcial")
                capturar_pantalla(pagina, "04_click_rfx_parcial", pasaporte)
            
            # ==========================================
            # PASO 4: Esperar nueva ventana
            # ==========================================
            log("📊 Esperando nueva página o cambio de URL...")
            
            try:
                pagina.wait_for_url(lambda url: "citaconsular" in url, timeout=15000)
                log("   ✅ URL cambió a citaconsular")
                capturar_pantalla(pagina, "05_url_cambio", pasaporte)
            except:
                log("   ⚠️ La URL no cambió, intentando detectar nueva página...")
                capturar_pantalla(pagina, "05_url_no_cambio", pasaporte)
            
            time.sleep(3)
            
            try:
                paginas = navegador.contexts[0].pages
                log(f"   📊 Páginas actuales: {len(paginas)}")
                capturar_pantalla(pagina, "06_paginas_actuales", pasaporte)
                
                if len(paginas) > 1:
                    pagina = paginas[-1]
                    log("   ✅ Cambiado a la nueva ventana")
                    capturar_pantalla(pagina, "07_nueva_ventana", pasaporte)
                    
                    # ==========================================
                    # PASO 5: Aceptar notificación de bienvenida
                    # ==========================================
                    log("📌 Buscando notificación de bienvenida...")
                    pagina.wait_for_load_state("networkidle", timeout=30000)
                    time.sleep(2)
                    capturar_pantalla(pagina, "08_ventana_bienvenida", pasaporte)
                    
                    boton_aceptado = False
                    selectores_bienvenida = [
                        "text=Aceptar",
                        "button:has-text('Aceptar')",
                        "text=Entendido",
                        "button:has-text('Entendido')",
                        "text=Bienvenido",
                        "button:has-text('Bienvenido')",
                        "text=Welcome",
                        "button:has-text('Welcome')",
                        "button[class*='welcome']",
                        "button[class*='aceptar']"
                    ]
                    
                    for selector in selectores_bienvenida:
                        try:
                            boton = pagina.wait_for_selector(selector, timeout=3000)
                            if boton:
                                boton.click()
                                log(f"   ✅ Click en Aceptar (bienvenida) con selector: {selector}")
                                boton_aceptado = True
                                time.sleep(2)
                                capturar_pantalla(pagina, "09_bienvenida_aceptada", pasaporte)
                                break
                        except:
                            continue
                    
                    if not boton_aceptado:
                        log("   ⚠️ No se encontró notificación de bienvenida, continuando...")
                        capturar_pantalla(pagina, "09_sin_bienvenida", pasaporte)
                    
                    # ==========================================
                    # PASO 6: Buscar "Continuar"
                    # ==========================================
                    log("📌 Buscando botón Continuar...")
                    capturar_pantalla(pagina, "10_buscando_continuar", pasaporte)
                    
                    try:
                        continuar = pagina.wait_for_selector("text=Continuar", timeout=10000)
                        continuar.click()
                        log("   ✅ Click en Continuar")
                        capturar_pantalla(pagina, "11_continuar_click", pasaporte)
                    except:
                        try:
                            continuar = pagina.wait_for_selector("text=Continue", timeout=10000)
                            continuar.click()
                            log("   ✅ Click en Continue")
                            capturar_pantalla(pagina, "11_continue_click", pasaporte)
                        except:
                            log("   ⚠️ No se encontró el botón Continuar, intentando con selector genérico...")
                            capturar_pantalla(pagina, "11_continuar_no_encontrado", pasaporte)
                            try:
                                continuar = pagina.wait_for_selector("button:has-text('Continuar')", timeout=10000)
                                continuar.click()
                                log("   ✅ Click en Continuar (genérico)")
                                capturar_pantalla(pagina, "11_continuar_generico", pasaporte)
                            except:
                                log("   ❌ No se encontró el botón Continuar en ninguna forma")
                                capturar_pantalla(pagina, "11_error_continuar", pasaporte)
                else:
                    log("   ⚠️ No se detectó nueva ventana, continuando en la misma...")
                    capturar_pantalla(pagina, "07_sin_nueva_ventana", pasaporte)
                    
                    try:
                        with navegador.context.expect_page(timeout=10000) as nueva_pagina_info:
                            enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=5000)
                            enlace.click()
                            log("   🔄 Reintentando clic en enlace RFX...")
                        pagina = nueva_pagina_info.value
                        log("   ✅ Nueva página detectada con expect_page")
                        capturar_pantalla(pagina, "07_expect_page_exito", pasaporte)
                    except:
                        log("   ❌ No se detectó nueva página")
                        capturar_pantalla(pagina, "07_expect_page_error", pasaporte)
                        try:
                            href = enlace.get_attribute('href')
                            if href:
                                log(f"   🔄 Navegando directamente a: {href}")
                                pagina.goto(href, timeout=30000)
                                log("   ✅ Navegación directa exitosa")
                                capturar_pantalla(pagina, "07_navegacion_directa", pasaporte)
                        except Exception as e2:
                            log(f"   ❌ Error en navegación directa: {e2}")
                            capturar_pantalla(pagina, "07_error_navegacion_directa", pasaporte)
            except Exception as e:
                log(f"   ⚠️ Error detectando páginas: {e}")
                capturar_pantalla(pagina, "06_error_detectando_paginas", pasaporte)
            
            # ==========================================
            # PASO 7: Buscar horarios disponibles
            # ==========================================
            pagina.wait_for_load_state("networkidle", timeout=60000)
            capturar_pantalla(pagina, "12_buscando_horarios", pasaporte)
            
            log("📌 Buscando horarios disponibles...")
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/9:[0-9]{2}/")
            
            if len(horarios) == 0:
                log("❌ No hay citas disponibles")
                capturar_pantalla(pagina, "13_no_hay_citas", pasaporte)
                cliente.cita_reservada = False
                db.session.commit()
                navegador.close()
                return False, "No hay citas disponibles"
            
            log(f"✅ Horarios encontrados: {len(horarios)}")
            capturar_pantalla(pagina, "13_horarios_encontrados", pasaporte)
            horarios[0].click()
            log("   ✅ Horario seleccionado")
            capturar_pantalla(pagina, "14_horario_seleccionado", pasaporte)
            
            time.sleep(2)
            
            # ==========================================
            # PASO 8: Rellenar datos
            # ==========================================
            log("📌 Rellenando datos...")
            capturar_pantalla(pagina, "15_rellenando_datos", pasaporte)
            
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 1:
                inputs[0].fill(cliente.pasaporte)
                log(f"   ✅ Pasaporte: {cliente.pasaporte}")
                capturar_pantalla(pagina, "16_pasaporte_ingresado", pasaporte)
            else:
                log("   ⚠️ No se encontró campo de pasaporte")
                capturar_pantalla(pagina, "16_error_pasaporte", pasaporte)
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada")
                capturar_pantalla(pagina, "17_contrasena_ingresada", pasaporte)
            elif len(inputs) >= 2:
                inputs[1].fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada (como texto)")
                capturar_pantalla(pagina, "17_contrasena_texto", pasaporte)
            else:
                log("   ⚠️ No se encontró campo de contraseña")
                capturar_pantalla(pagina, "17_error_contrasena", pasaporte)
            
            # ==========================================
            # PASO 9: Click en Confirmar
            # ==========================================
            try:
                confirmar = pagina.wait_for_selector("text=Confirmar", timeout=5000)
                confirmar.click()
                log("   ✅ Click en Confirmar")
                capturar_pantalla(pagina, "18_confirmar_click", pasaporte)
            except:
                try:
                    confirmar = pagina.wait_for_selector("button:has-text('Confirmar')", timeout=5000)
                    confirmar.click()
                    log("   ✅ Click en Confirmar (genérico)")
                    capturar_pantalla(pagina, "18_confirmar_generico", pasaporte)
                except:
                    log("   ⚠️ No se encontró el botón Confirmar")
                    capturar_pantalla(pagina, "18_error_confirmar", pasaporte)
            
            time.sleep(3)
            
            # ==========================================
            # PASO 10: Verificar confirmación
            # ==========================================
            log("📌 Verificando confirmación...")
            capturar_pantalla(pagina, "19_verificando_confirmacion", pasaporte)
            
            try:
                pagina.wait_for_selector("text=Su reserva se ha realizado con éxito", timeout=10000)
                log("✅ Confirmación encontrada")
                
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                archivo = f"static/cita_{cliente.pasaporte}_{fecha}.png"
                os.makedirs("static", exist_ok=True)
                pagina.screenshot(path=archivo, full_page=True)
                
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
                capturar_pantalla(pagina, "19_error_confirmacion", pasaporte)
                navegador.close()
                return False, "No se encontró confirmación"
                
        except Exception as e:
            log(f"❌ Error con {cliente.nombre}: {e}")
            try:
                archivo_error = f"static/error_final_{cliente.pasaporte}.png"
                pagina.screenshot(path=archivo_error, full_page=True)
                log(f"📸 Captura de error final guardada: {archivo_error}")
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