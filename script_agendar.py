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

def aceptar_cookies(pagina, paso=None):
    """Intenta aceptar cookies de TODAS las formas posibles"""
    log("🍪 Buscando botón de cookies...")
    if LOGGER_OK:
        log_info("🍪 Intentando aceptar cookies...", paso)
    
    # Lista de TODOS los selectores posibles para cookies
    selectores = [
        # Inputs
        "input[value='Aceptar']",
        "input[value='Aceptar cookies']",
        "input[value='Aceptar todas']",
        "input[value='Acepto']",
        "input[value='Entendido']",
        "input[value='OK']",
        "input[value='Ok']",
        "input[value='ok']",
        "input[type='submit'][value*='Aceptar']",
        "input[type='submit'][value*='aceptar']",
        
        # Botones por texto exacto
        "button:has-text('Aceptar')",
        "button:has-text('Aceptar cookies')",
        "button:has-text('Aceptar todas')",
        "button:has-text('Aceptar todo')",
        "button:has-text('Acepto')",
        "button:has-text('Entendido')",
        "button:has-text('OK')",
        "button:has-text('Ok')",
        "button:has-text('ok')",
        "button:has-text('Aceptar y cerrar')",
        "button:has-text('Aceptar y continuar')",
        "button:has-text('Continuar y aceptar')",
        
        # Botones por texto parcial (case insensitive)
        "button:has-text('Aceptar')",
        "button:has-text('aceptar')",
        "button:has-text('Acepto')",
        "button:has-text('acepto')",
        "button:has-text('Entendido')",
        "button:has-text('entendido')",
        "button:has-text('OK')",
        "button:has-text('Ok')",
        "button:has-text('ok')",
        
        # Botones por clase
        ".cookie-accept",
        ".cookie-accept-button",
        ".accept-cookies",
        ".accept-cookies-button",
        ".btn-accept-cookies",
        ".cookie-banner button",
        ".cookie-consent button",
        ".cookie-notice button",
        ".cookie-policy button",
        ".cookies button",
        ".cookie-accept-btn",
        ".cookie-accept-button",
        ".accept-cookie-btn",
        ".accept-btn",
        ".btn-accept",
        ".btn-cookie-accept",
        ".button-accept",
        ".button-cookie-accept",
        "[class*='cookie'] button",
        "[class*='cookie'] input[type='submit']",
        "[class*='Cookie'] button",
        "[class*='Cookie'] input[type='submit']",
        "[class*='cookie'] [class*='accept']",
        "[class*='Cookie'] [class*='accept']",
        
        # Botones por ID
        "#cookie-accept",
        "#accept-cookies",
        "#acceptCookies",
        "#cookies-accept",
        "#cookieAccept",
        "#cookie_accept",
        "#acceptCookie",
        "#btn-accept-cookies",
        "#btnAcceptCookies",
        "#cookie-btn-accept",
        "#cookie-accept-btn",
        "#cookie-banner-accept",
        "#cookie-consent-accept",
        "#cookie-notice-accept",
        "#cookie-policy-accept",
        "#cookies-accept-btn",
        "#cookies-accept-button",
        
        # Enlaces
        "a:has-text('Aceptar')",
        "a:has-text('Aceptar cookies')",
        "a:has-text('Aceptar todas')",
        "a:has-text('Acepto')",
        "a:has-text('Entendido')",
        "a:has-text('OK')",
        "a[href*='accept']",
        "a[href*='cookie']",
        
        # Divs que contienen el botón
        "div[class*='cookie'] button",
        "div[class*='Cookie'] button",
        "div[class*='cookie'] input",
        "div[class*='Cookie'] input",
        "div[class*='cookies'] button",
        "div[class*='Cookies'] button",
        "div[id*='cookie'] button",
        "div[id*='Cookie'] button",
        "div[class*='consent'] button",
        "div[class*='notice'] button",
        "div[class*='banner'] button",
        "div[class*='popup'] button",
        "div[class*='modal'] button",
        
        # Botones en español (variaciones)
        "button:has-text('Aceptar')",
        "button:has-text('Aceptar todas las cookies')",
        "button:has-text('Aceptar solo las necesarias')",
        "button:has-text('Aceptar cookies técnicas')",
        "button:has-text('Aceptar y continuar')",
        "button:has-text('Continuar con cookies')",
        "button:has-text('Estoy de acuerdo')",
        "button:has-text('De acuerdo')",
        "button:has-text('Entendido')",
        "button:has-text('Vale')",
        "button:has-text('Vale')",
        
        # Botones en inglés
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
        "button:has-text('Accept cookies')",
        "button:has-text('Accept all cookies')",
        "button:has-text('Accept and continue')",
        "button:has-text('I agree')",
        "button:has-text('Agree')",
        "button:has-text('Got it')",
        "button:has-text('Understood')",
        "button:has-text('OK')",
        "button:has-text('Ok')",
        
        # Botones por atributo data
        "[data-accept='cookies']",
        "[data-accept-cookies='true']",
        "[data-cookie-accept='true']",
        "[data-cookie-consent='accept']",
        "[data-cookie-banner='accept']",
        "[data-cookie-policy='accept']",
        "[data-cookie-notice='accept']",
        "[data-cookies-accept='true']",
        
        # Botones por role
        "button[role='button']:has-text('Aceptar')",
        "button[role='button']:has-text('Accept')",
        "button[role='button']:has-text('Acepto')",
        "button[role='button']:has-text('Entendido')",
        
        # Cualquier botón que contenga "cookie" en la página
        "button[class*='cookie']",
        "button[id*='cookie']",
        "button[name*='cookie']",
        "button[title*='cookie']",
        
        # Último recurso: cualquier botón visible en la página
        "button:visible",
        "input[type='button']:visible",
        "input[type='submit']:visible"
    ]
    
    cookies_aceptadas = False
    
    for selector in selectores:
        try:
            # Intentar encontrar el elemento
            elemento = pagina.wait_for_selector(selector, timeout=2000)
            if elemento:
                # Verificar que sea visible y clickeable
                if elemento.is_visible():
                    elemento.click()
                    log(f"✅ Cookies aceptadas con selector: {selector}")
                    if LOGGER_OK:
                        log_success(f"✅ Cookies aceptadas", paso)
                    cookies_aceptadas = True
                    time.sleep(1)
                    break
        except:
            continue
    
    # Si no encontró ningún selector, intentar buscar cualquier botón
    if not cookies_aceptadas:
        log("⚠️ No se encontró el botón de cookies con selectores específicos")
        log("🔍 Buscando cualquier botón que pueda ser de cookies...")
        if LOGGER_OK:
            log_warning("⚠️ Buscando cualquier botón de cookies...", paso)
        
        try:
            # Buscar cualquier botón en la página
            botones = pagina.query_selector_all("button")
            for boton in botones:
                texto = boton.text_content() or ""
                texto_lower = texto.lower()
                
                # Palabras clave para identificar botón de cookies
                palabras = ["aceptar", "acepto", "entendido", "ok", "accept", "agree", "got it", "understood", "cookie", "cookies"]
                
                if any(palabra in texto_lower for palabra in palabras):
                    if boton.is_visible():
                        boton.click()
                        log(f"✅ Cookies aceptadas con botón: '{texto}'")
                        if LOGGER_OK:
                            log_success(f"✅ Cookies aceptadas: '{texto}'", paso)
                        cookies_aceptadas = True
                        break
        except:
            pass
    
    # Si aún no encontró, buscar inputs
    if not cookies_aceptadas:
        try:
            inputs = pagina.query_selector_all("input[type='button'], input[type='submit']")
            for inp in inputs:
                valor = inp.get_attribute("value") or ""
                texto_lower = valor.lower()
                
                palabras = ["aceptar", "acepto", "entendido", "ok", "accept", "agree", "cookie", "cookies"]
                
                if any(palabra in texto_lower for palabra in palabras):
                    if inp.is_visible():
                        inp.click()
                        log(f"✅ Cookies aceptadas con input: '{valor}'")
                        if LOGGER_OK:
                            log_success(f"✅ Cookies aceptadas: '{valor}'", paso)
                        cookies_aceptadas = True
                        break
        except:
            pass
    
    if not cookies_aceptadas:
        log("⚠️ NO SE PUDIERON ACEPTAR LAS COOKIES")
        capturar(pagina, "error_cookies_no_aceptadas")
        if LOGGER_OK:
            log_warning("⚠️ No se pudieron aceptar cookies", paso)
    
    return cookies_aceptadas

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
            # PASO 2: COOKIES (CON TODAS LAS OPCIONES)
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 2: Aceptando cookies...", 2)
            
            aceptar_cookies(pagina, 2)
            
            # ============================================================
            # PASO 3: RFX
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 3: RFX...", 3)
            
            try:
                pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=15000)
                pagina.click("text=Reservar cita de visados RFX")
                log("✅ RFX encontrado")
                if LOGGER_OK:
                    log_success("✅ RFX encontrado", 3)
            except:
                try:
                    pagina.wait_for_selector("a[href*='citaconsular.es']", timeout=15000)
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
            
            # ============================================================
            # PASO 4: NUEVA VENTANA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 4: Esperando nueva ventana...", 4)
            
            time.sleep(2)
            
            paginas = navegador.context.pages
            if len(paginas) > 1:
                pagina = paginas[-1]
                log("✅ Nueva ventana abierta")
                if LOGGER_OK:
                    log_success("✅ Nueva ventana abierta", 4)
            else:
                log("⚠️ No se abrió nueva ventana, continuando...")
            
            log("⏳ Esperando citaconsular.es...")
            timeout = 20
            while "citaconsular.es" not in pagina.url and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
            if "citaconsular.es" in pagina.url:
                log(f"✅ URL: {pagina.url}")
                if LOGGER_OK:
                    log_success(f"✅ URL: {pagina.url}", 4)
            else:
                log(f"⚠️ No se cargó citaconsular.es, URL actual: {pagina.url}")
                capturar(pagina, "error_url_no_citaconsular")
            
            capturar(pagina, "paso_4_citaconsular")
            
            # ============================================================
            # PASO 5: POPUP DE BIENVENIDA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 5: Aceptando popup de bienvenida...", 5)

            log("⏳ Esperando popup de bienvenida...")
            time.sleep(2)

            popup_aceptado = False
            for intento in range(3):
                log(f"   🔄 Intento {intento+1} de 3...")
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

            time.sleep(2)

            continuar_encontrado = False
            for intento in range(3):
                log(f"   🔄 Intentando Continuar {intento+1} de 3...")
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