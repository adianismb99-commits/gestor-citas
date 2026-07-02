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

def esperar_y_clickear(pagina, selector, nombre="elemento", paso=None):
    log(f"⏳ Esperando: {nombre}...")
    if LOGGER_OK:
        log_info(f"⏳ Esperando: {nombre}", paso)
    while True:
        try:
            pagina.wait_for_selector(selector, timeout=1000)
            pagina.click(selector)
            log(f"✅ Click: {nombre}")
            if LOGGER_OK:
                log_success(f"✅ Click: {nombre}", paso)
            return True
        except:
            time.sleep(1)

def esperar_texto(pagina, texto, paso=None):
    log(f"⏳ Esperando texto: '{texto}'...")
    if LOGGER_OK:
        log_info(f"⏳ Esperando: '{texto}'", paso)
    while texto not in pagina.content():
        time.sleep(1)
    log(f"✅ Texto encontrado: '{texto}'")
    if LOGGER_OK:
        log_success(f"✅ Texto encontrado: '{texto}'", paso)

def esperar_requirejs(pagina, paso=None):
    log("⏳ Esperando RequireJS...")
    if LOGGER_OK:
        log_info("⏳ Esperando RequireJS...", paso)
    while True:
        try:
            script = """
            return (typeof require !== 'undefined' && 
                    typeof require.specified !== 'undefined' &&
                    require.specified('jquery') &&
                    require.specified('backbone'));
            """
            resultado = pagina.evaluate(script)
            if resultado:
                log("✅ RequireJS cargado")
                if LOGGER_OK:
                    log_success("✅ RequireJS cargado", paso)
                return True
        except:
            pass
        time.sleep(2)

def verificar_block_cloudflare(pagina):
    contenido = pagina.content()
    if "cf-browser-verification" in contenido or "challenge-platform" in contenido:
        return True
    if "503" in contenido and "TCDN-WAF" in contenido:
        return True
    return False

def aceptar_alerta(pagina, paso=None):
    """Intenta aceptar la alerta de TODAS las formas posibles"""
    log("=" * 50)
    log("🔍 INTENTANDO ACEPTAR ALERTA DE BIENVENIDA")
    log("=" * 50)
    if LOGGER_OK:
        log_info("🔍 Intentando aceptar alerta de bienvenida...", paso)
    
    aceptado = False
    metodos = []
    
    # ============================================================
    # MÉTODO 1: Diálogo de JavaScript (page.on)
    # ============================================================
    log("📌 MÉTODO 1: Buscando diálogo de JavaScript (page.on('dialog'))")
    if LOGGER_OK:
        log_info("📌 Método 1: page.on('dialog')", paso)
    
    def manejar_dialogo(dialog):
        log(f"   ✅ Diálogo detectado: {dialog.message}")
        if LOGGER_OK:
            log_success(f"   ✅ Diálogo detectado: {dialog.message}", paso)
        dialog.accept()
        log("   ✅ Alerta aceptada (dialog)")
        if LOGGER_OK:
            log_success("   ✅ Alerta aceptada (dialog)", paso)
        return True
    
    pagina.on("dialog", manejar_dialogo)
    
    # Esperar un momento
    time.sleep(2)
    
    # ============================================================
    # MÉTODO 2: Botón HTML con texto "Aceptar"
    # ============================================================
    log("📌 MÉTODO 2: Buscando botón HTML con texto 'Aceptar'")
    if LOGGER_OK:
        log_info("📌 Método 2: botón con texto 'Aceptar'", paso)
    
    try:
        aceptar = pagina.wait_for_selector("text=Aceptar", timeout=2000)
        if aceptar:
            aceptar.click()
            log("   ✅ Click en botón 'Aceptar' (texto exacto)")
            if LOGGER_OK:
                log_success("   ✅ Click en botón 'Aceptar'", paso)
            aceptado = True
            metodos.append("Método 2: text=Aceptar")
    except:
        log("   ❌ No se encontró 'Aceptar' exacto")
        if LOGGER_OK:
            log_warning("   ❌ No se encontró 'Aceptar' exacto", paso)
    
    # ============================================================
    # MÉTODO 3: Botón HTML con texto "Aceptar" (case insensitive)
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 3: Buscando botón con texto que contenga 'Aceptar' (insensitive)")
        if LOGGER_OK:
            log_info("📌 Método 3: botón contiene 'Aceptar'", paso)
        
        try:
            botones = pagina.query_selector_all("button")
            for boton in botones:
                texto = boton.text_content()
                if texto and "aceptar" in texto.lower():
                    boton.click()
                    log(f"   ✅ Click en botón: '{texto}'")
                    if LOGGER_OK:
                        log_success(f"   ✅ Click en botón: '{texto}'", paso)
                    aceptado = True
                    metodos.append(f"Método 3: botón contiene 'Aceptar' - texto: {texto}")
                    break
        except Exception as e:
            log(f"   ❌ Error: {e}")
    
    # ============================================================
    # MÉTODO 4: Botón HTML con texto "Entendido"
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 4: Buscando botón con texto 'Entendido'")
        if LOGGER_OK:
            log_info("📌 Método 4: botón 'Entendido'", paso)
        
        try:
            entendido = pagina.wait_for_selector("text=Entendido", timeout=1000)
            if entendido:
                entendido.click()
                log("   ✅ Click en botón 'Entendido'")
                if LOGGER_OK:
                    log_success("   ✅ Click en 'Entendido'", paso)
                aceptado = True
                metodos.append("Método 4: text=Entendido")
        except:
            log("   ❌ No se encontró 'Entendido'")
    
    # ============================================================
    # MÉTODO 5: Botón HTML con texto "Welcome"
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 5: Buscando botón con texto 'Welcome'")
        if LOGGER_OK:
            log_info("📌 Método 5: botón 'Welcome'", paso)
        
        try:
            welcome = pagina.wait_for_selector("text=Welcome", timeout=1000)
            if welcome:
                welcome.click()
                log("   ✅ Click en botón 'Welcome'")
                if LOGGER_OK:
                    log_success("   ✅ Click en 'Welcome'", paso)
                aceptado = True
                metodos.append("Método 5: text=Welcome")
        except:
            log("   ❌ No se encontró 'Welcome'")
    
    # ============================================================
    # MÉTODO 6: Botón HTML con texto "Bienvenido"
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 6: Buscando botón con texto 'Bienvenido'")
        if LOGGER_OK:
            log_info("📌 Método 6: botón 'Bienvenido'", paso)
        
        try:
            bienvenido = pagina.wait_for_selector("text=Bienvenido", timeout=1000)
            if bienvenido:
                bienvenido.click()
                log("   ✅ Click en botón 'Bienvenido'")
                if LOGGER_OK:
                    log_success("   ✅ Click en 'Bienvenido'", paso)
                aceptado = True
                metodos.append("Método 6: text=Bienvenido")
        except:
            log("   ❌ No se encontró 'Bienvenido'")
    
    # ============================================================
    # MÉTODO 7: Botón con clase "welcome"
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 7: Buscando botón con clase 'welcome'")
        if LOGGER_OK:
            log_info("📌 Método 7: botón con clase 'welcome'", paso)
        
        try:
            welcome_btn = pagina.query_selector("button[class*='welcome']")
            if welcome_btn:
                welcome_btn.click()
                log("   ✅ Click en botón con clase 'welcome'")
                if LOGGER_OK:
                    log_success("   ✅ Click en botón con clase 'welcome'", paso)
                aceptado = True
                metodos.append("Método 7: button[class*='welcome']")
        except Exception as e:
            log(f"   ❌ Error: {e}")
    
    # ============================================================
    # MÉTODO 8: Botón con clase "btn-primary" y texto "Aceptar"
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 8: Buscando botón con clase 'btn-primary' y texto 'Aceptar'")
        if LOGGER_OK:
            log_info("📌 Método 8: btn-primary con 'Aceptar'", paso)
        
        try:
            botones = pagina.query_selector_all("button.btn-primary")
            for boton in botones:
                texto = boton.text_content()
                if texto and ("Aceptar" in texto or "aceptar" in texto.lower()):
                    boton.click()
                    log(f"   ✅ Click en botón: '{texto}' (btn-primary)")
                    if LOGGER_OK:
                        log_success(f"   ✅ Click en botón: '{texto}'", paso)
                    aceptado = True
                    metodos.append(f"Método 8: btn-primary - texto: {texto}")
                    break
        except Exception as e:
            log(f"   ❌ Error: {e}")
    
    # ============================================================
    # MÉTODO 9: Buscar cualquier botón que tenga "Aceptar" en el DOM
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 9: Buscando ANY botón con 'Aceptar' en el DOM")
        if LOGGER_OK:
            log_info("📌 Método 9: ANY botón con 'Aceptar'", paso)
        
        try:
            elementos = pagina.query_selector_all("button, a, input[type='button'], input[type='submit']")
            for elemento in elementos:
                texto = elemento.text_content() or elemento.get_attribute("value") or ""
                if texto and "aceptar" in texto.lower():
                    elemento.click()
                    log(f"   ✅ Click en elemento: '{texto}'")
                    if LOGGER_OK:
                        log_success(f"   ✅ Click en elemento: '{texto}'", paso)
                    aceptado = True
                    metodos.append(f"Método 9: ANY - texto: {texto}")
                    break
        except Exception as e:
            log(f"   ❌ Error: {e}")
    
    # ============================================================
    # MÉTODO 10: Esperar a que la alerta desaparezca sola
    # ============================================================
    if not aceptado:
        log("📌 MÉTODO 10: Esperando a que la alerta desaparezca sola (timeout 10s)")
        if LOGGER_OK:
            log_info("📌 Método 10: esperar desaparición", paso)
        
        time.sleep(10)
        log("   ⏳ Espera completada, verificando si hay contenido...")
    
    # ============================================================
    # RESULTADO
    # ============================================================
    if aceptado:
        log("=" * 50)
        log(f"✅ ALERTA ACEPTADA con: {metodos[0] if metodos else 'desconocido'}")
        log("=" * 50)
        if LOGGER_OK:
            log_success(f"✅ Alerta aceptada con: {metodos[0] if metodos else 'desconocido'}", paso)
    else:
        log("=" * 50)
        log("⚠️ NO SE PUDO ACEPTAR LA ALERTA, continuando...")
        log("=" * 50)
        if LOGGER_OK:
            log_warning("⚠️ No se pudo aceptar alerta, continuando...", paso)
    
    return aceptado

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
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pagina = navegador.new_page()
        paso_actual = 1
        
        try:
            # ============================================================
            # PASO 1: CARGAR PÁGINA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 1: Cargando página...", paso_actual)
            url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            pagina.goto(url, timeout=60000)
            esperar_texto(pagina, "Servicios consulares", paso_actual)
            if LOGGER_OK:
                log_success("✅ Página cargada", paso_actual)
            paso_actual += 1
            
            if verificar_block_cloudflare(pagina):
                log("❌ CLOUDFLARE BLOQUEA")
                if LOGGER_OK:
                    log_error("❌ Cloudflare bloquea", paso_actual)
                resultado["motivo"] = "cloudflare_block"
                capturar(pagina, "cloudflare_block")
                navegador.close()
                if LOGGER_OK:
                    finalizar_logs("Bloqueado por Cloudflare")
                return resultado
            
            # ============================================================
            # PASO 2: COOKIES
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 2: Cookies...", paso_actual)
            try:
                pagina.wait_for_selector("input[value='Aceptar']", timeout=5000)
                pagina.click("input[value='Aceptar']")
                log("✅ Cookies aceptadas")
                if LOGGER_OK:
                    log_success("✅ Cookies aceptadas", paso_actual)
            except:
                try:
                    pagina.wait_for_selector("button:has-text('Aceptar')", timeout=5000)
                    pagina.click("button:has-text('Aceptar')")
                    log("✅ Cookies aceptadas")
                    if LOGGER_OK:
                        log_success("✅ Cookies aceptadas", paso_actual)
                except:
                    log("⚠️ No se encontraron cookies")
                    if LOGGER_OK:
                        log_warning("⚠️ No se encontraron cookies", paso_actual)
            paso_actual += 1
            
            # ============================================================
            # PASO 3: RFX + ESPERAR NUEVA VENTANA CON expect_page()
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 3: RFX y esperando nueva ventana...", paso_actual)

            log("⏳ Preparando para hacer clic en RFX y capturar nueva ventana...")
            if LOGGER_OK:
                log_info("⏳ Preparando expect_page...", paso_actual)

            try:
                with navegador.contexts[0].expect_page() as nueva_pagina_info:
                    try:
                        enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=30000)
                        if enlace:
                            log("✅ Enlace RFX encontrado, haciendo click...")
                            if LOGGER_OK:
                                log_success("✅ Enlace RFX encontrado", paso_actual)
                            enlace.click()
                    except:
                        enlace = pagina.wait_for_selector("a[href*='citaconsular.es']", timeout=30000)
                        if enlace:
                            log("✅ Enlace RFX encontrado por href, haciendo click...")
                            if LOGGER_OK:
                                log_success("✅ Enlace RFX encontrado por href", paso_actual)
                            enlace.click()
                
                pagina = nueva_pagina_info.value
                log("✅ Nueva ventana capturada con expect_page!")
                if LOGGER_OK:
                    log_success("✅ Nueva ventana capturada con expect_page", paso_actual)
                    
            except Exception as e:
                log(f"❌ Error al capturar nueva ventana: {e}")
                if LOGGER_OK:
                    log_error(f"❌ Error al capturar nueva ventana: {e}", paso_actual)
                resultado["motivo"] = "expect_page_failed"
                navegador.close()
                return resultado

            paso_actual += 1

            # ============================================================
            # PASO 4: ESPERAR CARGA DE CITACONSULAR Y ACEPTAR ALERTA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 4: Esperando carga de citaconsular.es...", paso_actual)

            log("⏳ Esperando que cargue citaconsular.es...")
            if LOGGER_OK:
                log_info("⏳ Esperando URL de citaconsular.es...", paso_actual)

            intentos = 0
            while "citaconsular.es" not in pagina.url:
                intentos += 1
                if intentos % 5 == 0:
                    log(f"   ⏳ Esperando citaconsular.es... ({intentos}s) - URL actual: {pagina.url}")
                    if LOGGER_OK:
                        log_info(f"⏳ Esperando citaconsular.es... ({intentos}s) - URL: {pagina.url}", paso_actual)
                time.sleep(1)

            log(f"✅ URL cargada correctamente: {pagina.url}")
            if LOGGER_OK:
                log_success(f"✅ URL cargada: {pagina.url}", paso_actual)

            log("⏳ Esperando que cargue el contenido de la página...")
            if LOGGER_OK:
                log_info("⏳ Esperando contenido de la página...", paso_actual)

            try:
                pagina.wait_for_load_state("networkidle", timeout=30000)
                log("✅ Contenido cargado (networkidle)")
                if LOGGER_OK:
                    log_success("✅ Contenido cargado", paso_actual)
            except:
                log("⚠️ Timeout esperando networkidle, continuando...")
                if LOGGER_OK:
                    log_warning("⚠️ Timeout networkidle, continuando...", paso_actual)

            # ============================================================
            # ACEPTAR ALERTA CON TODOS LOS MÉTODOS POSIBLES
            # ============================================================
            aceptar_alerta(pagina, paso_actual)

            # Esperar un momento después de la alerta
            time.sleep(2)
            
            # Captura de pantalla final del PASO 4
            log("📸 Tomando captura de pantalla del PASO 4...")
            capturar(pagina, "paso_4_ventana_cargada")
            log("✅ Captura guardada: paso_4_ventana_cargada.png")
            if LOGGER_OK:
                log_success("✅ Captura del paso 4 guardada", paso_actual)

            log("=" * 50)
            log("✅ PASO 4 COMPLETADO")
            log("=" * 50)

            paso_actual += 1
            
            # ============================================================
            # PASO 5: CONTINUAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 5: Continuar...", paso_actual)
            
            # Intentar varias formas de encontrar "Continuar"
            log("🔍 Buscando botón Continuar...")
            continuar_encontrado = False
            
            # Forma 1: text=Continuar
            try:
                pagina.wait_for_selector("text=Continuar", timeout=5000)
                pagina.click("text=Continuar")
                log("✅ Click en Continuar (text=Continuar)")
                if LOGGER_OK:
                    log_success("✅ Continuar click", paso_actual)
                continuar_encontrado = True
            except:
                log("   ❌ No se encontró 'Continuar' exacto")
            
            # Forma 2: text=Continue
            if not continuar_encontrado:
                try:
                    pagina.wait_for_selector("text=Continue", timeout=3000)
                    pagina.click("text=Continue")
                    log("✅ Click en Continuar (text=Continue)")
                    if LOGGER_OK:
                        log_success("✅ Continuar click (Continue)", paso_actual)
                    continuar_encontrado = True
                except:
                    log("   ❌ No se encontró 'Continue'")
            
            # Forma 3: clsDivContinueButton
            if not continuar_encontrado:
                try:
                    pagina.wait_for_selector(".clsDivContinueButton", timeout=3000)
                    pagina.click(".clsDivContinueButton")
                    log("✅ Click en Continuar (.clsDivContinueButton)")
                    if LOGGER_OK:
                        log_success("✅ Continuar click (CSS)", paso_actual)
                    continuar_encontrado = True
                except:
                    log("   ❌ No se encontró '.clsDivContinueButton'")
            
            # Forma 4: button con texto "Continuar"
            if not continuar_encontrado:
                try:
                    botones = pagina.query_selector_all("button")
                    for boton in botones:
                        texto = boton.text_content()
                        if texto and "continuar" in texto.lower():
                            boton.click()
                            log(f"✅ Click en botón: '{texto}'")
                            if LOGGER_OK:
                                log_success(f"✅ Click en botón: '{texto}'", paso_actual)
                            continuar_encontrado = True
                            break
                except Exception as e:
                    log(f"   ❌ Error buscando botones: {e}")
            
            if not continuar_encontrado:
                log("⚠️ No se encontró Continuar en ninguna forma")
                if LOGGER_OK:
                    log_warning("⚠️ No se encontró Continuar", paso_actual)
            
            paso_actual += 1
            
            # ============================================================
            # PASO 6: HORARIOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 6: Horarios...", paso_actual)
            esperar_requirejs(pagina, paso_actual)
            time.sleep(5)
            
            contenido = pagina.content()
            if "No hay horas disponibles" in contenido:
                log("❌ No hay citas")
                if LOGGER_OK:
                    log_warning("❌ No hay citas disponibles", paso_actual)
                resultado["motivo"] = "no_hay_citas"
                capturar(pagina, "no_hay_citas")
                navegador.close()
                if LOGGER_OK:
                    finalizar_logs("No hay citas disponibles")
                return resultado
            
            # Buscar horarios
            horarios = pagina.query_selector_all(".clsDivDatetimeSlot")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("[class*='slot']")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            
            if len(horarios) == 0:
                log("❌ No hay horarios")
                if LOGGER_OK:
                    log_warning("❌ No hay horarios", paso_actual)
                resultado["motivo"] = "no_hay_horarios"
                capturar(pagina, "no_hay_horarios")
                navegador.close()
                if LOGGER_OK:
                    finalizar_logs("No hay horarios")
                return resultado
            
            log(f"✅ Horarios encontrados: {len(horarios)}")
            if LOGGER_OK:
                log_success(f"✅ Horarios encontrados: {len(horarios)}", paso_actual)
            horarios[0].click()
            paso_actual += 1
            
            # ============================================================
            # PASO 7: DATOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 7: Datos...", paso_actual)
            
            # Esperar campos
            time.sleep(3)
            
            # Buscar pasaporte
            campo_pasaporte = None
            try:
                campo_pasaporte = pagina.query_selector("input[placeholder='Pasaporte']")
            except:
                pass
            
            if campo_pasaporte is None:
                inputs = pagina.query_selector_all("input[type='text']")
                if len(inputs) >= 2:
                    campo_pasaporte = inputs[1]
                elif len(inputs) >= 1:
                    campo_pasaporte = inputs[0]
            
            if campo_pasaporte:
                campo_pasaporte.fill(cliente["pasaporte"])
                log(f"✅ Pasaporte: {cliente['pasaporte']}")
                if LOGGER_OK:
                    log_success("✅ Pasaporte ingresado", paso_actual)
            
            # Buscar contraseña
            campo_password = pagina.query_selector("input[type='password']")
            if campo_password:
                campo_password.fill(cliente["contrasena"])
                log("✅ Contraseña ingresada")
                if LOGGER_OK:
                    log_success("✅ Contraseña ingresada", paso_actual)
            paso_actual += 1
            
            # ============================================================
            # PASO 8: CONFIRMAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 8: Confirmar...", paso_actual)
            try:
                esperar_y_clickear(pagina, "text=Confirmar", "Confirmar", paso_actual)
                if LOGGER_OK:
                    log_success("✅ Confirmar click", paso_actual)
            except:
                try:
                    esperar_y_clickear(pagina, "button:has-text('Confirmar')", "Confirmar (button)", paso_actual)
                    if LOGGER_OK:
                        log_success("✅ Confirmar click", paso_actual)
                except:
                    try:
                        esperar_y_clickear(pagina, "input[value='Confirmar']", "Confirmar (input)", paso_actual)
                        if LOGGER_OK:
                            log_success("✅ Confirmar click", paso_actual)
                    except:
                        log("⚠️ No se encontró Confirmar")
                        if LOGGER_OK:
                            log_warning("⚠️ No se encontró Confirmar", paso_actual)
            paso_actual += 1
            
            # ============================================================
            # PASO 9: RESULTADO
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 9: Resultado...", paso_actual)
            for _ in range(30):
                contenido = pagina.content()
                if "Su reserva se ha realizado con éxito" in contenido:
                    log("🎉 CITA CONFIRMADA!")
                    if LOGGER_OK:
                        log_success("🎉 CITA CONFIRMADA!", paso_actual)
                    resultado["exito"] = True
                    resultado["motivo"] = "cita_confirmada"
                    capturar(pagina, "cita_confirmada")
                    navegador.close()
                    if LOGGER_OK:
                        finalizar_logs("¡CITA CONFIRMADA!")
                    return resultado
                if "No hay" in contenido and "horas" in contenido:
                    log("❌ No hay citas")
                    if LOGGER_OK:
                        log_warning("❌ No hay citas", paso_actual)
                    resultado["motivo"] = "no_hay_citas"
                    capturar(pagina, "no_hay_citas")
                    navegador.close()
                    if LOGGER_OK:
                        finalizar_logs("No hay citas disponibles")
                    return resultado
                time.sleep(1)
            
            log("❌ No se confirmó")
            if LOGGER_OK:
                log_error("❌ No se confirmó", paso_actual)
            resultado["motivo"] = "no_confirmacion"
            capturar(pagina, "no_confirmacion")
            navegador.close()
            if LOGGER_OK:
                finalizar_logs("No se confirmó la cita")
            return resultado
            
        except Exception as e:
            log(f"❌ Error: {e}")
            if LOGGER_OK:
                log_error(f"❌ Error: {str(e)[:100]}", paso_actual)
            resultado["motivo"] = f"error: {str(e)[:100]}"
            try:
                capturar(pagina, "error")
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