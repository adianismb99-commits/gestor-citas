from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Usuario, Cliente, Dispositivo, Configuracion, Historial
from datetime import datetime, timedelta
import bcrypt
import random
import string
import uuid
import hashlib
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-cambia-esto')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///citas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ========================================
# FUNCIONES AUXILIARES
# ========================================

def generar_codigo_2fa():
    """Genera un código de 6 dígitos aleatorio"""
    return ''.join(random.choices(string.digits, k=6))

def generar_device_id():
    """Genera un ID único para el dispositivo"""
    datos = f"{datetime.now()}-{uuid.uuid4()}"
    return hashlib.md5(datos.encode()).hexdigest()

def enviar_codigo_por_email(email_destino, codigo):
    """Envía el código 2FA por correo (usando Gmail SMTP)"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        mensaje = MIMEText(f"""
        🔐 Código de verificación

        Tu código de 6 dígitos es: {codigo}

        Este código expira en 5 minutos.

        Si no solicitaste este código, ignora este correo.
        """)
        mensaje['Subject'] = '🔐 Código de verificación - Gestor de Citas'
        mensaje['From'] = os.getenv('EMAIL_FROM', 'tu-email@gmail.com')
        mensaje['To'] = email_destino
        
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(
                os.getenv('EMAIL_FROM', 'tu-email@gmail.com'),
                os.getenv('EMAIL_PASSWORD', 'tu-contrasena')
            )
            servidor.send_message(mensaje)
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

def registrar_dispositivo(usuario_id, device_id):
    """Registra un nuevo dispositivo confiable"""
    expira = datetime.now() + timedelta(days=30)
    dispositivo = Dispositivo(
        usuario_id=usuario_id,
        device_id=device_id,
        expira=expira
    )
    db.session.add(dispositivo)
    db.session.commit()
    return dispositivo

def actualizar_dispositivo(usuario_id, device_id):
    """Actualiza el último uso de un dispositivo"""
    dispositivo = Dispositivo.query.filter_by(
        usuario_id=usuario_id,
        device_id=device_id
    ).first()
    if dispositivo:
        dispositivo.ultimo_uso = datetime.now()
        db.session.commit()

def dispositivo_es_confiable(usuario_id, device_id):
    """Verifica si un dispositivo es confiable"""
    if not device_id:
        return False
    
    dispositivo = Dispositivo.query.filter_by(
        usuario_id=usuario_id,
        device_id=device_id
    ).first()
    
    if not dispositivo:
        return False
    
    if dispositivo.expira < datetime.now():
        return False
    
    return True

# ========================================
# RUTAS
# ========================================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if Usuario.query.filter_by(username=username).first():
            flash('El usuario ya existe')
            return redirect(url_for('registro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado')
            return redirect(url_for('registro'))
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        nuevo_usuario = Usuario(
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado correctamente. Inicia sesión.')
        return redirect(url_for('login'))
    
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        device_id_actual = request.cookies.get('device_id')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if not usuario:
            flash('Usuario o contraseña incorrectos')
            return redirect(url_for('login'))
        
        if not bcrypt.checkpw(password.encode('utf-8'), usuario.password_hash.encode('utf-8')):
            flash('Usuario o contraseña incorrectos')
            return redirect(url_for('login'))
        
        # Verificar si el dispositivo es confiable
        if dispositivo_es_confiable(usuario.id, device_id_actual):
            # Dispositivo confiable → iniciar sesión directamente
            login_user(usuario)
            actualizar_dispositivo(usuario.id, device_id_actual)
            return redirect(url_for('dashboard'))
        # 🔥 MODO PRUEBA - Saltar 2FA si el usuario se llama "admin"
        if username == "admin":
            login_user(usuario)
            return redirect(url_for('dashboard'))
        
        # Dispositivo no confiable → pedir 2FA
        codigo = generar_codigo_2fa()
        usuario.codigo_2fa = codigo
        usuario.codigo_2fa_expiracion = datetime.now() + timedelta(minutes=5)
        db.session.commit()
        
        # Enviar código por email
        enviar_codigo_por_email(usuario.email, codigo)
        
        session['user_id_2fa'] = usuario.id
        
        flash(f'📧 Se ha enviado un código de verificación a {usuario.email}')
        return redirect(url_for('verificar_2fa'))
    
    return render_template('login.html')

@app.route('/verificar_2fa', methods=['GET', 'POST'])
def verificar_2fa():
    user_id = session.get('user_id_2fa')
    if not user_id:
        flash('Sesión expirada, inicia sesión de nuevo')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        codigo_ingresado = request.form['codigo']
        
        if not usuario.codigo_2fa:
            flash('No hay código activo. Solicita uno nuevo.')
            return redirect(url_for('verificar_2fa'))
        
        if datetime.now() > usuario.codigo_2fa_expiracion:
            flash('El código ha expirado. Solicita uno nuevo.')
            return redirect(url_for('verificar_2fa'))
        
        if usuario.codigo_2fa != codigo_ingresado:
            flash('Código incorrecto')
            return redirect(url_for('verificar_2fa'))
        
        # ✅ Código correcto
        usuario.codigo_2fa = None
        usuario.codigo_2fa_expiracion = None
        db.session.commit()
        
        # Crear dispositivo confiable
        device_id = generar_device_id()
        registrar_dispositivo(usuario.id, device_id)
        
        # Iniciar sesión
        login_user(usuario)
        
        response = redirect(url_for('dashboard'))
        response.set_cookie(
            'device_id',
            device_id,
            max_age=60*60*24*30,  # 30 días
            httponly=True,
            samesite='Lax'
        )
        
        flash('✅ Dispositivo verificado correctamente')
        return response
    
    return render_template('verificar_2fa.html', email=usuario.email)

@app.route('/reenviar_codigo')
def reenviar_codigo():
    user_id = session.get('user_id_2fa')
    if not user_id:
        flash('Sesión expirada')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    codigo = generar_codigo_2fa()
    usuario.codigo_2fa = codigo
    usuario.codigo_2fa_expiracion = datetime.now() + timedelta(minutes=5)
    db.session.commit()
    
    enviar_codigo_por_email(usuario.email, codigo)
    
    flash('📧 Nuevo código enviado a tu correo')
    return redirect(url_for('verificar_2fa'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    clientes = Cliente.query.filter_by(usuario_id=current_user.id).all()
    config = Configuracion.query.filter_by(usuario_id=current_user.id).first()
    
    # Estadísticas
    total = len(clientes)
    reservadas = len([c for c in clientes if c.cita_reservada])
    pendientes = total - reservadas
    
    return render_template('dashboard.html',
                         clientes=clientes,
                         config=config,
                         total=total,
                         reservadas=reservadas,
                         pendientes=pendientes)

@app.route('/agregar_cliente', methods=['GET', 'POST'])
@login_required
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        pasaporte = request.form['pasaporte']
        contrasena = request.form['contrasena']
        
        nuevo_cliente = Cliente(
            usuario_id=current_user.id,
            nombre=nombre,
            pasaporte=pasaporte,
            contrasena_cita=contrasena
        )
        
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        flash('✅ Cliente agregado correctamente')
        return redirect(url_for('dashboard'))
    
    return render_template('agregar_cliente.html')

@app.route('/eliminar_cliente/<int:cliente_id>')
@login_required
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if cliente.usuario_id != current_user.id:
        flash('No autorizado')
        return redirect(url_for('dashboard'))
    
    db.session.delete(cliente)
    db.session.commit()
    flash('✅ Cliente eliminado')
    return redirect(url_for('dashboard'))

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    config = Configuracion.query.filter_by(usuario_id=current_user.id).first()
    
    if request.method == 'POST':
        dias = request.form.getlist('dias')
        hora_inicio = request.form['hora_inicio']
        hora_fin = request.form['hora_fin']
        intervalo = int(request.form['intervalo'])
        auto_agendar = 'auto_agendar' in request.form
        
        if not config:
            config = Configuracion(usuario_id=current_user.id)
            db.session.add(config)
        
        config.dias_semana = ','.join(dias) if dias else ''
        config.hora_inicio = hora_inicio
        config.hora_fin = hora_fin
        config.intervalo_minutos = intervalo
        config.auto_agendar = auto_agendar
        
        db.session.commit()
        flash('✅ Configuración guardada correctamente')
        return redirect(url_for('dashboard'))
    
    # Preparar días seleccionados
    dias_seleccionados = config.dias_semana.split(',') if config and config.dias_semana else []
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    
    return render_template('configuracion.html',
                         config=config,
                         dias_seleccionados=dias_seleccionados,
                         dias_semana=dias_semana)

@app.route('/agendar_ahora', methods=['POST'])
@login_required
def agendar_ahora():
    from script_agendar import reservar_citas_para_usuario
    
    clientes = Cliente.query.filter_by(
        usuario_id=current_user.id,
        cita_reservada=False
    ).all()
    
    if not clientes:
        return jsonify({
            'success': False,
            'message': 'No tienes clientes pendientes'
        })
    
    # Guardar el ID del usuario antes de iniciar el hilo
    usuario_id = current_user.id
    
    # Ejecutar en hilo separado
    def ejecutar():
        with app.app_context():
            reservar_citas_para_usuario(usuario_id)
    
    hilo = threading.Thread(target=ejecutar)
    hilo.start()
    
    return jsonify({
        'success': True,
        'message': f'🚀 Iniciando agendamiento para {len(clientes)} clientes'
    })

# ========================================
# CREAR BASE DE DATOS
# ========================================

with app.app_context():
    db.create_all()
    print("✅ Base de datos creada correctamente")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)