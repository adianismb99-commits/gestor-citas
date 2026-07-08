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

def esperar_y_clickear(pagina, selector, nombre="elemento", timeout=30000):
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
        # Playwright consume MUCHA MENOS memoria
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
        
        # Configurar timeout por defecto
        pagina.set_default_timeout(30000)
        
        try:
            # ============================================================
            # PASO 1: CARGAR PÁGINA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 1: Cargando página...", 1)
            
            url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            pagina.goto(url, timeout=60000)
            log("⏳ Esperando que cargue la página...")
            time.sleep(10)
            
            # Verificar Cloudflare
            contenido = pagina.content()
            if "cf-browser-verification" in contenido or "Just a moment" in await pagina.title():
                log("⚠️ Cloudflare detectado, esperando 15 segundos...")
                time.sleep(15)
                capturar(pagina, "cloudflare_detectado")
            
            # Esperar texto
            try:
                pagina.wait_for_selector("text=Servicios consulares", timeout=30000)
                log("✅ Página cargada")
                if LOGGER_OK:
                    log_success("✅ Página cargada", 1)
            except:
                log("⚠️ No se encontró texto 'Servicios consulares', continuando...")
                capturar(pagina, "error_no_texto")
            
            # PASO 2: COOKIES
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
            
            # PASO 3: RFX
            if LOGGER_OK:
                log_info("📌 PASO 3: RFX...", 3)
            
            try:
                pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=30000)
                pagina.click("text=Reservar cita de visados RFX")
                log("✅ RFX encontrado")
                if LOGGER_OK:
                    log_success("✅ RFX encontrado", 3)
            except:
                try:
                    pagina.wait_for_selector("a[href*='citaconsular.es']", timeout=30000)
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
            
            # PASO 4: NUEVA VENTANA
            if LOGGER_OK:
                log_info("📌 PASO 4: Esperando nueva ventana...", 4)
            
            time.sleep(5)
            
            # Obtener todas las páginas
            paginas = navegador.context.pages
            if len(paginas) > 1:
                pagina = paginas[-1]
                log("✅ Nueva ventana abierta")
                if LOGGER_OK:
                    log_success("✅ Nueva ventana abierta", 4)
            else:
                log("⚠️ No se abrió nueva ventana, continuando...")
            
            # Esperar URL de citaconsular
            log("⏳ Esperando citaconsular.es...")
            timeout = 60
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
            
            # PASO 5: POPUP DE BIENVENIDA
            if LOGGER_OK:
                log_info("📌 PASO 5: Aceptando popup de bienvenida...", 5)

            log("⏳ Esperando popup de bienvenida...")
            time.sleep(10)

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
                        time.sleep(5)

            if not popup_aceptado:
                log("⚠️ No se encontró popup de bienvenida, continuando...")
                capturar(pagina, "error_no_popup")

            # PASO 6: CONTINUAR
            if LOGGER_OK:
                log_info("📌 PASO 6: Continuar...", 6)

            log("⏳ Esperando 10 segundos...")
            time.sleep(10)

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
                            time.sleep(5)

            if not continuar_encontrado:
                log("⚠️ No se encontró Continuar")
                capturar(pagina, "error_no_continuar")

            # PASO 7: HORARIOS
            if LOGGER_OK:
                log_info("📌 PASO 7: Horarios...", 7)
            
            time.sleep(10)
            
            log("⏳ Esperando horarios...")
            timeout = 60
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
            
            # PASO 8: DATOS
            if LOGGER_OK:
                log_info("📌 PASO 8: Datos...", 8)
            
            time.sleep(5)
            
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
            
            # PASO 9: CONFIRMAR
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
            
            time.sleep(3)
            
            # PASO 10: RESULTADO
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