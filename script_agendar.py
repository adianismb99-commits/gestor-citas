import os
import sys
import time
from datetime import datetime
from models import db, Cliente

from playwright.sync_api import sync_playwright

def log(mensaje):
    print(mensaje)
    sys.stdout.flush()

def capturar_pantalla(pagina, nombre, cliente_pasaporte=""):
    try:
        os.makedirs("static", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"static/paso_{nombre}_{cliente_pasaporte}_{timestamp}.png"
        # Timeout reducido a 10 segundos para evitar bloqueos
        pagina.screenshot(path=archivo, full_page=True, timeout=10000)
        log(f"   📸 Captura guardada: {archivo}")
        return archivo
    except Exception as e:
        log(f"   ⚠️ Error al guardar captura: {e}")
        return None

def aceptar_cookies(pagina, cliente_pasaporte=""):
    log("🍪 Buscando banner de cookies...")
    
    selectores = [
        "text=Aceptar",
        "button:has-text('Aceptar')",
        "text=Entendido",
        "button:has-text('Entendido')",
        "text=Acepto",
        "button:has-text('Acepto')",
        "#cookie-accept",
        ".cookie-accept",
        "button[class*='cookie']",
        "button:has-text('Aceptar todas')",
        "button:has-text('Aceptar cookies')"
    ]
    
    for selector in selectores:
        try:
            boton = pagina.wait_for_selector(selector, timeout=2000)
            if boton:
                boton.click()
                log(f"   ✅ Cookies aceptadas con selector: {selector}")
                time.sleep(1)
                capturar_pantalla(pagina, "01_cookies_aceptadas", cliente_pasaporte)
                return True
        except:
            continue
    
    log("   ⚠️ No se encontró banner de cookies, continuando...")
    return False

def reservar_cita_individual(cliente):
    log(f"📌 Iniciando reserva para {cliente.nombre}...")
    pasaporte = cliente.pasaporte
    
    with sync_playwright() as p:
        # Usar headless="new" para mejor rendimiento
        navegador = p.chromium.launch(
            headless="new",
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pagina = navegador.new_page()
        
        # Reducir timeouts
        pagina.set_default_timeout(30000)
        
        try:
            # PASO 1: Cargar página
            log(f"📌 Entrando a la página...")
            url_visado = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola"
            
            pagina.goto(url_visado, timeout=30000)
            pagina.wait_for_load_state("networkidle", timeout=30000)
            
            log("   ✅ Página cargada")
            capturar_pantalla(pagina, "02_pagina_principal", pasaporte)
            
            # PASO 2: Cookies
            aceptar_cookies(pagina, pasaporte)
            
            # PASO 3: RFX
            log("📌 Buscando enlace RFX...")
            try:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados RFX", timeout=15000)
                log("   ✅ Enlace encontrado")
                capturar_pantalla(pagina, "03_enlace_rfx", pasaporte)
                enlace.click()
                log("   ✅ Click en RFX")
            except:
                enlace = pagina.wait_for_selector("text=Reservar cita de visados", timeout=15000)
                log("   ✅ Enlace encontrado (parcial)")
                enlace.click()
                log("   ✅ Click en RFX (parcial)")
            
            time.sleep(2)
            
            # PASO 4: Nueva ventana
            log("📊 Esperando nueva ventana...")
            
            try:
                with navegador.context.expect_page(timeout=15000) as nueva_pagina_info:
                    # Reintentar clic si es necesario
                    pass
                # Ya debería estar en la nueva página
            except:
                # Si no hay nueva página, navegar directamente
                try:
                    href = enlace.get_attribute('href')
                    if href and "citaconsular" in href:
                        log(f"   🔄 Navegando directamente a: {href}")
                        pagina.goto(href, timeout=30000)
                        log("   ✅ Navegación directa")
                except Exception as e:
                    log(f"   ⚠️ Error en navegación: {e}")
            
            time.sleep(2)
            
            # Obtener páginas
            try:
                paginas = navegador.contexts[0].pages
                if len(paginas) > 1:
                    pagina = paginas[-1]
                    log("   ✅ Cambiado a nueva ventana")
                else:
                    log("   ⚠️ No hay nueva ventana, continuando...")
            except:
                pass
            
            capturar_pantalla(pagina, "04_nueva_ventana", pasaporte)
            
            # PASO 5: Bienvenida
            log("📌 Buscando bienvenida...")
            time.sleep(2)
            
            selectores_bienvenida = [
                "text=Aceptar",
                "button:has-text('Aceptar')",
                "text=Entendido",
                "text=Welcome",
                "button:has-text('Welcome')",
                "button[class*='welcome']"
            ]
            
            for selector in selectores_bienvenida:
                try:
                    boton = pagina.wait_for_selector(selector, timeout=2000)
                    if boton:
                        boton.click()
                        log(f"   ✅ Click en Aceptar (bienvenida)")
                        time.sleep(1)
                        break
                except:
                    continue
            
            capturar_pantalla(pagina, "05_bienvenida", pasaporte)
            
            # PASO 6: Continuar
            log("📌 Buscando Continuar...")
            try:
                continuar = pagina.wait_for_selector("text=Continuar", timeout=5000)
                continuar.click()
                log("   ✅ Click en Continuar")
            except:
                try:
                    continuar = pagina.wait_for_selector("text=Continue", timeout=5000)
                    continuar.click()
                    log("   ✅ Click en Continue")
                except:
                    try:
                        continuar = pagina.wait_for_selector("button:has-text('Continuar')", timeout=5000)
                        continuar.click()
                        log("   ✅ Click en Continuar (genérico)")
                    except:
                        log("   ⚠️ No se encontró Continuar")
                        capturar_pantalla(pagina, "06_error_continuar", pasaporte)
            
            time.sleep(2)
            capturar_pantalla(pagina, "07_despues_continuar", pasaporte)
            
            # PASO 7: Horarios
            log("📌 Buscando horarios...")
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            
            if len(horarios) == 0:
                log("❌ No hay citas disponibles")
                capturar_pantalla(pagina, "08_no_hay_citas", pasaporte)
                cliente.cita_reservada = False
                db.session.commit()
                navegador.close()
                return False, "No hay citas disponibles"
            
            log(f"✅ Horarios: {len(horarios)}")
            horarios[0].click()
            capturar_pantalla(pagina, "09_horario_seleccionado", pasaporte)
            
            time.sleep(2)
            
            # PASO 8: Datos
            log("📌 Rellenando datos...")
            inputs = pagina.query_selector_all("input[type='text']")
            if len(inputs) >= 1:
                inputs[0].fill(cliente.pasaporte)
                log(f"   ✅ Pasaporte: {cliente.pasaporte}")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada")
            elif len(inputs) >= 2:
                inputs[1].fill(cliente.contrasena_cita)
                log("   ✅ Contraseña ingresada (como texto)")
            
            capturar_pantalla(pagina, "10_datos_ingresados", pasaporte)
            
            # PASO 9: Confirmar
            try:
                confirmar = pagina.wait_for_selector("text=Confirmar", timeout=5000)
                confirmar.click()
                log("   ✅ Click en Confirmar")
            except:
                try:
                    confirmar = pagina.wait_for_selector("button:has-text('Confirmar')", timeout=5000)
                    confirmar.click()
                    log("   ✅ Click en Confirmar (genérico)")
                except:
                    log("   ⚠️ No se encontró Confirmar")
                    capturar_pantalla(pagina, "11_error_confirmar", pasaporte)
            
            time.sleep(3)
            
            # PASO 10: Confirmación final
            log("📌 Verificando confirmación...")
            try:
                pagina.wait_for_selector("text=Su reserva se ha realizado con éxito", timeout=10000)
                log("✅ Confirmación encontrada")
                
                fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
                archivo = f"static/cita_{pasaporte}_{fecha}.png"
                pagina.screenshot(path=archivo, full_page=True, timeout=10000)
                
                cliente.cita_reservada = True
                cliente.fecha_cita = datetime.now()
                cliente.comprobante = archivo
                db.session.commit()
                
                log(f"🎉 ¡CITA CONFIRMADA para {cliente.nombre}!")
                navegador.close()
                return True, "Cita reservada exitosamente"
            except:
                log("❌ No se encontró confirmación")
                capturar_pantalla(pagina, "12_error_confirmacion", pasaporte)
                navegador.close()
                return False, "No se encontró confirmación"
                
        except Exception as e:
            log(f"❌ Error: {e}")
            try:
                archivo_error = f"static/error_final_{pasaporte}.png"
                pagina.screenshot(path=archivo_error, full_page=True, timeout=10000)
            except:
                pass
            cliente.cita_reservada = False
            db.session.commit()
            navegador.close()
            return False, str(e)

def reservar_citas_para_usuario(usuario_id):
    log(f"🚀 Iniciando agendamiento para usuario {usuario_id}")
    
    from app import app
    
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
            exito, mensaje = reservar_cita_individual(cliente)
            resultados.append({
                'cliente': cliente.nombre,
                'exito': exito,
                'mensaje': mensaje
            })
            time.sleep(5)
        
        log("\n🏁 Proceso completado")
        return resultados