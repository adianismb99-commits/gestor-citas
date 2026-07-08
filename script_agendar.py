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
    
    # URL DIRECTA DE CITAS
    URL_CITAS = "https://www.citaconsular.es/es/hosteds/widgetdefault/2686d3b68dc9e0db0ba3c6a20437e9cc7"
    
    # Referer (página del Ministerio)
    REFERER = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
    
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
            # PASO 1: IR DIRECTAMENTE A CITAS CON REFERER
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 1: Navegando directamente a citas con referer...", 1)
            
            log(f"🔄 Navegando a URL de citas...")
            pagina.goto(
                URL_CITAS,
                referer=REFERER,
                timeout=30000
            )
            log("✅ Navegación completada")
            time.sleep(5)
            
            # Verificar si estamos en citaconsular
            if "citaconsular.es" in pagina.url:
                log(f"✅ En citaconsular.es")
                if LOGGER_OK:
                    log_success(f"✅ En citaconsular.es", 1)
                capturar(pagina, "paso_1_citaconsular")
            else:
                log(f"⚠️ No estamos en citaconsular. URL: {pagina.url}")
                capturar(pagina, "error_url_no_citaconsular")
                navegador.close()
                resultado["motivo"] = "no_citaconsular"
                return resultado
            
            # ============================================================
            # PASO 2: POPUP DE BIENVENIDA
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 2: Aceptando popup de bienvenida...", 2)

            log("⏳ Esperando popup de bienvenida...")
            time.sleep(3)

            popup_aceptado = False
            for intento in range(5):
                log(f"   🔄 Intento {intento+1} de 5...")
                try:
                    # Buscar el botón Aceptar en el popup
                    aceptar = pagina.query_selector("text=Aceptar")
                    if aceptar:
                        aceptar.click()
                        log("✅ Popup de bienvenida aceptado")
                        popup_aceptado = True
                        if LOGGER_OK:
                            log_success("✅ Popup de bienvenida aceptado", 2)
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
            # PASO 3: CONTINUAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 3: Continuar...", 3)

            time.sleep(3)

            continuar_encontrado = False
            for intento in range(5):
                log(f"   🔄 Intentando Continuar {intento+1} de 5...")
                try:
                    pagina.click("text=Continuar")
                    log("✅ Click en Continuar")
                    continuar_encontrado = True
                    if LOGGER_OK:
                        log_success("✅ Continuar clickeado", 3)
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
            # PASO 4: HORARIOS
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 4: Buscando horarios...", 4)
            
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
                    log_success(f"✅ Horarios encontrados: {len(horarios)}", 4)
            else:
                log("❌ No hay horarios")
                resultado["motivo"] = "no_hay_horarios"
                capturar(pagina, "no_hay_horarios")
                navegador.close()
                if LOGGER_OK:
                    finalizar_logs("No hay horarios")
                return resultado
            
            # ============================================================
            # PASO 5: DATOS DEL CLIENTE
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 5: Ingresando datos...", 5)
            
            time.sleep(2)
            
            # Pasaporte
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 2:
                inputs[1].fill(cliente["pasaporte"])
                log(f"✅ Pasaporte: {cliente['pasaporte']}")
                if LOGGER_OK:
                    log_success("✅ Pasaporte ingresado", 5)
            else:
                log("⚠️ No se encontró campo de pasaporte")
                capturar(pagina, "error_no_pasaporte")
            
            # Contraseña
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente["contrasena"])
                log("✅ Contraseña ingresada")
                if LOGGER_OK:
                    log_success("✅ Contraseña ingresada", 5)
            else:
                log("⚠️ No se encontró campo de contraseña")
                capturar(pagina, "error_no_password")
            
            # ============================================================
            # PASO 6: CONFIRMAR
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 6: Confirmando...", 6)
            
            try:
                pagina.click("text=Confirmar")
                log("✅ Click en Confirmar")
                if LOGGER_OK:
                    log_success("✅ Confirmar clickeado", 6)
            except:
                try:
                    pagina.click("button:has-text('Confirmar')")
                    log("✅ Click en Confirmar (button)")
                except:
                    log("⚠️ No se encontró Confirmar")
                    capturar(pagina, "error_no_confirmar")
            
            time.sleep(2)
            
            # ============================================================
            # PASO 7: RESULTADO
            # ============================================================
            if LOGGER_OK:
                log_info("📌 PASO 7: Verificando resultado...", 7)
            
            contenido = pagina.content()
            if "Su reserva se ha realizado con éxito" in contenido:
                log("🎉 CITA CONFIRMADA!")
                resultado["exito"] = True
                resultado["motivo"] = "cita_confirmada"
                capturar(pagina, "cita_confirmada")
                if LOGGER_OK:
                    log_success("🎉 CITA CONFIRMADA!", 7)
                    finalizar_logs("¡CITA CONFIRMADA!")
            else:
                log("❌ No se confirmó la cita")
                resultado["motivo"] = "no_confirmacion"
                capturar(pagina, "no_confirmacion")
                if LOGGER_OK:
                    log_error("❌ No se confirmó", 7)
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