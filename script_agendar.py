import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

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

def esperar_y_clickear(driver, selectores, nombre="elemento"):
    log(f"⏳ Esperando: {nombre}...")
    while True:
        for selector in selectores:
            try:
                elemento = driver.find_element(By.XPATH, selector)
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(0.5)
                elemento.click()
                log(f"✅ Click: {nombre}")
                return True
            except:
                continue
        time.sleep(1)

def esperar_texto(driver, texto):
    log(f"⏳ Esperando texto: '{texto}'...")
    while texto not in driver.page_source:
        time.sleep(1)
    log(f"✅ Texto encontrado: '{texto}'")

def esperar_requirejs(driver):
    log("⏳ Esperando RequireJS...")
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
    
    # En Render usamos Chrome, no Edge
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    
    # Usar ChromeDriver
    from webdriver_manager.chrome import ChromeDriverManager
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    resultado = {
        "exito": False,
        "motivo": "",
        "captura": None
    }
    
    try:
        # PASO 1: Cargar página
        log("📌 Cargando página principal...")
        url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
        driver.get(url)
        esperar_texto(driver, "Servicios consulares")
        log("✅ Página cargada")
        
        if verificar_block_cloudflare(driver):
            log("❌ CLOUDFLARE BLOQUEA")
            resultado["motivo"] = "cloudflare_block"
            capturar(driver, "cloudflare_block")
            driver.quit()
            return resultado
        
        # PASO 2: Cookies
        log("📌 Aceptando cookies...")
        selectores_cookies = [
            "//input[@value='Aceptar']",
            "//button[contains(text(), 'Aceptar')]",
            "//button[contains(text(), 'Aceptar cookies')]",
            "//button[contains(text(), 'Entendido')]",
        ]
        esperar_y_clickear(driver, selectores_cookies, "cookies")
        
        # PASO 3: RFX
        log("📌 Buscando RFX...")
        selectores_rfx = [
            "//a[contains(text(), 'Reservar cita de visados RFX')]",
            "//a[contains(text(), 'Reservar cita de visados')]",
            "//a[contains(@href, 'citaconsular.es')]",
        ]
        esperar_y_clickear(driver, selectores_rfx, "RFX")
        
        # PASO 4: Nueva ventana + Alerta
        log("📌 Nueva ventana...")
        while len(driver.window_handles) < 2:
            time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        log("✅ Nueva ventana abierta")
        
        log("⏳ Esperando alerta Welcome/Bienvenido...")
        while True:
            try:
                alerta = driver.switch_to.alert
                log(f"✅ Alerta detectada: {alerta.text}")
                alerta.accept()
                log("✅ Alerta aceptada")
                break
            except:
                time.sleep(1)
        
        log("⏳ Esperando URL de citaconsular.es...")
        while "citaconsular.es" not in driver.current_url:
            time.sleep(1)
        log(f"✅ URL: {driver.current_url}")
        
        # PASO 5: Continuar
        log("📌 Continuar...")
        selectores_continuar = [
            "//button[contains(text(), 'Continuar')]",
            "//button[contains(text(), 'Continue')]",
            "//input[@value='Continuar']",
            "//*[contains(@class, 'clsDivContinueButton')]",
        ]
        esperar_y_clickear(driver, selectores_continuar, "Continuar")
        
        # PASO 6: Horarios
        log("📌 Buscando horarios...")
        esperar_requirejs(driver)
        log("⏳ Esperando 5 segundos para estabilizar...")
        time.sleep(5)
        
        pagina = driver.page_source
        if "No hay horas disponibles" in pagina or "No hay citas disponibles" in pagina:
            log("❌ No hay citas disponibles")
            resultado["motivo"] = "no_hay_citas"
            capturar(driver, "no_hay_citas")
            driver.quit()
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
            log(f"✅ Horarios encontrados: {len(horarios)}")
            for i, h in enumerate(horarios[:5]):
                texto = h.text.strip()
                if texto:
                    log(f"   {i+1}. {texto}")
            
            log("⏳ Seleccionando el primero...")
            try:
                horarios[0].click()
                log("✅ Horario seleccionado")
            except:
                driver.execute_script("arguments[0].click();", horarios[0])
                log("✅ Horario seleccionado (JavaScript)")
        else:
            log("❌ No se encontraron horarios")
            resultado["motivo"] = "no_hay_horarios"
            capturar(driver, "no_hay_horarios")
            driver.quit()
            return resultado
        
        # PASO 7: Datos
        log("📌 Rellenando datos...")
        inputs = []
        while len(inputs) == 0:
            inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
            time.sleep(1)
        log(f"✅ Formulario cargado ({len(inputs)} campos)")
        
        # Buscar pasaporte
        campo_pasaporte = None
        try:
            label = driver.find_element(By.XPATH, "//label[contains(text(), 'Pasaporte') or contains(text(), 'pasaporte') or contains(text(), 'N°') or contains(text(), 'Nº')]")
            campo_pasaporte = driver.find_element(By.XPATH, f"//label[contains(text(), 'Pasaporte') or contains(text(), 'pasaporte') or contains(text(), 'N°') or contains(text(), 'Nº')]/following::input[1]")
            log("✅ Pasaporte por LABEL")
        except:
            pass
        
        if campo_pasaporte is None:
            try:
                campo_pasaporte = driver.find_element(By.XPATH, "//input[@placeholder='Pasaporte' or contains(@placeholder, 'pasaporte')]")
                log("✅ Pasaporte por PLACEHOLDER")
            except:
                pass
        
        if campo_pasaporte is None:
            inputs_local = driver.find_elements(By.XPATH, "//input[@type='text']")
            if len(inputs_local) >= 2:
                campo_pasaporte = inputs_local[1]
                log("✅ Pasaporte como SEGUNDO campo")
            elif len(inputs_local) >= 1:
                campo_pasaporte = inputs_local[0]
                log("⚠️ Usando PRIMER campo como pasaporte")
        
        if campo_pasaporte:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_pasaporte)
                time.sleep(0.5)
                campo_pasaporte.click()
                time.sleep(0.5)
                campo_pasaporte.clear()
                campo_pasaporte.send_keys(cliente["pasaporte"])
                log(f"✅ Pasaporte: {cliente['pasaporte']}")
            except:
                driver.execute_script("arguments[0].value = arguments[1];", campo_pasaporte, cliente["pasaporte"])
                log(f"✅ Pasaporte (JS): {cliente['pasaporte']}")
        else:
            log("❌ No se encontró campo de pasaporte")
        
        # Buscar contraseña
        campo_password = None
        try:
            label = driver.find_element(By.XPATH, "//label[contains(text(), 'Contraseña') or contains(text(), 'contraseña') or contains(text(), 'Password')]")
            campo_password = driver.find_element(By.XPATH, f"//label[contains(text(), 'Contraseña') or contains(text(), 'contraseña') or contains(text(), 'Password')]/following::input[1]")
            log("✅ Contraseña por LABEL")
        except:
            pass
        
        if campo_password is None:
            try:
                campo_password = driver.find_element(By.XPATH, "//input[@placeholder='Contraseña' or contains(@placeholder, 'contraseña')]")
                log("✅ Contraseña por PLACEHOLDER")
            except:
                pass
        
        if campo_password is None:
            try:
                campo_password = driver.find_element(By.XPATH, "//input[@type='password']")
                log("✅ Contraseña por tipo password")
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
                log("✅ Contraseña ingresada")
            except:
                driver.execute_script("arguments[0].value = arguments[1];", campo_password, cliente["contrasena"])
                log("✅ Contraseña (JS)")
        else:
            log("❌ No se encontró campo de contraseña")
        
        # PASO 8: Confirmar
        log("📌 Confirmando...")
        selectores_confirmar = [
            "//button[contains(text(), 'Confirmar')]",
            "//button[contains(text(), 'Confirm')]",
            "//input[@value='Confirmar']",
            "//button[contains(@class, 'confirm')]",
        ]
        esperar_y_clickear(driver, selectores_confirmar, "Confirmar")
        
        # PASO 9: Resultado
        log("📌 Verificando resultado...")
        for _ in range(30):
            if "Su reserva se ha realizado con éxito" in driver.page_source:
                log("🎉 CITA CONFIRMADA!")
                resultado["exito"] = True
                resultado["motivo"] = "cita_confirmada"
                capturar(driver, "cita_confirmada")
                driver.quit()
                return resultado
            if "No hay" in driver.page_source and "horas" in driver.page_source:
                log("❌ No hay citas")
                resultado["motivo"] = "no_hay_citas"
                capturar(driver, "no_hay_citas")
                driver.quit()
                return resultado
            time.sleep(1)
        
        log("❌ No se confirmó")
        resultado["motivo"] = "no_confirmacion"
        capturar(driver, "no_confirmacion")
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
        return resultado

def reservar_citas_para_usuario(usuario_id):
    """Función que llama Render desde app.py"""
    log(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    
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
        
        log(f"📋 Clientes: {len(clientes)}")
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