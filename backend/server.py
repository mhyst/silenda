#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity, get_jwt,
)
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError
from werkzeug.security import check_password_hash
import os
from datetime import timedelta
import logging

# Importar el módulo de base de datos
from database import db, Usuario
from services.usuarios import UsuarioService

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
    
    with db.session_scope() as session:
        user = UsuarioService.iniciar_sesion(username, password)
    
    # Verificar si el usuario existe y la contraseña es correcta
        if user:
            # Crear el token de acceso - asegurarse de que el identity sea una cadena
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "username": user.nombre,
                    "role": "user"
                }
            )
            return jsonify({
                "access_token": access_token,
                "user_id": user.id,
                "username": user.nombre,
                "msg": "Inicio de sesión exitoso"
            }), 200
        else:
            # Si las credenciales son incorrectas
            return jsonify({"msg": "Usuario o contraseña incorrectos"}), 401

def verify_jwt_and_get_user():
    """
    Verifica el token JWT y devuelve una tupla con (código, user_id, user_name).
    
    Returns:
        tuple: (status_code, user_id, user_name)
        - status_code: 200 si es válido, 401 si no autorizado, 404 si usuario no encontrado
        - user_id: ID del usuario si es válido, None en otro caso
        - user_name: Nombre del usuario si es válido, None en otro caso
    """
    try:
        # Obtener la identidad del token
        current_user_id = get_jwt_identity()
        
        # Obtener información del usuario desde la base de datos
        user_id = int(current_user_id) if isinstance(current_user_id, str) and current_user_id.isdigit() else current_user_id
        claims = get_jwt()
        username = claims.get("username")
        role = claims.get("role")
        
               
        return 200, user_id, username, role
    except (NoAuthorizationError, ExpiredSignatureError) as e:
        logging.warning(f"Token no válido o expirado: {str(e)}")
        return 401, None, None, None 
    except Exception as e:
        logging.warning(f"Error al verificar el token: {str(e)}")
        return 401, None, None, None

# Ruta protegida de ejemplo
@app.route("/api/protegido", methods=["GET"])
@jwt_required()
def ruta_protegida():
    # Obtener la identidad del token
    code, user_id, user_name, role = verify_jwt_and_get_user()
    
    if code == 200:
        return jsonify({
            "message": f"¡Acceso concedido! Usuario: {user_name}",
            "user_id": user_id,
            "username": user_name
        }), code

    return jsonify({"message": "Usuario no encontrado"}), code

# Ruta para verificar un token JWT
@app.route("/api/auth/verify", methods=["POST"])
@jwt_required()
def verify_token():
    # Usar la función de utilidad para verificar el token y obtener el usuario
    code, user_id, username, role = verify_jwt_and_get_user()
    
    if code != 200:
        return jsonify({
            "valid": False,
            "message": "Token inválido o usuario no encontrado" if code == 404 else "Usuario no autorizado"
        }), code
    
    # Obtener información adicional del token
    token_data = get_jwt()
    
    # Calcular tiempo restante de expiración
    from datetime import datetime, timezone
    exp_timestamp = token_data['exp']
    current_timestamp = datetime.now(timezone.utc).timestamp()
    expires_in = int(exp_timestamp - current_timestamp)  # en segundos
    
    # Formatear tiempo restante
    minutes, seconds = divmod(expires_in, 60)
    expires_in_formatted = f"{minutes}m {seconds}s"
    
    # Crear la respuesta final
    return jsonify({
        "valid": True,
        "message": "Token válido",
        "user": {
            "id": user_id,
            "username": username,
            "role": role,
            "is_authenticated": True,
            "is_active": True
        },
        "token_info": {
            "issued_at": datetime.fromtimestamp(token_data['iat'], timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(exp_timestamp, timezone.utc).isoformat(),
            "expires_in_seconds": expires_in,
            "expires_in": expires_in_formatted,
            "token_type": token_data['type']
        }
    }), 200

# Ruta para obtener los datos del usuario actual
@app.route("/api/user/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    Endpoint protegido que devuelve los datos del usuario autenticado.
    Requiere un token JWT válido en el encabezado de autorización.
    """
    # Verificar el token y obtener el ID del usuario
    code, user_id, _, _ = verify_jwt_and_get_user()
    
    if code != 200:
        return jsonify({
            "error": "No autorizado" if code == 401 else "Usuario no encontrado"
        }), code
    
    # Obtener los datos del usuario desde la base de datos
    with db.session_scope() as session:
        user = UsuarioService.get_usuario_por_id(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Convertir el objeto Usuario a un diccionario
        user_data = {
            "id": user.id,
            "nombre": user.nombre,
            "fecha_creado": user.fecha_creado.isoformat() if user.fecha_creado else None,
            "activo": user.activo,
            "role": user.role
        }
        
        return jsonify(user_data), 200

@app.route("/api/user/me", methods=["PATCH"])
@jwt_required()
def update_current_user():
    """
    Endpoint protegido que actualiza los datos del usuario autenticado.
    Permite actualizar el nombre de usuario y/o la contraseña.
    Requiere un token JWT válido en el encabezado de autorización.
    """
    # Verificar el token y obtener el ID del usuario
    code, user_id, _, _ = verify_jwt_and_get_user()
    
    if code != 200:
        return jsonify({
            "error": "No autorizado" if code == 401 else "Usuario no encontrado"
        }), code
    
    # Obtener los datos de la petición
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    # Validar que se proporcione al menos un campo para actualizar
    if not any([username, password]):
        return jsonify({
            "error": "Se debe proporcionar al menos un campo para actualizar (username o password)"
        }), 400
    
    try:
        with db.session_scope() as session:
            # Obtener el usuario actual
            user = UsuarioService.get_usuario_por_id(user_id)
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # Actualizar los campos proporcionados
            update_data = {}
            if username is not None:
                # Verificar si el nuevo nombre de usuario ya existe
                if username != user.nombre:  # Solo verificar si el nombre es diferente
                    existing_user = UsuarioService.get_usuario_por_nombre(username)
                    if existing_user and existing_user.id != user.id:
                        return jsonify({"error": "El nombre de usuario ya está en uso"}), 400
                update_data['username'] = username
            
            if password is not None:
                if not password.strip():
                    return jsonify({"error": "La contraseña no puede estar vacía"}), 400
                update_data['password'] = password
            
            # Actualizar el usuario
            updated_user = UsuarioService.actualizar_usuario(
                id=user_id,
                username=update_data.get('username', user.nombre),
                password=update_data.get('password', None)  # None significa que no se actualiza la contraseña
            )
            
            # Preparar la respuesta
            response_data = {
                "id": updated_user.id,
                "username": updated_user.nombre,
                "message": "Usuario actualizado correctamente"
            }
            
            # Si se actualizó el nombre de usuario, generar un nuevo token
            if 'username' in update_data:
                new_token = create_access_token(
                    identity=str(updated_user.id),
                    additional_claims={
                        "username": updated_user.nombre,
                        "role": "user"
                    }
                )
                response_data["new_token"] = new_token
            
            return jsonify(response_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Error al actualizar el usuario: {str(e)}")
        return jsonify({"error": "Error interno del servidor al actualizar el usuario"}), 500

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

