import time
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright

# ========================================
# IMPORTAR LOGGER
# ========================================
try:
    from logger import log_info, log_success, log_warning, log_error, finalizar_logs, limpiar_logs
    LOGGER_OK = True
    print("✅ Logger importado correctamente")
except Exception as e:
    LOGGER_OK = False
    print(f"⚠️ Logger no disponible: {e}")

def log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")
    sys.stdout.flush()

def capturar(pagina, nombre):
    try:
        archivo = f"static/{nombre}.png"
        os.makedirs("static", exist_ok=True)
        pagina.screenshot(path=archivo)
        log(f"📸 Captura: {archivo}")
        return archivo
    except:
        return None

def esperar_y_clickear(pagina, selector, nombre="elemento", timeout=15000):
    log(f"⏳ Esperando: {nombre}...")
    try:
        pagina.wait_for_selector(selector, timeout=timeout)
        pagina.click(selector)
        log(f"✅ Click: {nombre}")
        return True
    except Exception as e:
        log(f"❌ No se encontró: {nombre} - {e}")
        return False

def reservar_cita(cliente):
    log(f"🚀 Iniciando reserva para {cliente['nombre']}")
    if LOGGER_OK:
        log_info(f"🚀 Iniciando reserva para {cliente['nombre']}")
        limpiar_logs()
    
    resultado = {
        "exito": False,
        "motivo": "",
        "captura": None
    }
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--blink-settings=imagesEnabled=false',
                '--memory-pressure-off',
                '--max_old_space_size=128'
            ]
        )
        pagina = navegador.new_page()
        pagina.set_default_timeout(15000)
        
        try:
            # ============================================================
            # PASO 1: CARGAR PÁGINA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 1: Cargando página...", 1)
            
            url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            pagina.goto(url, timeout=30000)
            log("⏳ Cargando página...")
            time.sleep(3)
            
            # Verificar Cloudflare
            contenido = pagina.content()
            titulo = pagina.title()
            if "cf-browser-verification" in contenido or "Just a moment" in titulo:
                log("⚠️ Cloudflare detectado, esperando 3 segundos...")
                time.sleep(3)
                capturar(pagina, "cloudflare_detectado")
            
            try:
                pagina.wait_for_selector("text=Servicios consulares", timeout=10000)
                log("✅ Página cargada")
                if LOGGER_OK:
                    log_success("✅ Página cargada", 1)
            except:
                log("⚠️ No se encontró texto, continuando...")
                capturar(pagina, "error_no_texto")
            
            # ============================================================
            # PASO 2: COOKIES
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 2: Cookies...", 2)
            
            try:
                pagina.click("input[value='Aceptar']")
                log("✅ Cookies aceptadas")
                if LOGGER_OK:
                    log_success("✅ Cookies aceptadas", 2)
            except:
                try:
                    pagina.click("button:has-text('Aceptar')")
                    log("✅ Cookies aceptadas")
                except:
                    log("⚠️ No se encontraron cookies")
            
            # ============================================================
            # PASO 3: RFX
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 3: RFX...", 3)
            
            enlace_href = None
            
            try:
                pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=15000)
                enlace_href = pagina.get_attribute("text=Reservar cita de visados RFX", "href")
                pagina.click("text=Reservar cita de visados RFX")
                log("✅ RFX encontrado (texto exacto)")
                if LOGGER_OK:
                    log_success("✅ RFX encontrado", 3)
            except:
                try:
                    pagina.wait_for_selector("a[href*='citaconsular.es']", timeout=15000)
                    enlace_href = pagina.get_attribute("a[href*='citaconsular.es']", "href")
                    pagina.click("a[href*='citaconsular.es']")
                    log("✅ RFX encontrado (por href)")
                    if LOGGER_OK:
                        log_success("✅ RFX encontrado (por href)", 3)
                except:
                    log("❌ No se encontró RFX")
                    resultado["motivo"] = "no_rfx"
                    capturar(pagina, "error_no_rfx")
                    navegador.close()
                    return resultado
            
            log(f"📍 URL del enlace RFX: {enlace_href}")
            
            # ============================================================
            # PASO 4: NUEVA PÁGINA - TODOS LOS MÉTODOS POSIBLES
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 4: Intentando detectar nueva página...", 4)
            
            log("=" * 50)
            log("🔍 MÉTODO 1: navegador.context.pages")
            log("=" * 50)
            
            # Esperar un momento
            time.sleep(3)
            
            # MÉTODO 1: Obtener todas las páginas del contexto
            try:
                paginas = navegador.context.pages
                log(f"   📄 Páginas en contexto: {len(paginas)}")
                for i, p in enumerate(paginas):
                    log(f"      {i+1}. URL: {p.url}")
                
                if len(paginas) > 1:
                    pagina = paginas[-1]
                    log("✅ Cambiado a la nueva página (Método 1)")
                    if LOGGER_OK:
                        log_success("✅ Nueva página detectada (context.pages)", 4)
                else:
                    log("⚠️ Solo hay 1 página en el contexto")
            except Exception as e:
                log(f"❌ Error en Método 1: {e}")
            
            # MÉTODO 2: Esperar a que la URL cambie
            log("=" * 50)
            log("🔍 MÉTODO 2: Esperar cambio de URL")
            log("=" * 50)
            
            try:
                pagina.wait_for_url(lambda url: "citaconsular.es" in url, timeout=5000)
                log(f"✅ URL cambió a: {pagina.url}")
                if LOGGER_OK:
                    log_success("✅ URL cambió a citaconsular.es", 4)
            except:
                log("⚠️ La URL no cambió en 5 segundos")
                log(f"   URL actual: {pagina.url}")
            
            # MÉTODO 3: Usar expect_page() para capturar la nueva página
            log("=" * 50)
            log("🔍 MÉTODO 3: expect_page()")
            log("=" * 50)
            
            try:
                # Crear un nuevo contexto para aislar la nueva página
                with navegador.context.expect_page() as nueva_pagina_info:
                    # Reintentar el clic en el enlace RFX
                    try:
                        pagina.click("text=Reservar cita de visados RFX")
                    except:
                        pagina.click("a[href*='citaconsular.es']")
                    log("   🔄 Reintentando click en RFX...")
                
                nueva_pagina = nueva_pagina_info.value
                log(f"✅ Nueva página capturada con expect_page: {nueva_pagina.url}")
                pagina = nueva_pagina
                if LOGGER_OK:
                    log_success("✅ Nueva página detectada (expect_page)", 4)
            except Exception as e:
                log(f"❌ Error en Método 3: {e}")
            
            # MÉTODO 4: Navegar directamente al href
            log("=" * 50)
            log("🔍 MÉTODO 4: Navegación directa al href")
            log("=" * 50)
            
            if enlace_href and "citaconsular.es" not in pagina.url:
                try:
                    log(f"   Navegando a: {enlace_href}")
                    pagina.goto(enlace_href, timeout=30000)
                    log(f"✅ Navegación directa exitosa: {pagina.url}")
                    if LOGGER_OK:
                        log_success("✅ Navegación directa exitosa", 4)
                except Exception as e:
                    log(f"❌ Error en navegación directa: {e}")
            
            # MÉTODO 5: Buscar la URL de citaconsular en todas las páginas
            log("=" * 50)
            log("🔍 MÉTODO 5: Buscar en todas las páginas")
            log("=" * 50)
            
            try:
                paginas = navegador.context.pages
                for i, p in enumerate(paginas):
                    if "citaconsular.es" in p.url:
                        pagina = p
                        log(f"✅ Página de citaconsular encontrada en posición {i+1}: {p.url}")
                        if LOGGER_OK:
                            log_success("✅ Página de citaconsular encontrada", 4)
                        break
            except Exception as e:
                log(f"❌ Error en Método 5: {e}")
            
            # Verificar si estamos en citaconsular
            if "citaconsular.es" in pagina.url:
                log(f"✅ Página final: {pagina.url}")
                if LOGGER_OK:
                    log_success(f"✅ Página final: {pagina.url}", 4)
            else:
                log(f"⚠️ No estamos en citaconsular. URL actual: {pagina.url}")
                capturar(pagina, "error_url_no_citaconsular")
            
            capturar(pagina, "paso_4_citaconsular")
            
            # ============================================================
            # PASO 5: POPUP DE BIENVENIDA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 5: Aceptando popup de bienvenida...", 5)

            log("⏳ Esperando popup de bienvenida...")
            time.sleep(3)

            popup_aceptado = False
            for intento in range(5):
                log(f"   🔄 Intento {intento+1} de 5...")
                try:
                    pagina.click("text=Aceptar")
                    log("✅ Popup de bienvenida aceptado")
                    popup_aceptado = True
                    if LOGGER_OK:
                        log_success("✅ Popup de bienvenida aceptado", 5)
                    break
                except:
                    try:
                        pagina.click("button:has-text('Aceptar')")
                        log("✅ Popup de bienvenida aceptado")
                        popup_aceptado = True
                        break
                    except:
                        time.sleep(2)

            if not popup_aceptado:
                log("⚠️ No se encontró popup de bienvenida, continuando...")
                capturar(pagina, "error_no_popup")

            # ============================================================
            # PASO 6: CONTINUAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 6: Continuar...", 6)

            time.sleep(3)

            continuar_encontrado = False
            for intento in range(5):
                log(f"   🔄 Intentando Continuar {intento+1} de 5...")
                try:
                    pagina.click("text=Continuar")
                    log("✅ Click en Continuar")
                    continuar_encontrado = True
                    if LOGGER_OK:
                        log_success("✅ Continuar clickeado", 6)
                    break
                except:
                    try:
                        pagina.click("text=Continue")
                        log("✅ Click en Continue")
                        continuar_encontrado = True
                        break
                    except:
                        try:
                            pagina.click(".clsDivContinueButton")
                            log("✅ Click en Continuar (CSS)")
                            continuar_encontrado = True
                            break
                        except:
                            time.sleep(2)

            if not continuar_encontrado:
                log("⚠️ No se encontró Continuar")
                capturar(pagina, "error_no_continuar")

            # ============================================================
            # PASO 7: HORARIOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 7: Horarios...", 7)
            
            time.sleep(3)
            
            log("⏳ Esperando horarios...")
            timeout = 30
            horarios = []
            while timeout > 0:
                contenido = pagina.content()
                if "No hay horas disponibles" in contenido:
                    log("❌ No hay citas disponibles")
                    resultado["motivo"] = "no_hay_citas"
                    capturar(pagina, "no_hay_citas")
                    navegador.close()
                    if LOGGER_OK:
                        finalizar_logs("No hay citas disponibles")
                    return resultado
                
                horarios = pagina.query_selector_all(".clsDivDatetimeSlot")
                if len(horarios) > 0:
                    break
                time.sleep(1)
                timeout -= 1
            
            if len(horarios) > 0:
                log(f"✅ Horarios encontrados: {len(horarios)}")
                horarios[0].click()
                if LOGGER_OK:
                    log_success(f"✅ Horarios encontrados: {len(horarios)}", 7)
            else:
                log("❌ No hay horarios")
                resultado["motivo"] = "no_hay_horarios"
                capturar(pagina, "no_hay_horarios")
                navegador.close()
                if LOGGER_OK:
                    finalizar_logs("No hay horarios")
                return resultado
            
            # ============================================================
            # PASO 8: DATOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 8: Datos...", 8)
            
            time.sleep(2)
            
            # Pasaporte
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 2:
                inputs[1].fill(cliente["pasaporte"])
                log(f"✅ Pasaporte: {cliente['pasaporte']}")
                if LOGGER_OK:
                    log_success("✅ Pasaporte ingresado", 8)
            else:
                log("⚠️ No se encontró campo de pasaporte")
                capturar(pagina, "error_no_pasaporte")
            
            # Contraseña
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente["contrasena"])
                log("✅ Contraseña ingresada")
                if LOGGER_OK:
                    log_success("✅ Contraseña ingresada", 8)
            else:
                log("⚠️ No se encontró campo de contraseña")
                capturar(pagina, "error_no_password")
            
            # ============================================================
            # PASO 9: CONFIRMAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 9: Confirmar...", 9)
            
            try:
                pagina.click("text=Confirmar")
                log("✅ Click en Confirmar")
                if LOGGER_OK:
                    log_success("✅ Confirmar clickeado", 9)
            except:
                try:
                    pagina.click("button:has-text('Confirmar')")
                    log("✅ Click en Confirmar (button)")
                except:
                    log("⚠️ No se encontró Confirmar")
                    capturar(pagina, "error_no_confirmar")
            
            time.sleep(2)
            
            # ============================================================
            # PASO 10: RESULTADO
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 10: Resultado...", 10)
            
            contenido = pagina.content()
            if "Su reserva se ha realizado con éxito" in contenido:
                log("🎉 CITA CONFIRMADA!")
                resultado["exito"] = True
                resultado["motivo"] = "cita_confirmada"
                capturar(pagina, "cita_confirmada")
                if LOGGER_OK:
                    log_success("🎉 CITA CONFIRMADA!", 10)
                    finalizar_logs("¡CITA CONFIRMADA!")
            else:
                log("❌ No se confirmó")
                resultado["motivo"] = "no_confirmacion"
                capturar(pagina, "no_confirmacion")
                if LOGGER_OK:
                    log_error("❌ No se confirmó", 10)
                    finalizar_logs("No se confirmó la cita")
            
            navegador.close()
            return resultado
            
        except Exception as e:
            log(f"❌ Error general: {e}")
            resultado["motivo"] = f"error: {str(e)[:100]}"
            try:
                capturar(pagina, "error_general")
            except:
                pass
            navegador.close()
            if LOGGER_OK:
                finalizar_logs(f"Error: {str(e)[:100]}")
            return resultado

def reservar_citas_para_usuario(usuario_id):
    log(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    if LOGGER_OK:
        log_info(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    
    from app import app
    from models import db, Cliente
    
    with app.app_context():
        clientes = Cliente.query.filter_by(
            usuario_id=usuario_id,
            cita_reservada=False
        ).all()
        
        if not clientes:
            log("❌ No hay clientes pendientes")
            if LOGGER_OK:
                log_warning("❌ No hay clientes pendientes")
            return []
        
        log(f"📋 Clientes a procesar: {len(clientes)}")
        if LOGGER_OK:
            log_info(f"📋 Clientes a procesar: {len(clientes)}")
        
        resultados = []
        for cliente in clientes:
            log(f"\n🔄 Procesando: {cliente.nombre}")
            if LOGGER_OK:
                log_info(f"🔄 Procesando: {cliente.nombre}")
            
            cliente_dict = {
                "nombre": cliente.nombre,
                "pasaporte": cliente.pasaporte,
                "contrasena": cliente.contrasena_cita
            }
            resultado = reservar_cita(cliente_dict)
            
            if resultado["exito"]:
                cliente.cita_reservada = True
                cliente.fecha_cita = datetime.now()
                cliente.comprobante = resultado.get("captura", "")
                db.session.commit()
                log(f"✅ {cliente.nombre} - CITA RESERVADA")
                if LOGGER_OK:
                    log_success(f"✅ {cliente.nombre} - CITA RESERVADA")
            else:
                log(f"❌ {cliente.nombre} - {resultado['motivo']}")
                if LOGGER_OK:
                    log_error(f"❌ {cliente.nombre} - {resultado['motivo']}")
            
            resultados.append(resultado)
            time.sleep(5)
        
        log("\n🏁 Proceso completado")
        if LOGGER_OK:
            log_success("🏁 Proceso completado")
        return resultados

if __name__ == "__main__":
    cliente = {
        "nombre": "Prueba Test",
        "pasaporte": "N123456",
        "contrasena": "tu_contraseña_real"
    }
    reservar_cita(cliente)