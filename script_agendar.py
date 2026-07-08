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
        # ============================================================
        # NAVEGADOR CONFIGURADO PARA RENDER (headless=True)
        # ============================================================
        navegador = p.chromium.launch(
            headless=True,  # IMPORTANTE: True para Render
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
        
        # Eliminar webdriver
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
                if LOGGER_OK:
                    log_success("✅ Cookies aceptadas", 2)
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
            
            # Buscar el enlace RFX
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
            
            # Esperar a que se abra una nueva página
            with contexto.expect_page() as nueva_pagina_info:
                enlace.click()
            
            # Cambiar a la nueva página
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
            
            # Verificar si hay captcha
            contenido = pagina.content()
            
            if "idCaptchaButton" in contenido or "Continue / Continuar" in contenido:
                log("🔐 CAPTCHA de Cloudflare detectado")
                capturar(pagina, "captcha_detectado")
                
                try:
                    # Buscar y hacer clic en el botón
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