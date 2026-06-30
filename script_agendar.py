import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Importar logger
from logger import log_info, log_success, log_warning, log_error, finalizar_logs, limpiar_logs

def log(mensaje):
    """Función para logs en consola"""
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
    log_info(f"Esperando: {nombre}", paso)
    while True:
        for selector in selectores:
            try:
                elemento = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(0.5)
                elemento.click()
                log(f"✅ Click: {nombre}")
                log_success(f"Click: {nombre}", paso)
                return True
            except:
                continue
        time.sleep(1)

def esperar_texto(driver, texto, paso=None):
    log(f"⏳ Esperando texto: '{texto}'...")
    log_info(f"Esperando texto: '{texto}'", paso)
    while texto not in driver.page_source:
        time.sleep(1)
    log(f"✅ Texto encontrado: '{texto}'")
    log_success(f"Texto encontrado: '{texto}'", paso)

def esperar_requirejs(driver, paso=None):
    log("⏳ Esperando RequireJS...")
    log_info("Esperando que cargue RequireJS...", paso)
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
                log_success("RequireJS cargado correctamente", paso)
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
        log_info("📌 PASO 1: Cargando página principal...", paso_actual)
        url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
        driver.get(url)
        esperar_texto(driver, "Servicios consulares", paso_actual)
        log_success("✅ Página cargada correctamente", paso_actual)
        paso_actual += 1
        
        if verificar_block_cloudflare(driver):
            log_error("❌ CLOUDFLARE BLOQUEA", paso_actual)
            resultado["motivo"] = "cloudflare_block"
            capturar(driver, "cloudflare_block")
            driver.quit()
            finalizar_logs("Bloqueado por Cloudflare")
            return resultado
        
        # PASO 2: Cookies
        log_info("📌 PASO 2: Aceptando cookies...", paso_actual)
        selectores_cookies = [
            "//input[@value='Aceptar']",
            "//button[contains(text(), 'Aceptar')]",
            "//button[contains(text(), 'Aceptar cookies')]",
            "//button[contains(text(), 'Entendido')]",
        ]
        esperar_y_clickear(driver, selectores_cookies, "cookies", paso_actual)
        log_success("✅ Cookies aceptadas", paso_actual)
        paso_actual += 1
        
        # PASO 3: RFX
        log_info("📌 PASO 3: Buscando enlace RFX...", paso_actual)
        selectores_rfx = [
            "//a[contains(text(), 'Reservar cita de visados RFX')]",
            "//a[contains(text(), 'Reservar cita de visados')]",
            "//a[contains(@href, 'citaconsular.es')]",
        ]
        esperar_y_clickear(driver, selectores_rfx, "RFX", paso_actual)
        log_success("✅ Enlace RFX encontrado y clickeado", paso_actual)
        paso_actual += 1
        
        # PASO 4: Nueva ventana + Alerta
        log_info("📌 PASO 4: Nueva ventana y alerta...", paso_actual)
        while len(driver.window_handles) < 2:
            time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        log_success("✅ Nueva ventana abierta", paso_actual)
        
        log_info("⏳ Esperando alerta Welcome/Bienvenido...", paso_actual)
        while True:
            try:
                alerta = driver.switch_to.alert
                log_success(f"✅ Alerta detectada: {alerta.text}", paso_actual)
                alerta.accept()
                log_success("✅ Alerta aceptada", paso_actual)
                break
            except:
                time.sleep(1)
        
        while "citaconsular.es" not in driver.current_url:
            time.sleep(1)
        log_success(f"✅ URL cargada: {driver.current_url}", paso_actual)
        paso_actual += 1
        
        # PASO 5: Continuar
        log_info("📌 PASO 5: Buscando botón Continuar...", paso_actual)
        selectores_continuar = [
            "//button[contains(text(), 'Continuar')]",
            "//button[contains(text(), 'Continue')]",
            "//input[@value='Continuar']",
            "//*[contains(@class, 'clsDivContinueButton')]",
        ]
        esperar_y_clickear(driver, selectores_continuar, "Continuar", paso_actual)
        log_success("✅ Click en Continuar", paso_actual)
        paso_actual += 1
        
        # PASO 6: Horarios
        log_info("📌 PASO 6: Buscando horarios...", paso_actual)
        esperar_requirejs(driver, paso_actual)
        
        log_info("⏳ Esperando 5 segundos para estabilizar...", paso_actual)
        time.sleep(5)
        
        pagina = driver.page_source
        if "No hay horas disponibles" in pagina or "No hay citas disponibles" in pagina:
            log_warning("❌ No hay citas disponibles", paso_actual)
            resultado["motivo"] = "no_hay_citas"
            capturar(driver, "no_hay_citas")
            driver.quit()
            finalizar_logs("No hay citas disponibles")
            return resultado
        
        horarios = driver.find_elements(By.CSS_SELECTOR, ".clsDivDatetimeSlot")
        if len(horarios) == 0:
            horarios = driver.find_elements(By.XPATH, "//*[contains(text(), ':') and (contains(text(), '8') or contains(text(), '9') or contains(text(), '10'))]")
        
        horarios_filtrados = []
        for h in horarios:
            texto = h.text.strip()
            if "No hay" not in texto and "horas" not in texto and "disponibles" not in texto:
                if texto and any(str(i) in texto for i in range(8, 21)):
                    horarios_filtrados.append(h)
        horarios = horarios_filtrados
        
        if len(horarios) > 0:
            log_success(f"✅ Horarios encontrados: {len(horarios)}", paso_actual)
            for i, h in enumerate(horarios[:5]):
                texto = h.text.strip()
                if texto:
                    log_info(f"   {i+1}. {texto}", paso_actual)
            
            log_info("⏳ Seleccionando el primero...", paso_actual)
            try:
                horarios[0].click()
                log_success("✅ Horario seleccionado", paso_actual)
            except:
                driver.execute_script("arguments[0].click();", horarios[0])
                log_success("✅ Horario seleccionado (JavaScript)", paso_actual)
        else:
            log_warning("❌ No se encontraron horarios", paso_actual)
            resultado["motivo"] = "no_hay_horarios"
            capturar(driver, "no_hay_horarios")
            driver.quit()
            finalizar_logs("No hay horarios disponibles")
            return resultado
        
        paso_actual += 1
        
        # PASO 7: Datos
        log_info("📌 PASO 7: Rellenando datos...", paso_actual)
        
        inputs = []
        while len(inputs) == 0:
            inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
            time.sleep(1)
        log_success(f"✅ Formulario cargado ({len(inputs)} campos)", paso_actual)
        
        # Buscar pasaporte
        campo_pasaporte = None
        try:
            label = driver.find_element(By.XPATH, "//label[contains(text(), 'Pasaporte') or contains(text(), 'pasaporte') or contains(text(), 'N°') or contains(text(), 'Nº')]")
            campo_pasaporte = driver.find_element(By.XPATH, f"//label[contains(text(), 'Pasaporte') or contains(text(), 'pasaporte') or contains(text(), 'N°') or contains(text(), 'Nº')]/following::input[1]")
            log_success("✅ Pasaporte por LABEL", paso_actual)
        except:
            pass
        
        if campo_pasaporte is None:
            try:
                campo_pasaporte = driver.find_element(By.XPATH, "//input[@placeholder='Pasaporte' or contains(@placeholder, 'pasaporte')]")
                log_success("✅ Pasaporte por PLACEHOLDER", paso_actual)
            except:
                pass
        
        if campo_pasaporte is None:
            inputs_local = driver.find_elements(By.XPATH, "//input[@type='text']")
            if len(inputs_local) >= 2:
                campo_pasaporte = inputs_local[1]
                log_success("✅ Pasaporte como SEGUNDO campo", paso_actual)
            elif len(inputs_local) >= 1:
                campo_pasaporte = inputs_local[0]
                log_warning("⚠️ Usando PRIMER campo como pasaporte", paso_actual)
        
        if campo_pasaporte:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_pasaporte)
                time.sleep(0.5)
                campo_pasaporte.click()
                time.sleep(0.5)
                campo_pasaporte.clear()
                campo_pasaporte.send_keys(cliente["pasaporte"])
                log_success(f"✅ Pasaporte: {cliente['pasaporte']}", paso_actual)
            except:
                driver.execute_script("arguments[0].value = arguments[1];", campo_pasaporte, cliente["pasaporte"])
                log_success(f"✅ Pasaporte (JS): {cliente['pasaporte']}", paso_actual)
        else:
            log_error("❌ No se encontró campo de pasaporte", paso_actual)
        
        # Buscar contraseña
        campo_password = None
        try:
            label = driver.find_element(By.XPATH, "//label[contains(text(), 'Contraseña') or contains(text(), 'contraseña') or contains(text(), 'Password')]")
            campo_password = driver.find_element(By.XPATH, f"//label[contains(text(), 'Contraseña') or contains(text(), 'contraseña') or contains(text(), 'Password')]/following::input[1]")
            log_success("✅ Contraseña por LABEL", paso_actual)
        except:
            pass
        
        if campo_password is None:
            try:
                campo_password = driver.find_element(By.XPATH, "//input[@placeholder='Contraseña' or contains(@placeholder, 'contraseña')]")
                log_success("✅ Contraseña por PLACEHOLDER", paso_actual)
            except:
                pass
        
        if campo_password is None:
            try:
                campo_password = driver.find_element(By.XPATH, "//input[@type='password']")
                log_success("✅ Contraseña por tipo password", paso_actual)
            except:
                pass
        
        if campo_password:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_password)
                time.sleep(0.5)
                campo_password.click()
                time.sleep(0.5)
                campo_password.clear()
                campo_password.send_keys(cliente["contrasena"])
                log_success("✅ Contraseña ingresada", paso_actual)
            except:
                driver.execute_script("arguments[0].value = arguments[1];", campo_password, cliente["contrasena"])
                log_success("✅ Contraseña (JS)", paso_actual)
        else:
            log_error("❌ No se encontró campo de contraseña", paso_actual)
        
        paso_actual += 1
        
        # PASO 8: Confirmar
        log_info("📌 PASO 8: Confirmando...", paso_actual)
        selectores_confirmar = [
            "//button[contains(text(), 'Confirmar')]",
            "//button[contains(text(), 'Confirm')]",
            "//input[@value='Confirmar']",
            "//button[contains(@class, 'confirm')]",
        ]
        esperar_y_clickear(driver, selectores_confirmar, "Confirmar", paso_actual)
        log_success("✅ Click en Confirmar", paso_actual)
        paso_actual += 1
        
        # PASO 9: Resultado
        log_info("📌 PASO 9: Verificando resultado...", paso_actual)
        for _ in range(30):
            if "Su reserva se ha realizado con éxito" in driver.page_source:
                log_success("🎉 CITA CONFIRMADA!", paso_actual)
                resultado["exito"] = True
                resultado["motivo"] = "cita_confirmada"
                capturar(driver, "cita_confirmada")
                driver.quit()
                finalizar_logs("¡CITA CONFIRMADA!")
                return resultado
            if "No hay" in driver.page_source and "horas" in driver.page_source:
                log_warning("❌ No hay citas", paso_actual)
                resultado["motivo"] = "no_hay_citas"
                capturar(driver, "no_hay_citas")
                driver.quit()
                finalizar_logs("No hay citas disponibles")
                return resultado
            time.sleep(1)
        
        log_warning("❌ No se confirmó", paso_actual)
        resultado["motivo"] = "no_confirmacion"
        capturar(driver, "no_confirmacion")
        driver.quit()
        finalizar_logs("No se confirmó la cita")
        return resultado
        
    except Exception as e:
        log_error(f"❌ Error: {e}", paso_actual)
        resultado["motivo"] = f"error: {str(e)[:100]}"
        try:
            capturar(driver, "error")
        except:
            pass
        driver.quit()
        finalizar_logs(f"Error: {str(e)[:100]}")
        return resultado

def reservar_citas_para_usuario(usuario_id):
    """Función que llama Render desde app.py"""
    log(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
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
            log_warning("No hay clientes pendientes")
            return []
        
        log(f"📋 Clientes: {len(clientes)}")
        log_info(f"Clientes a procesar: {len(clientes)}")
        resultados = []
        
        for cliente in clientes:
            log(f"\n🔄 Procesando: {cliente.nombre}")
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
                log_success(f"{cliente.nombre} - CITA RESERVADA")
            else:
                log(f"❌ {cliente.nombre} - {resultado['motivo']}")
                log_error(f"{cliente.nombre} - {resultado['motivo']}")
            
            resultados.append(resultado)
            time.sleep(5)
        
        log("\n🏁 Proceso completado")
        log_success("🏁 Proceso completado")
        return resultados

if __name__ == "__main__":
    cliente = {
        "nombre": "Prueba Test",
        "pasaporte": "N123456",
        "contrasena": "tu_contraseña_real"
    }
    reservar_cita(cliente)