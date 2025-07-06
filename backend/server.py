#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity
)
from werkzeug.security import check_password_hash
import os
from datetime import timedelta

# Importar el módulo de base de datos
from database import db, Usuario

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'tu_clave_secreta_super_segura')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # El token expira en 1 hora

# Inicializar JWT
jwt = JWTManager(app)

# Ruta de autenticación
@app.route("/api/auth/login", methods=["POST"])
def login():
    # Obtener datos de la petición
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)
    
    # Validar que se enviaron los datos requeridos
    if not username or not password:
        return jsonify({"msg": "Faltan credenciales"}), 400
    
    # Buscar el usuario en la base de datos
    with db.session_scope() as session:
        user = session.query(Usuario).filter(Usuario.nombre == username).first()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if user and check_password_hash(user.clave, password):
            # Crear el token de acceso - asegurarse de que el identity sea una cadena
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                "access_token": access_token,
                "user_id": user.id,
                "username": user.nombre,
                "msg": "Inicio de sesión exitoso"
            }), 200
        
        # Si las credenciales son incorrectas
        return jsonify({"msg": "Usuario o contraseña incorrectos"}), 401

# Ruta protegida de ejemplo
@app.route("/api/protegido", methods=["GET"])
@jwt_required()
def ruta_protegida():
    # Obtener la identidad del token
    current_user_id = get_jwt_identity()
    
    # Aquí podrías obtener más información del usuario desde la base de datos si es necesario
    with db.session_scope() as session:
        user = session.query(Usuario).get(current_user_id)
        if user:
            return jsonify({
                "mensaje": f"¡Acceso concedido! Usuario: {user.nombre}",
                "user_id": user.id,
                "username": user.nombre
            }), 200
    
    return jsonify({"msg": "Usuario no encontrado"}), 404

# Ruta para verificar un token JWT
@app.route("/api/auth/verify", methods=["POST"])
@jwt_required()
def verify_token():
    # Obtener la identidad del token como string
    current_user_id = get_jwt_identity()
    
    # Obtener información adicional del token
    from flask_jwt_extended import get_jwt
    token_data = get_jwt()
    
    # Obtener información del usuario dentro del contexto de la sesión
    with db.session_scope() as session:
        # Convertir el ID a entero si es necesario
        user_id = int(current_user_id) if isinstance(current_user_id, str) and current_user_id.isdigit() else current_user_id
        user = session.query(Usuario).get(user_id)
        
        if not user:
            return jsonify({
                "valid": False,
                "message": "Usuario no encontrado"
            }), 404
            
        # Verificar si el usuario está activo (si el modelo tiene un campo 'activo')
        is_active = getattr(user, 'activo', True)  # Por defecto True si no existe el atributo
        
        # Obtener los datos del usuario que necesitamos antes de salir del contexto de la sesión
        user_data = {
            "id": user.id,
            "username": user.nombre,
            "is_authenticated": True,
            "is_active": bool(is_active)  # Asegurarse de que sea booleano
        }
        
        if not is_active:
            return jsonify({
                "valid": False,
                "message": "Usuario inactivo"
            }), 401
    
    # Calcular tiempo restante de expiración
    from datetime import datetime, timezone
    exp_timestamp = token_data['exp']
    current_timestamp = datetime.now(timezone.utc).timestamp()
    expires_in = int(exp_timestamp - current_timestamp)  # en segundos
    
    # Formatear tiempo restante
    minutes, seconds = divmod(expires_in, 60)
    expires_in_formatted = f"{minutes}m {seconds}s"
    
    # Crear la respuesta final fuera del contexto de la sesión
    return jsonify({
        "valid": True,
        "message": "Token válido",
        "user": user_data,
        "token_info": {
            "issued_at": datetime.fromtimestamp(token_data['iat'], timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(exp_timestamp, timezone.utc).isoformat(),
            "expires_in_seconds": expires_in,
            "expires_in": expires_in_formatted,
            "token_type": token_data['type']
        }
    }), 200

# Ruta de prueba
@app.route("/")
def index():
    return "¡API de autenticación funcionando!"

@app.route("/hola")
def hola():
    return "¡No sé si es hola lo que quieres decir!"

if __name__ == "__main__":
    # Inicializar la base de datos
    db.init_db()
    
    # Ejecutar la aplicación
    app.run(
        ssl_context=("localhost+3.pem", "localhost+3-key.pem"),
        host="0.0.0.0",
        port=11443,
        debug=True
    )

