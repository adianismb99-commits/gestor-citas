from playwright.sync_api import sync_playwright
import time
from datetime import datetime

clientes = [
    {
        "nombre": "Juan Perez",
        "pasaporte": "N694481",
        "contrasena": "U2g664Qr7c"
    },
]

def reservar_cita(cliente):
    print(f"\n🔄 Procesando: {cliente['nombre']}")
    
    with sync_playwright() as p:
        # Usar Edge con tiempos de espera más largos
        navegador = p.chromium.launch(
            headless=False,
            channel="msedge"
        )
        pagina = navegador.new_page()
        
        # Aumentar timeout a 60 segundos para páginas lentas
        pagina.set_default_timeout(60000)  # 60 segundos
        
        print("📌 Paso 1: Entrando a la página (esperando hasta 60 segundos)...")
        try:
            pagina.goto(
                "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Servicios-consulares.aspx?scco=Cuba&scd=166&scca=Visados&scs=Visados+Nacionales+-+Visado+de+residencia+de+familiares+de+personas+de+nacionalidad+espa%C3%B1ola",
                wait_until="domcontentloaded",  # No esperar a que carguen todas las imágenes
                timeout=60000
            )
        except Exception as e:
            print(f"   ⚠️ Timeout en carga, pero continuamos...")
        
        # Esperar un poco extra para que la página termine de cargar
        time.sleep(5)
        
        print("📌 Paso 2: Buscando enlace de RFX...")
        try:
            # Esperar a que el enlace esté disponible
            pagina.wait_for_selector("text=Reservar citas de visados RFX", timeout=30000)
            pagina.click("text=Reservar citas de visados RFX")
        except:
            try:
                pagina.click("text=RFX")
            except:
                try:
                    pagina.click("a:has-text('Reservar')")
                except:
                    print("   ⚠️ No se encontró el enlace RFX")
                    navegador.close()
                    return False
        time.sleep(3)
        
        print("📌 Paso 3: Aceptando ventana de bienvenida...")
        try:
            pagina.wait_for_selector("text=Aceptar", timeout=10000)
            pagina.click("text=Aceptar")
        except:
            try:
                pagina.click("button:has-text('Aceptar')")
            except:
                print("   ⚠️ No apareció ventana de bienvenida, continuando...")
        time.sleep(2)
        
        print("📌 Paso 4: Haciendo click en Continuar...")
        try:
            pagina.wait_for_selector("text=Continuar", timeout=10000)
            pagina.click("text=Continuar")
        except:
            try:
                pagina.click("text=Continue")
            except:
                try:
                    pagina.click("button:has-text('Continuar')")
                except:
                    print("   ⚠️ No se encontró botón Continuar")
                    navegador.close()
                    return False
        time.sleep(3)
        
        print("📌 Paso 5: Buscando horarios disponibles...")
        try:
            # Esperar a que cargue la lista de horarios
            time.sleep(5)
            
            # Buscar horarios con diferentes patrones
            horarios = pagina.query_selector_all("text=/[0-9]:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/8:[0-9]{2}/")
            if len(horarios) == 0:
                horarios = pagina.query_selector_all("text=/9:[0-9]{2}/")
            
            if len(horarios) > 0:
                print(f"   ✅ Horarios encontrados: {len(horarios)}")
                horarios[0].click()
                print("   ✅ Seleccionado el primer horario disponible")
            else:
                print("   ❌ NO HAY CITAS DISPONIBLES")
                pagina.screenshot(path=f"no_citas_{cliente['pasaporte']}.png")
                navegador.close()
                return False
        except Exception as e:
            print(f"   ⚠️ Error buscando horarios: {e}")
            pagina.screenshot(path=f"error_horarios_{cliente['pasaporte']}.png")
            navegador.close()
            return False
        
        time.sleep(3)
        
        print("📌 Paso 6: Rellenando pasaporte y contraseña...")
        try:
            # Esperar a que los inputs estén disponibles
            time.sleep(2)
            
            inputs_text = pagina.query_selector_all("input[type='text']")
            if len(inputs_text) >= 1:
                inputs_text[0].fill(cliente["pasaporte"])
                print(f"   ✅ Pasaporte ingresado: {cliente['pasaporte']}")
            else:
                print("   ⚠️ No se encontró campo de pasaporte")
            
            password_input = pagina.query_selector("input[type='password']")
            if password_input:
                password_input.fill(cliente["contrasena"])
                print("   ✅ Contraseña ingresada")
            else:
                if len(inputs_text) >= 2:
                    inputs_text[1].fill(cliente["contrasena"])
                    print("   ✅ Contraseña ingresada (como texto)")
            
            time.sleep(1)
            
            try:
                pagina.click("text=Confirmar")
            except:
                try:
                    pagina.click("button:has-text('Confirmar')")
                except:
                    pagina.click("input[value='Confirmar']")
            print("   ✅ Click en Confirmar")
        except Exception as e:
            print(f"   ⚠️ Error en formulario: {e}")
            pagina.screenshot(path=f"error_formulario_{cliente['pasaporte']}.png")
            navegador.close()
            return False
        
        time.sleep(5)
        
        print("📌 Paso 7: Verificando confirmación...")
        try:
            # Esperar mensaje de éxito (hasta 15 segundos)
            pagina.wait_for_selector("text=Su reserva se ha realizado con éxito", timeout=15000)
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo = f"cita_{cliente['pasaporte']}_{fecha}.png"
            pagina.screenshot(path=archivo, full_page=True)
            print(f"🎉 ¡CITA CONFIRMADA para {cliente['nombre']}!")
            print(f"📸 Captura guardada: {archivo}")
            navegador.close()
            return True
        except:
            print(f"❌ No se confirmó la cita para {cliente['nombre']}")
            pagina.screenshot(path=f"error_confirmacion_{cliente['pasaporte']}.png")
            navegador.close()
            return False

print("=" * 50)
print("      SCRIPT DE RESERVA DE CITAS")
print("=" * 50)

for cliente in clientes:
    exito = reservar_cita(cliente)
    if exito:
        print(f"✅ {cliente['nombre']} - CITA RESERVADA")
    else:
        print(f"❌ {cliente['nombre']} - SIN CITA")
    time.sleep(5)

print("\n🏁 PROCESO FINALIZADO")