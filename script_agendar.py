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
    except Exception as e:
        log(f"⚠️ Error al capturar {nombre}: {e}")
        return None

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
    
    URL_MINISTERIO = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=False,  # TEMPORAL: para debug
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--window-size=1920,1080'
            ]
        )
        
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        pagina = contexto.new_page()
        
        pagina.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        pagina.set_default_timeout(30000)
        
        try:
            # ============================================================
            # PASO 1: CARGAR PÁGINA DEL MINISTERIO
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 1: Cargando página del Ministerio...", 1)
            
            log(f"🔄 Cargando página del Ministerio...")
            pagina.goto(URL_MINISTERIO, timeout=30000, wait_until="networkidle")
            log("✅ Página cargada")
            time.sleep(3)
            capturar(pagina, "paso_1_ministerio")
            
            # ============================================================
            # PASO 2: ACEPTAR COOKIES
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 2: Aceptando cookies...", 2)
            
            try:
                pagina.click("input[value='Aceptar']")
                log("✅ Cookies aceptadas")
            except:
                try:
                    pagina.click("button:has-text('Aceptar')")
                    log("✅ Cookies aceptadas")
                except:
                    log("⚠️ No se encontraron cookies")
            
            # ============================================================
            # PASO 3: HACER CLIC EN RFX Y ESPERAR NUEVA PÁGINA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 3: Haciendo clic en RFX...", 3)
            
            enlace = pagina.query_selector("text=Reservar cita de visados RFX")
            if not enlace:
                enlace = pagina.query_selector("a[href*='citaconsular.es']")
            
            if not enlace:
                log("❌ No se encontró el enlace RFX")
                resultado["motivo"] = "no_rfx"
                capturar(pagina, "error_no_rfx")
                navegador.close()
                return resultado
            
            log("🔄 Haciendo clic en RFX...")
            with contexto.expect_page() as nueva_pagina_info:
                enlace.click()
            
            pagina = nueva_pagina_info.value
            log("✅ Nueva página abierta")
            pagina.wait_for_load_state("networkidle")
            time.sleep(3)
            capturar(pagina, "paso_3_citaconsular_inicial")
            
            # ============================================================
            # PASO 4: PASAR EL CAPTCHA DE CLOUDFLARE
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 4: Pasando captcha de Cloudflare...", 4)
            
            # Verificar si estamos en la página de captcha
            contenido = pagina.content()
            if "idCaptchaButton" in contenido or "Continue / Continuar" in contenido:
                log("🔐 CAPTCHA de Cloudflare detectado")
                capturar(pagina, "captcha_detectado")
                
                # Buscar y hacer clic en el botón
                try:
                    boton = pagina.query_selector("#idCaptchaButton")
                    if boton:
                        log("🔄 Haciendo clic en 'Continue / Continuar'...")
                        boton.click()
                        log("✅ Click en botón de captcha")
                        time.sleep(5)
                        
                        # Esperar redirección
                        pagina.wait_for_load_state("networkidle")
                        log("✅ Redirección completada")
                        capturar(pagina, "despues_captcha")
                    else:
                        log("⚠️ No se encontró el botón del captcha")
                except Exception as e:
                    log(f"❌ Error al hacer clic en captcha: {e}")
            else:
                log("ℹ️ No se detectó captcha, continuando...")
            
            # Verificar URL final
            if "citaconsular.es" in pagina.url:
                log(f"✅ En citaconsular.es: {pagina.url}")
                if LOGGER_OK:
                    log_success("✅ En citaconsular.es", 4)
            else:
                log(f"⚠️ URL final: {pagina.url}")
                capturar(pagina, "error_url_final")
            
            # ============================================================
            # PASO 5: POPUP DE BIENVENIDA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 5: Popup de bienvenida...", 5)

            popup_aceptado = False
            for intento in range(5):
                try:
                    aceptar = pagina.query_selector("text=Aceptar")
                    if aceptar:
                        aceptar.click()
                        log("✅ Popup aceptado")
                        popup_aceptado = True
                        break
                except:
                    try:
                        pagina.click("button:has-text('Aceptar')")
                        log("✅ Popup aceptado")
                        popup_aceptado = True
                        break
                    except:
                        time.sleep(2)

            if not popup_aceptado:
                log("⚠️ No se encontró popup")

            # ============================================================
            # PASO 6: CONTINUAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 6: Continuar...", 6)

            continuar_encontrado = False
            for intento in range(5):
                try:
                    selectores = [
                        "text=Continuar",
                        "text=Continue",
                        "button:has-text('Continuar')",
                        ".clsDivContinueButton"
                    ]
                    for selector in selectores:
                        try:
                            pagina.click(selector)
                            log(f"✅ Continuar clickeado ({selector})")
                            continuar_encontrado = True
                            break
                        except:
                            continue
                    if continuar_encontrado:
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
                    return resultado
                
                horarios = pagina.query_selector_all(".clsDivDatetimeSlot")
                if len(horarios) > 0:
                    break
                time.sleep(1)
                timeout -= 1
            
            if len(horarios) > 0:
                log(f"✅ Horarios encontrados: {len(horarios)}")
                horarios[0].click()
            else:
                log("❌ No hay horarios")
                resultado["motivo"] = "no_hay_horarios"
                capturar(pagina, "no_hay_horarios")
                navegador.close()
                return resultado
            
            # ============================================================
            # PASO 8: DATOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 8: Datos...", 8)
            
            time.sleep(2)
            
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 2:
                inputs[1].fill(cliente["pasaporte"])
                log(f"✅ Pasaporte: {cliente['pasaporte']}")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente["contrasena"])
                log("✅ Contraseña ingresada")
            
            # ============================================================
            # PASO 9: CONFIRMAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 9: Confirmar...", 9)
            
            try:
                pagina.click("text=Confirmar")
                log("✅ Confirmar clickeado")
            except:
                log("⚠️ No se encontró Confirmar")
            
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
            else:
                log("❌ No se confirmó")
                resultado["motivo"] = "no_confirmacion"
                capturar(pagina, "no_confirmacion")
            
            navegador.close()
            return resultado
            
        except Exception as e:
            log(f"❌ Error: {e}")
            resultado["motivo"] = f"error: {str(e)[:100]}"
            try:
                capturar(pagina, "error_general")
            except:
                pass
            navegador.close()
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
            return []
        
        log(f"📋 Clientes a procesar: {len(clientes)}")
        
        resultados = []
        for cliente in clientes:
            log(f"\n🔄 Procesando: {cliente.nombre}")
            
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
            else:
                log(f"❌ {cliente.nombre} - {resultado['motivo']}")
            
            resultados.append(resultado)
            time.sleep(5)
        
        log("\n🏁 Proceso completado")
        return resultados

if __name__ == "__main__":
    cliente = {
        "nombre": "Prueba Test",
        "pasaporte": "N123456",
        "contrasena": "tu_contraseña_real"
    }
    reservar_cita(cliente)