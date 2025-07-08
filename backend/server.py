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
from services.mensajes import MensajesService
from services.salas import SalaService

# Configuración de la aplicación
app = Flask(__name__)

# Inicializa SocketIO con la app Flask
socketio = SocketIO(app, cors_allowed_origins="*")

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

# Ruta para obtener el perfil público de un usuario
@app.route("/api/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_profile(user_id):
    """
    Obtiene el perfil público de un usuario por su ID.
    Requiere autenticación con JWT.
    
    Args:
        user_id (int): ID del usuario cuyo perfil se desea obtener
        
    Returns:
        JSON con los datos del perfil del usuario o mensaje de error
    """
    # Verificar el token JWT
    code, current_user_id, _, _ = verify_jwt_and_get_user()
    if code != 200:
        return jsonify({"msg": "No autorizado"}), 401
    
    # Obtener el usuario solicitado
    with db.session_scope() as session:
        user = db.get_usuario_por_id(user_id)
        
        if not user or not user.activo:
            return jsonify({"msg": "Usuario no encontrado"}), 404
            
        # Devolver solo la información pública del perfil
        return jsonify({
            "id": user.id,
            "nombre": user.nombre,
            "fecha_creado": user.fecha_creado.isoformat(),
            "activo": user.activo
        }), 200

# Ruta para buscar usuarios por nombre
@app.route("/api/users/search", methods=["GET"])
@jwt_required()
def search_users():
    """
    Busca usuarios por nombre parcial (case-insensitive).
    Requiere autenticación con JWT.
    
    Query Parameters:
        query (str): Texto a buscar en los nombres de usuario (mínimo 2 caracteres)
        limit (int, opcional): Número máximo de resultados (por defecto 10, máximo 50)
        
    Returns:
        JSON con la lista de usuarios que coinciden con la búsqueda
    """
    # Verificar el token JWT
    code, current_user_id, _, _ = verify_jwt_and_get_user()
    if code != 200:
        return jsonify({"msg": "No autorizado"}), 401
    
    # Obtener parámetros de la consulta
    query = request.args.get('query', '').strip()
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Máximo 50 resultados
    except ValueError:
        limit = 10
    
    # Validar la consulta
    if len(query) < 2:
        return jsonify({
            "msg": "La búsqueda debe tener al menos 2 caracteres",
            "results": []
        }), 400
    
    # Buscar usuarios
    with db.session_scope() as session:
        users = db.buscar_usuarios_por_nombre(query, limit=limit)
        
        # Formatear resultados
        results = [{
            "id": user.id,
            "nombre": user.nombre,
            "fecha_creado": user.fecha_creado.isoformat(),
            "activo": user.activo
        } for user in users]
        
        return jsonify({
            "query": query,
            "count": len(results),
            "results": results
        }), 200

# Ruta de prueba
@app.route("/")
def index():
    return "¡Bienvenido a la API de Silenda!"

@app.route("/hola")
def hola():
    return "¡Hola desde Silenda!"

# Endpoints de salas

@app.route("/api/rooms", methods=["GET"])
@jwt_required()
def get_rooms():
    """
    Obtiene todas las salas disponibles a las que pertenece el usuario.
    
    Returns:
        Lista de salas
    """

    # Obtener el ID del usuario autenticado
    user_id = get_jwt_identity()
    
    # Obtener las salas a las que pertenece el usuario
    with db.session_scope() as session:
        salas = db.listar_salas(usuario_id=user_id)

        for sala in salas:
            socketio.join_room(f"sala_{sala.id}")
    
        # Convertir las salas a diccionario para la respuesta
        salas_dict = [{
            "id": sala.id,
            "nombre": sala.nombre,
            "privada": sala.privada,
            "fecha_creado": sala.fecha_creado.isoformat()
        } for sala in salas]
    
        return jsonify(salas_dict), 200



@app.route("/api/rooms/<int:room_id>", methods=["GET"])
@jwt_required()
def get_room(room_id):
    """
    Obtiene información detallada de una sala.
    
    Args:
        room_id: ID de la sala a consultar
        
    Returns:
        Información detallada de la sala
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Obtener la sala
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar que el usuario es miembro de la sala si es privada
    if sala.privada and not SalaService.es_miembro(room_id, user_id):
        return jsonify({"msg": "No tienes permiso para ver esta sala"}), 403
        
    # Obtener información de la sala
    return jsonify({
        "id": sala.id,
        "nombre": sala.nombre,
        "tipo": "privada" if sala.privada else "pública",
        "fecha_creacion": sala.fecha_creado.isoformat(),
        "creador_id": sala.usuario_creador_id
    }), 200

@app.route("/api/rooms", methods=["POST"])
@jwt_required()
def create_room():
    """
    Crea una nueva sala.
    
    Body (JSON):
        nombre: Nombre de la sala (requerido)
        privada: Booleano que indica si la sala es privada (opcional, por defecto True)
        
    Returns:
        La sala creada
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Obtener datos de la solicitud
    data = request.get_json()
    if not data or 'nombre' not in data:
        return jsonify({"msg": "Se requiere el nombre de la sala"}), 400
        
    # Crear la sala
    try:
        privada = data.get('privada', True)
        sala = SalaService.crear_sala(
            nombre=data['nombre'],
            privada=privada,
            usuario_creador_id=user_id
        )
        
        # Añadir al creador como miembro de la sala
        SalaService.agregar_usuario_a_sala(user_id, sala.id, rol='admin')
        
        return jsonify({
            "id": sala.id,
            "nombre": sala.nombre,
            "tipo": "privada" if sala.privada else "pública",
            "fecha_creacion": sala.fecha_creado.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({"msg": f"Error al crear la sala: {str(e)}"}), 500

@app.route("/api/rooms/<int:room_id>/join", methods=["POST"])
@jwt_required()
def join_room(room_id):
    """
    Une al usuario actual a una sala.
    
    Args:
        room_id: ID de la sala a la que unirse
        
    Returns:
        Mensaje de éxito o error
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Verificar que la sala existe
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar si el usuario ya es miembro
    if SalaService.es_miembro(room_id, user_id):
        return jsonify({"msg": "Ya eres miembro de esta sala"}), 400
        
    try:
        # Unir al usuario a la sala
        SalaService.agregar_usuario_a_sala(room_id, user_id)
        socketio.join_room(f"sala_{room_id}")
        return jsonify({"msg": "Te has unido a la sala correctamente"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error al unirse a la sala: {str(e)}"}), 500

@app.route("/api/rooms/<int:room_id>/leave", methods=["POST"])
@jwt_required()
def leave_room(room_id):
    """
    Saca al usuario actual de una sala.
    
    Args:
        room_id: ID de la sala de la que salir
        
    Returns:
        Mensaje de éxito o error
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Verificar que la sala existe
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar si el usuario es miembro
    if not SalaService.es_miembro(room_id, user_id):
        return jsonify({"msg": "No eres miembro de esta sala"}), 400
        
    try:
        # Sacar al usuario de la sala
        SalaService.eliminar_usuario_de_sala(room_id, user_id)
        socketio.leave_room(f"sala_{room_id}")
        return jsonify({"msg": "Has abandonado la sala correctamente"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error al salir de la sala: {str(e)}"}), 500

@app.route("/api/rooms/<int:room_id>", methods=["PATCH"])
@jwt_required()
def update_room(room_id):
    """
    Actualiza los detalles de una sala (solo para administradores).
    
    Body (JSON):
        nombre: Nuevo nombre de la sala (opcional)
        privada: Nuevo estado de privacidad (opcional)
        
    Returns:
        La sala actualizada
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Verificar que la sala existe
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar que el usuario es administrador de la sala
    if not SalaService.es_admin(room_id, user_id):
        return jsonify({"msg": "No tienes permiso para modificar esta sala"}), 403
        
    # Obtener datos de la solicitud
    data = request.get_json()
    if not data:
        return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
        
    try:
        # Actualizar la sala
        if 'nombre' in data:
            sala.nombre = data['nombre']
        if 'privada' in data:
            sala.privada = data['privada']
            
        db.session.commit()
        
        return jsonify({
            "id": sala.id,
            "nombre": sala.nombre,
            "privada": sala.privada,
            "fecha_actualizacion": sala.fecha_creado.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al actualizar la sala: {str(e)}"}), 500

@app.route("/api/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
def delete_room(room_id):
    """
    Elimina una sala (solo para administradores).
    
    Args:
        room_id: ID de la sala a eliminar
        
    Returns:
        Mensaje de éxito o error
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Verificar que la sala existe
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar que el usuario es administrador de la sala
    if not SalaService.es_admin(room_id, user_id):
        return jsonify({"msg": "No tienes permiso para eliminar esta sala"}), 403
        
    try:
        # Eliminar la sala
        SalaService.eliminar_sala(room_id)
        socketio.leave_room(f"sala_{room_id}")
        socketio.emit("sala_eliminada", {"room_id": room_id})
        return jsonify({"msg": "Sala eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error al eliminar la sala: {str(e)}"}), 500

@app.route("/api/rooms/<int:room_id>/members", methods=["GET"])
@jwt_required()
def get_room_members(room_id):
    """
    Obtiene la lista de miembros de una sala.
    
    Args:
        room_id: ID de la sala
        
    Returns:
        Lista de miembros de la sala
    """
    # Verificar que el usuario está autenticado
    status_code, user_id, _ = verify_jwt_and_get_user()
    if status_code != 200:
        return jsonify({"msg": "No autorizado"}), 401
        
    # Verificar que la sala existe
    sala = SalaService.obtener_sala_por_id(room_id)
    if not sala:
        return jsonify({"msg": "Sala no encontrada"}), 404
        
    # Verificar que el usuario es miembro de la sala si es privada
    if sala.privada and not SalaService.es_miembro(room_id, user_id):
        return jsonify({"msg": "No tienes permiso para ver los miembros de esta sala"}), 403
        
    # Obtener los miembros de la sala
    try:
        miembros = SalaService.listar_usuarios_de_sala(room_id)
        return jsonify([{
            "id": m.usuario.id,
            "nombre": m.usuario.nombre,
            "rol": m.rol,
            "fecha_union": m.fecha_union.isoformat()
        } for m in miembros]), 200
    except Exception as e:
        return jsonify({"msg": f"Error al obtener los miembros de la sala: {str(e)}"}), 500

# Endpoints de mensajes

@app.route("/api/rooms/<int:room_id>/messages", methods=["GET"])
@jwt_required()
def get_room_messages(room_id):
    """
    Obtiene mensajes de una sala con paginación hacia atrás.
    
    Query Parameters:
        before: ID del mensaje a partir del cual cargar mensajes más antiguos (opcional)
        limit: Número máximo de mensajes a devolver (por defecto 50, máximo 100)
        
    Returns:
        Lista de mensajes ordenados por fecha de envío (más recientes primero)
    """
    try:
        # Obtener parámetros de la consulta
        before_id = request.args.get('before', type=int)
        limit = min(100, request.args.get('limit', 50, type=int))
        
        # Obtener mensajes
        mensajes = MensajesService.obtener_mensajes_paginados(
            sala_id=room_id,
            antes_de_id=before_id,
            limite=limit
        )
        
        # Convertir mensajes a diccionarios
        mensajes_dict = [{
            'id': msg.id,
            'contenido': msg.contenido,
            'fecha_envio': msg.fecha_envio.isoformat(),
            'usuario_id': msg.usuario_id,
            'sala_id': msg.sala_id
        } for msg in mensajes]
        
        return jsonify(mensajes_dict), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/rooms/<int:room_id>/messages", methods=["POST"])
@jwt_required()
def send_message(room_id):
    """
    Envía un mensaje a una sala.
    
    Body (JSON):
        contenido: Contenido del mensaje (requerido)
        
    Returns:
        El mensaje creado
    """
    try:
        # Obtener datos de la petición
        data = request.get_json()
        contenido = data.get('contenido')
        
        if not contenido:
            return jsonify({"error": "El contenido del mensaje es requerido"}), 400
        
        # Obtener el ID del usuario autenticado
        user_id = get_jwt_identity()
        
        try:
            # Crear el mensaje
            mensaje = MensajesService.agregar_mensaje(
                contenido=contenido,
                sala_id=room_id,
                usuario_id=user_id
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Convertir el mensaje a diccionario para la respuesta
        mensaje_dict = {
            'id': mensaje.id,
            'contenido': mensaje.contenido,
            'fecha_envio': mensaje.fecha_envio.isoformat(),
            'usuario_id': mensaje.usuario_id,
            'sala_id': mensaje.sala_id
        }

        socketio.emit("nuevo_mensaje", mensaje_dict, room=f"sala_{room_id}")
        
        return jsonify(mensaje_dict), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/messages/<int:message_id>", methods=["GET"])
@jwt_required()
def get_message(message_id):
    """
    Obtiene un mensaje específico por su ID.

    Este método no tiene ninguna protección por lo que en teoría cualquier usuario podrá obtener cualquier mensaje.
    permite a cualquiera con un token válido recopilar cualquier
    mensaje del sistema. Esto habría que corregirlo.
    
    Returns:
        El mensaje solicitado
    """
    try:
        mensaje = MensajesService.obtener_mensaje_por_id(message_id)
        
        if not mensaje:
            return jsonify({"error": "Mensaje no encontrado"}), 404
            
        mensaje_dict = {
            'id': mensaje.id,
            'contenido': mensaje.contenido,
            'fecha_envio': mensaje.fecha_envio.isoformat(),
            'usuario_id': mensaje.usuario_id,
            'sala_id': mensaje.sala_id
        }
        
        return jsonify(mensaje_dict), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/messages/<int:message_id>", methods=["PATCH"])
@jwt_required()
def edit_message(message_id):
    """
    Edita un mensaje existente.
    
    Body (JSON):
        contenido: Nuevo contenido del mensaje (requerido)
        
    Returns:
        El mensaje actualizado
    """
    try:
        # Obtener datos de la petición
        data = request.get_json()
        nuevo_contenido = data.get('contenido')
        
        if not nuevo_contenido:
            return jsonify({"error": "El contenido del mensaje es requerido"}), 400
        
        # Obtener el ID del usuario autenticado
        user_id = get_jwt_identity()
        
        # Intentar editar el mensaje
        mensaje_actualizado = MensajesService.editar_mensaje(
            mensaje_id=message_id,
            usuario_id=user_id,
            nuevo_contenido=nuevo_contenido
        )
        
        if not mensaje_actualizado:
            return jsonify({"error": "No tienes permiso para editar este mensaje"}), 403
            
        # Convertir el mensaje a diccionario para la respuesta
        mensaje_dict = {
            'id': mensaje_actualizado.id,
            'contenido': mensaje_actualizado.contenido,
            'fecha_envio': mensaje_actualizado.fecha_envio.isoformat(),
            'usuario_id': mensaje_actualizado.usuario_id,
            'sala_id': mensaje_actualizado.sala_id
        }
        
        socketio.emit("mensaje_actualizado", mensaje_dict, room=f"sala_{mensaje_actualizado.sala_id}")
        return jsonify(mensaje_dict), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/messages/<int:message_id>", methods=["DELETE"])
@jwt_required()
def delete_message(message_id):
    """
    Elimina un mensaje.
    
    Returns:
        Mensaje de éxito o error
    """
    try:
        # Obtener el ID del usuario autenticado
        user_id = get_jwt_identity()
        
        # Intentar eliminar el mensaje
        eliminado, sala_id = MensajesService.eliminar_mensaje(
            mensaje_id=message_id,
            usuario_id=user_id
        )
        
        if not eliminado:
            return jsonify({"error": "No tienes permiso para eliminar este mensaje o el mensaje no existe"}), 403
            
        socketio.emit("mensaje_eliminado", {"id": message_id}, room=f"sala_{sala_id}")
        return jsonify({"mensaje": "Mensaje eliminado correctamente"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Parte de gestión de WebSockets

@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")
    identidad = decode_token(token)["sub"]

    # Sala privada
    join_room(f"user_{identidad}")

    # Supongamos que cargas los grupos desde la base de datos:
    salas = db.listar_salas(usuario_id=identidad)
    for sala_id in salas:
        join_room(f"sala_{sala_id}")

    print(f"Usuario {identidad} conectado y unido a sus salas.")


if __name__ == "__main__":
    # Inicializar la base de datos
    db.init_db()
    
    # Ejecutar la aplicación
    socketio.run(
        ssl_context=("localhost+3.pem", "localhost+3-key.pem"),
        host="0.0.0.0",
        port=11443,
        debug=True
    )

