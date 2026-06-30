from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 2FA
    codigo_2fa = db.Column(db.String(6), nullable=True)
    codigo_2fa_expiracion = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    clientes = db.relationship('Cliente', backref='usuario', lazy=True)
    dispositivos = db.relationship('Dispositivo', backref='usuario', lazy=True)
    configuraciones = db.relationship('Configuracion', backref='usuario', uselist=False)
    historial = db.relationship('Historial', backref='usuario', lazy=True)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    pasaporte = db.Column(db.String(20), nullable=False)
    contrasena_cita = db.Column(db.String(50), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
    cita_reservada = db.Column(db.Boolean, default=False)
    fecha_cita = db.Column(db.DateTime, nullable=True)
    comprobante = db.Column(db.String(200), nullable=True)

class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    device_id = db.Column(db.String(64), unique=True, nullable=False)
    nombre_dispositivo = db.Column(db.String(100), default="Dispositivo desconocido")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_uso = db.Column(db.DateTime, default=datetime.utcnow)
    expira = db.Column(db.DateTime)

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    dias_semana = db.Column(db.String(100), default="lunes,martes,miercoles,jueves,viernes")
    hora_inicio = db.Column(db.String(5), default="08:00")
    hora_fin = db.Column(db.String(5), default="20:00")
    intervalo_minutos = db.Column(db.Integer, default=5)
    auto_agendar = db.Column(db.Boolean, default=False)

class Historial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    fecha_intento = db.Column(db.DateTime, default=datetime.utcnow)
    exito = db.Column(db.Boolean, default=False)
    mensaje = db.Column(db.String(200))
    comprobante = db.Column(db.String(200), nullable=True)