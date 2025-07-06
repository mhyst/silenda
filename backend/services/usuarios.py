from database import db, Usuario
from werkzeug.security import generate_password_hash, check_password_hash

class UsuarioService:
    @staticmethod
    def crear_usuario(username, password):
        
        existente = db.get_usuario_por_nombre(username)
        if existente:
            raise ValueError("El nombre de usuario ya existe")
        
        clave_hash = generate_password_hash(password)
        return db.crear_usuario(session, username, clave_hash)

    @staticmethod
    def iniciar_sesion(username, password):
        
        usuario = db.get_usuario_por_nombre(username)
        if not usuario or not check_password_hash(usuario.clave, password):
            return None
        return usuario
    
    @staticmethod
    def listar_usuarios():
        return db.listar_usuarios()
    
    @staticmethod
    def get_usuario_por_id(id):
        return db.get_usuario_por_id(id)

    @staticmethod
    def get_usuario_por_nombre(username):
        return db.get_usuario_por_nombre(username)
    
    @staticmethod
    def actualizar_usuario(id, username, password):
        usuario = db.get_usuario_por_id(id)
        if not usuario:
            raise ValueError("El usuario no existe")
        usuario.nombre = username
        usuario.clave = generate_password_hash(password)
        return db.actualizar_usuario(usuario)
    
        