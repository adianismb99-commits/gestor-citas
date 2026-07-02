import time
import os
import sys
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def capturar(driver, nombre):
    try:
        archivo = f"static/{nombre}.png"
        os.makedirs("static", exist_ok=True)
        driver.save_screenshot(archivo)
        log(f"📸 Captura: {archivo}")
        return archivo
    except:
        return None

def esperar_y_clickear(driver, by, selector, nombre="elemento", timeout=30):
    log(f"⏳ Esperando: {nombre}...")
    try:
        elemento = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        elemento.click()
        log(f"✅ Click: {nombre}")
        return True
    except:
        log(f"❌ No se encontró: {nombre}")
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
    
    # ============================================================
    # CONFIGURAR UNDETECTED-CHROMEDRIVER CON OPTIMIZACIONES
    # ============================================================
    log("📌 Configurando undetected-chromedriver...")
    if LOGGER_OK:
        log_info("📌 Configurando navegador anti-detección...")
    
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=256')
    options.add_argument('--js-flags="--max-old-space-size=256"')
    options.add_argument('--disable-crash-reporter')
    options.add_argument('--disable-in-process-stack-traces')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-breakpad')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-domain-reliability')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-offer-store-unmasked-wallet-cards')
    options.add_argument('--disable-password-generation')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-print-preview')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--disable-speech-api')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-web-security')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = uc.Chrome(
            options=options,
            version_main=None,
            use_subprocess=True,
            browser_executable_path=None
        )
        log("✅ undetected-chromedriver iniciado")
        if LOGGER_OK:
            log_success("✅ Navegador anti-detección iniciado")
    except Exception as e:
        log(f"❌ Error al iniciar Chrome: {e}")
        resultado["motivo"] = "chrome_error"
        return resultado
    
    try:
        # ============================================================
        # PASO 1: CARGAR PÁGINA
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 1: Cargando página...", 1)
        
        url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
        driver.get(url)
        log("⏳ Esperando que cargue la página...")
        time.sleep(5)
        
        # Esperar a que cargue
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            log("✅ Página cargada")
            if LOGGER_OK:
                log_success("✅ Página cargada", 1)
        except:
            log("⚠️ Timeout esperando página, continuando...")
        
        # Verificar Cloudflare
        if "cf-browser-verification" in driver.page_source or "Just a moment" in driver.title:
            log("⚠️ Cloudflare detectado, esperando 10 segundos...")
            time.sleep(10)
            capturar(driver, "cloudflare_detectado")
        
        # PASO 2: COOKIES
        if LOGGER_OK:
            log_info("📌 PASO 2: Cookies...", 2)
        
        try:
            cookie_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Aceptar']"))
            )
            cookie_btn.click()
            log("✅ Cookies aceptadas")
            if LOGGER_OK:
                log_success("✅ Cookies aceptadas", 2)
        except:
            try:
                cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Aceptar')]")
                cookie_btn.click()
                log("✅ Cookies aceptadas")
            except:
                log("⚠️ No se encontraron cookies")
        
        # PASO 3: RFX
        if LOGGER_OK:
            log_info("📌 PASO 3: RFX...", 3)
        
        enlace_rfx = None
        try:
            enlace_rfx = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Reservar cita de visados RFX')]"))
            )
            log("✅ RFX encontrado (texto exacto)")
        except:
            try:
                enlace_rfx = driver.find_element(By.XPATH, "//a[contains(@href, 'citaconsular.es')]")
                log("✅ RFX encontrado (por href)")
            except:
                log("❌ No se encontró RFX")
        
        if enlace_rfx:
            enlace_rfx.click()
            log("✅ Click en RFX")
            if LOGGER_OK:
                log_success("✅ RFX clickeado", 3)
        else:
            log("❌ No se encontró RFX")
            resultado["motivo"] = "no_rfx"
            driver.quit()
            return resultado
        
        # PASO 4: NUEVA VENTANA
        if LOGGER_OK:
            log_info("📌 PASO 4: Esperando nueva ventana...", 4)
        
        time.sleep(5)
        ventanas = driver.window_handles
        if len(ventanas) > 1:
            driver.switch_to.window(ventanas[-1])
            log("✅ Nueva ventana abierta")
            if LOGGER_OK:
                log_success("✅ Nueva ventana abierta", 4)
        else:
            log("⚠️ No se abrió nueva ventana, continuando...")
        
        # Esperar URL de citaconsular
        log("⏳ Esperando citaconsular.es...")
        timeout = 60
        while "citaconsular.es" not in driver.current_url and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        log(f"✅ URL: {driver.current_url}")
        if LOGGER_OK:
            log_success(f"✅ URL: {driver.current_url}", 4)
        
        capturar(driver, "paso_4_citaconsular")
        
        # ============================================================
        # PASO 5: ACEPTAR POPUP DE BIENVENIDA
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 5: Aceptando popup de bienvenida...", 5)
        
        log("⏳ Esperando popup de bienvenida...")
        
        try:
            aceptar_btn = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar')]"))
            )
            aceptar_btn.click()
            log("✅ Popup de bienvenida aceptado")
            if LOGGER_OK:
                log_success("✅ Popup de bienvenida aceptado", 5)
        except:
            log("⚠️ No se encontró popup de bienvenida")
        
        # ============================================================
        # PASO 6: CONTINUAR
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 6: Continuar...", 6)
        
        try:
            continuar_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar')]"))
            )
            continuar_btn.click()
            log("✅ Click en Continuar")
            if LOGGER_OK:
                log_success("✅ Continuar clickeado", 6)
        except:
            log("⚠️ No se encontró Continuar")
        
        # ============================================================
        # PASO 7: HORARIOS
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 7: Horarios...", 7)
        
        time.sleep(5)
        
        # Esperar a que carguen los horarios
        log("⏳ Esperando horarios...")
        timeout = 60
        horarios = []
        while timeout > 0:
            if "No hay horas disponibles" in driver.page_source:
                log("❌ No hay citas disponibles")
                resultado["motivo"] = "no_hay_citas"
                capturar(driver, "no_hay_citas")
                driver.quit()
                if LOGGER_OK:
                    finalizar_logs("No hay citas disponibles")
                return resultado
            
            horarios = driver.find_elements(By.CSS_SELECTOR, ".clsDivDatetimeSlot")
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
            capturar(driver, "no_hay_horarios")
            driver.quit()
            if LOGGER_OK:
                finalizar_logs("No hay horarios")
            return resultado
        
        # ============================================================
        # PASO 8: DATOS
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 8: Datos...", 8)
        
        time.sleep(3)
        
        # Pasaporte
        inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
        if len(inputs) >= 2:
            inputs[1].send_keys(cliente["pasaporte"])
            log(f"✅ Pasaporte: {cliente['pasaporte']}")
            if LOGGER_OK:
                log_success("✅ Pasaporte ingresado", 8)
        else:
            log("⚠️ No se encontró campo de pasaporte")
        
        # Contraseña
        try:
            password_input = driver.find_element(By.XPATH, "//input[@type='password']")
            password_input.send_keys(cliente["contrasena"])
            log("✅ Contraseña ingresada")
            if LOGGER_OK:
                log_success("✅ Contraseña ingresada", 8)
        except:
            log("⚠️ No se encontró campo de contraseña")
        
        # ============================================================
        # PASO 9: CONFIRMAR
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 9: Confirmar...", 9)
        
        try:
            confirmar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirmar')]")
            confirmar_btn.click()
            log("✅ Click en Confirmar")
            if LOGGER_OK:
                log_success("✅ Confirmar clickeado", 9)
        except:
            log("⚠️ No se encontró Confirmar")
        
        time.sleep(3)
        
        # ============================================================
        # PASO 10: RESULTADO
        # ============================================================
        if LOGGER_OK:
            log_info("📌 PASO 10: Resultado...", 10)
        
        if "Su reserva se ha realizado con éxito" in driver.page_source:
            log("🎉 CITA CONFIRMADA!")
            resultado["exito"] = True
            resultado["motivo"] = "cita_confirmada"
            capturar(driver, "cita_confirmada")
            if LOGGER_OK:
                log_success("🎉 CITA CONFIRMADA!", 10)
                finalizar_logs("¡CITA CONFIRMADA!")
        else:
            log("❌ No se confirmó")
            resultado["motivo"] = "no_confirmacion"
            capturar(driver, "no_confirmacion")
            if LOGGER_OK:
                log_error("❌ No se confirmó", 10)
                finalizar_logs("No se confirmó la cita")
        
        driver.quit()
        return resultado
        
    except Exception as e:
        log(f"❌ Error: {e}")
        resultado["motivo"] = f"error: {str(e)[:100]}"
        try:
            capturar(driver, "error")
        except:
            pass
        driver.quit()
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