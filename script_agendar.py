import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Importar logger
try:
    from logger import log_info, log_success, log_warning, log_error, finalizar_logs, limpiar_logs
    LOGGER_OK = True
except:
    LOGGER_OK = False
    print("⚠️ Logger no disponible")

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

def esperar_y_clickear(driver, selectores, nombre="elemento", paso=None):
    log(f"⏳ Esperando: {nombre}...")
    if LOGGER_OK:
        log_info(f"Esperando: {nombre}", paso)
    while True:
        for selector in selectores:
            try:
                elemento = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(0.5)
                elemento.click()
                log(f"✅ Click: {nombre}")
                if LOGGER_OK:
                    log_success(f"Click: {nombre}", paso)
                return True
            except:
                continue
        time.sleep(1)

def esperar_texto(driver, texto, paso=None):
    log(f"⏳ Esperando texto: '{texto}'...")
    if LOGGER_OK:
        log_info(f"Esperando texto: '{texto}'", paso)
    while texto not in driver.page_source:
        time.sleep(1)
    log(f"✅ Texto encontrado: '{texto}'")
    if LOGGER_OK:
        log_success(f"Texto encontrado: '{texto}'", paso)

def esperar_requirejs(driver, paso=None):
    log("⏳ Esperando RequireJS...")
    if LOGGER_OK:
        log_info("Esperando RequireJS...", paso)
    while True:
        try:
            script = """
            return (typeof require !== 'undefined' && 
                    typeof require.specified !== 'undefined' &&
                    require.specified('jquery') &&
                    require.specified('backbone'));
            """
            if driver.execute_script(script):
                log("✅ RequireJS cargado")
                if LOGGER_OK:
                    log_success("RequireJS cargado", paso)
                return True
        except:
            pass
        time.sleep(2)

def verificar_block_cloudflare(driver):
    pagina = driver.page_source
    if "cf-browser-verification" in pagina or "challenge-platform" in pagina:
        return True
    if "503" in pagina and "TCDN-WAF" in pagina:
        return True
    return False

def reservar_cita(cliente):
    log(f"🚀 Iniciando reserva para {cliente['nombre']}")
    if LOGGER_OK:
        log_info(f"Iniciando reserva para {cliente['nombre']}")
        limpiar_logs()
    
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    
    from webdriver_manager.chrome import ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    resultado = {
        "exito": False,
        "motivo": "",
        "captura": None
    }
    
    paso_actual = 1
    
    try:
        # PASO 1: Cargar página
        if LOGGER_OK:
            log_info("📌 PASO 1: Cargando página principal...", paso_actual)
        url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
        driver.get(url)
        esperar_texto(driver, "Servicios consulares", paso_actual)
        if LOGGER_OK:
            log_success("✅ Página cargada", paso_actual)
        paso_actual += 1
        
        if verificar_block_cloudflare(driver):
            log("❌ CLOUDFLARE BLOQUEA")
            if LOGGER_OK:
                log_error("Cloudflare bloquea el acceso", paso_actual)
            resultado["motivo"] = "cloudflare_block"
            capturar(driver, "cloudflare_block")
            driver.quit()
            if LOGGER_OK:
                finalizar_logs("Bloqueado por Cloudflare")
            return resultado
        
        # PASO 2: Cookies
        if LOGGER_OK:
            log_info("📌 PASO 2: Aceptando cookies...", paso_actual)
        selectores_cookies = [
            "//input[@value='Aceptar']",
            "//button[contains(text(), 'Aceptar')]",
        ]
        esperar_y_clickear(driver, selectores_cookies, "cookies", paso_actual)
        if LOGGER_OK:
            log_success("✅ Cookies aceptadas", paso_actual)
        paso_actual += 1
        
        # PASO 3: RFX
        if LOGGER_OK:
            log_info("📌 PASO 3: Buscando enlace RFX...", paso_actual)
        selectores_rfx = [
            "//a[contains(text(), 'Reservar cita de visados RFX')]",
            "//a[contains(@href, 'citaconsular.es')]",
        ]
        esperar_y_clickear(driver, selectores_rfx, "RFX", paso_actual)
        if LOGGER_OK:
            log_success("✅ Enlace RFX encontrado", paso_actual)
        paso_actual += 1
        
        # PASO 4: Nueva ventana + Alerta
        if LOGGER_OK:
            log_info("📌 PASO 4: Nueva ventana y alerta...", paso_actual)
        while len(driver.window_handles) < 2:
            time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        if LOGGER_OK:
            log_success("✅ Nueva ventana abierta", paso_actual)
        
        if LOGGER_OK:
            log_info("⏳ Esperando alerta Welcome/Bienvenido...", paso_actual)
        while True:
            try:
                alerta = driver.switch_to.alert
                alerta.accept()
                if LOGGER_OK:
                    log_success("✅ Alerta aceptada", paso_actual)
                break
            except:
                time.sleep(1)
        
        while "citaconsular.es" not in driver.current_url:
            time.sleep(1)
        if LOGGER_OK:
            log_success(f"✅ URL cargada", paso_actual)
        paso_actual += 1
        
        # PASO 5: Continuar
        if LOGGER_OK:
            log_info("📌 PASO 5: Buscando Continuar...", paso_actual)
        selectores_continuar = [
            "//button[contains(text(), 'Continuar')]",
            "//*[contains(@class, 'clsDivContinueButton')]",
        ]
        esperar_y_clickear(driver, selectores_continuar, "Continuar", paso_actual)
        if LOGGER_OK:
            log_success("✅ Click en Continuar", paso_actual)
        paso_actual += 1
        
        # PASO 6: Horarios
        if LOGGER_OK:
            log_info("📌 PASO 6: Buscando horarios...", paso_actual)
        esperar_requirejs(driver, paso_actual)
        time.sleep(5)
        
        pagina = driver.page_source
        if "No hay horas disponibles" in pagina:
            log("❌ No hay citas")
            if LOGGER_OK:
                log_warning("No hay citas disponibles", paso_actual)
            resultado["motivo"] = "no_hay_citas"
            capturar(driver, "no_hay_citas")
            driver.quit()
            if LOGGER_OK:
                finalizar_logs("No hay citas disponibles")
            return resultado
        
        horarios = driver.find_elements(By.CSS_SELECTOR, ".clsDivDatetimeSlot")
        if len(horarios) == 0:
            horarios = driver.find_elements(By.XPATH, "//*[contains(text(), ':') and (contains(text(), '8') or contains(text(), '9'))]")
        
        horarios_filtrados = []
        for h in horarios:
            texto = h.text.strip()
            if texto and "No hay" not in texto:
                horarios_filtrados.append(h)
        horarios = horarios_filtrados
        
        if len(horarios) == 0:
            log("❌ No hay horarios")
            if LOGGER_OK:
                log_warning("No hay horarios disponibles", paso_actual)
            resultado["motivo"] = "no_hay_horarios"
            capturar(driver, "no_hay_horarios")
            driver.quit()
            if LOGGER_OK:
                finalizar_logs("No hay horarios disponibles")
            return resultado
        
        log(f"✅ Horarios: {len(horarios)}")
        if LOGGER_OK:
            log_success(f"Horarios encontrados: {len(horarios)}", paso_actual)
        horarios[0].click()
        paso_actual += 1
        
        # PASO 7: Datos
        if LOGGER_OK:
            log_info("📌 PASO 7: Rellenando datos...", paso_actual)
        
        inputs = []
        while len(inputs) == 0:
            inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
            time.sleep(1)
        
        campo_pasaporte = None
        try:
            campo_pasaporte = driver.find_element(By.XPATH, "//input[@placeholder='Pasaporte' or contains(@placeholder, 'pasaporte')]")
        except:
            if len(inputs) >= 2:
                campo_pasaporte = inputs[1]
            elif len(inputs) >= 1:
                campo_pasaporte = inputs[0]
        
        if campo_pasaporte:
            campo_pasaporte.send_keys(cliente["pasaporte"])
            log(f"✅ Pasaporte: {cliente['pasaporte']}")
            if LOGGER_OK:
                log_success(f"Pasaporte ingresado", paso_actual)
        
        campo_password = driver.find_element(By.XPATH, "//input[@type='password']")
        if campo_password:
            campo_password.send_keys(cliente["contrasena"])
            log("✅ Contraseña ingresada")
            if LOGGER_OK:
                log_success("Contraseña ingresada", paso_actual)
        paso_actual += 1
        
        # PASO 8: Confirmar
        if LOGGER_OK:
            log_info("📌 PASO 8: Confirmando...", paso_actual)
        selectores_confirmar = [
            "//button[contains(text(), 'Confirmar')]",
            "//input[@value='Confirmar']",
        ]
        esperar_y_clickear(driver, selectores_confirmar, "Confirmar", paso_actual)
        if LOGGER_OK:
            log_success("✅ Confirmar click", paso_actual)
        paso_actual += 1
        
        # PASO 9: Resultado
        if LOGGER_OK:
            log_info("📌 PASO 9: Verificando resultado...", paso_actual)
        for _ in range(30):
            if "Su reserva se ha realizado con éxito" in driver.page_source:
                log("🎉 CITA CONFIRMADA!")
                if LOGGER_OK:
                    log_success("🎉 CITA CONFIRMADA!", paso_actual)
                resultado["exito"] = True
                resultado["motivo"] = "cita_confirmada"
                capturar(driver, "cita_confirmada")
                driver.quit()
                if LOGGER_OK:
                    finalizar_logs("¡CITA CONFIRMADA!")
                return resultado
            if "No hay" in driver.page_source and "horas" in driver.page_source:
                log("❌ No hay citas")
                if LOGGER_OK:
                    log_warning("No hay citas disponibles", paso_actual)
                resultado["motivo"] = "no_hay_citas"
                capturar(driver, "no_hay_citas")
                driver.quit()
                if LOGGER_OK:
                    finalizar_logs("No hay citas disponibles")
                return resultado
            time.sleep(1)
        
        log("❌ No se confirmó")
        if LOGGER_OK:
            log_error("No se encontró confirmación", paso_actual)
        resultado["motivo"] = "no_confirmacion"
        capturar(driver, "no_confirmacion")
        driver.quit()
        if LOGGER_OK:
            finalizar_logs("No se confirmó la cita")
        return resultado
        
    except Exception as e:
        log(f"❌ Error: {e}")
        if LOGGER_OK:
            log_error(f"Error: {str(e)[:100]}", paso_actual)
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
        log_info(f"Iniciando agendamiento para usuario {usuario_id}")
    
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
                log_warning("No hay clientes pendientes")
            return []
        
        log(f"📋 Clientes: {len(clientes)}")
        if LOGGER_OK:
            log_info(f"Clientes a procesar: {len(clientes)}")
        
        resultados = []
        for cliente in clientes:
            log(f"\n🔄 Procesando: {cliente.nombre}")
            if LOGGER_OK:
                log_info(f"Procesando: {cliente.nombre}")
            
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
                    log_success(f"{cliente.nombre} - CITA RESERVADA")
            else:
                log(f"❌ {cliente.nombre} - {resultado['motivo']}")
                if LOGGER_OK:
                    log_error(f"{cliente.nombre} - {resultado['motivo']}")
            
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