# captcha_solver.py
import time
import requests
import json

# ============================================================
# CONFIGURACIÓN - REEMPLAZA CON TUS VALORES
# ============================================================

# OBTÉN TU API KEY EN: https://2captcha.com/
API_KEY_2CAPTCHA = "TU_API_KEY_AQUI"

# SITEKEY DE CLOUDFLARE (EXTRAÍDO DE LA PÁGINA)
SITEKEY_CLOUDFLARE = "0x4AAAAAAAAjq6WYeRDKmebM"


# ============================================================
# FUNCIONES PARA RESOLVER CLOUDFLARE TURNSTILE
# ============================================================

def crear_tarea_turnstile(url_actual):
    """
    Crea una tarea en 2Captcha para resolver Cloudflare Turnstile
    """
    payload = {
        "clientKey": API_KEY_2CAPTCHA,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": url_actual,
            "websiteKey": SITEKEY_CLOUDFLARE
        }
    }
    
    try:
        response = requests.post(
            "https://api.2captcha.com/createTask",
            json=payload,
            timeout=30
        )
        resultado = response.json()
        
        if resultado.get("errorId") == 0:
            task_id = resultado.get("taskId")
            print(f"✅ Tarea creada: {task_id}")
            return task_id
        else:
            print(f"❌ Error: {resultado.get('errorDescription')}")
            return None
            
    except Exception as e:
        print(f"❌ Error al crear tarea: {e}")
        return None


def obtener_resultado_tarea(task_id):
    """
    Obtiene el resultado de una tarea de 2Captcha
    """
    payload = {
        "clientKey": API_KEY_2CAPTCHA,
        "taskId": task_id
    }
    
    intentos = 0
    max_intentos = 30  # 30 intentos * 2 segundos = 60 segundos máximo
    
    while intentos < max_intentos:
        try:
            response = requests.post(
                "https://api.2captcha.com/getTaskResult",
                json=payload,
                timeout=30
            )
            resultado = response.json()
            
            if resultado.get("status") == "ready":
                token = resultado.get("solution", {}).get("token")
                print(f"✅ Token obtenido: {token[:30]}...")
                return token
            elif resultado.get("status") == "processing":
                print(f"⏳ Procesando... intento {intentos+1}/{max_intentos}")
                time.sleep(2)
                intentos += 1
            else:
                print(f"❌ Error: {resultado}")
                return None
                
        except Exception as e:
            print(f"❌ Error al obtener resultado: {e}")
            return None
    
    print("❌ Timeout: No se pudo obtener el token")
    return None


def resolver_captcha(url_actual):
    """
    Función principal: resuelve el captcha y devuelve el token
    """
    print("🔐 Iniciando resolución de captcha con 2Captcha...")
    print(f"📍 URL: {url_actual}")
    
    # 1. Crear la tarea
    task_id = crear_tarea_turnstile(url_actual)
    if not task_id:
        return None
    
    # 2. Obtener el resultado
    token = obtener_resultado_tarea(task_id)
    
    return token


def inyectar_token_en_pagina(pagina, token):
    """
    Inyecta el token en la página de Cloudflare
    """
    try:
        # Inyectar el token en el formulario
        pagina.evaluate(f"""
            // Crear input oculto con el token
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'cf-turnstile-response';
            input.value = '{token}';
            document.body.appendChild(input);
            
            // Buscar cualquier formulario y agregarlo
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {{
                const input2 = document.createElement('input');
                input2.type = 'hidden';
                input2.name = 'cf-turnstile-response';
                input2.value = '{token}';
                form.appendChild(input2);
            }});
            
            // Disparar eventos
            const event = new Event('change', {{ bubbles: true }});
            input.dispatchEvent(event);
        """)
        
        print("✅ Token inyectado en la página")
        
        # Hacer clic en el botón "Continue / Continuar"
        try:
            pagina.click("#idCaptchaButton")
            print("✅ Click en 'Continue / Continuar'")
        except:
            try:
                pagina.click("text=Continue / Continuar")
                print("✅ Click en 'Continue / Continuar'")
            except:
                try:
                    pagina.click("button:has-text('Continuar')")
                    print("✅ Click en 'Continuar'")
                except:
                    print("⚠️ No se encontró el botón, enviando formulario...")
                    try:
                        pagina.evaluate("""
                            document.querySelector('form')?.submit();
                        """)
                        print("✅ Formulario enviado")
                    except:
                        pass
        
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"❌ Error inyectando token: {e}")
        return False


def resolver_captcha_en_pagina(pagina, url_actual):
    """
    Función principal: resuelve el captcha en la página actual
    """
    print("🔐 Iniciando resolución de captcha...")
    
    # 1. Resolver el captcha con 2Captcha
    token = resolver_captcha(url_actual)
    if not token:
        print("❌ No se pudo resolver el captcha")
        return False
    
    # 2. Inyectar el token en la página
    resultado = inyectar_token_en_pagina(pagina, token)
    
    if resultado:
        print("✅ Captcha superado correctamente")
    else:
        print("❌ Falló al inyectar el token")
    
    return resultado