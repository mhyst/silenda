from database import db, Sala, Usuario, usuarios_salas
from datetime import datetime

class SalaService:
    @staticmethod
    def crear_sala(nombre, privada=True, usuario_creador_id=None):
        """
        Crea una nueva sala de chat.
        
        Args:
            nombre: Nombre de la sala
            privada: Booleano que indica si la sala es privada (True) o pública (False)
            usuario_creador_id: ID del usuario que crea la sala (opcional)
            
        Returns:
            La sala creada
        """
        return db.crear_sala(nombre, privada, usuario_creador_id)
    
    @staticmethod
    def obtener_sala_por_id(sala_id):
        """
        Obtiene una sala por su ID.
        
        Args:
            sala_id: ID de la sala a buscar
            
        Returns:
            La sala encontrada o None si no existe
        """
        return db.get_sala_por_id(sala_id)

    @staticmethod
    def es_admin(sala_id, usuario_id):
        return db.es_admin(sala_id, usuario_id)

    @staticmethod
    def es_miembro(sala_id, usuario_id):
        return db.es_miembro(sala_id, usuario_id)
    
    @staticmethod
    def actualizar_sala(sala_id, usuario_id, nombre=None, privada=None):
        """
        Modifica una sala. Solo los administradores de la sala pueden modificarla.
        
        Args:
            sala_id: ID de la sala a modificar
            usuario_id: ID del usuario que intenta modificar la sala (debe ser admin)
            nombre: Nuevo nombre de la sala (opcional)
            privada: Nueva privacidad de la sala (opcional)
            
        Returns:
            La sala modificada
            
        Raises:
            ValueError: Si el usuario no es administrador de la sala
        """
        es_admin = SalaService.es_admin(sala_id, usuario_id)
        
        if not es_admin:
            raise ValueError("No tienes permisos para modificar esta sala")
            
        # Si el usuario es admin, proceder con la actualización
        return db.actualizar_sala(sala_id, nombre, privada)

    @staticmethod
    def eliminar_sala(usuario_id, sala_id):
        """
        Elimina una sala.
        
        Args:
            sala_id: ID de la sala a eliminar
            
        Returns:
            La sala eliminada
        """
        es_admin = SalaService.es_admin(sala_id, usuario_id)
        
        if not es_admin:
            raise ValueError("No tienes permisos para eliminar esta sala")
        
        return db.eliminar_sala(sala_id)

    @staticmethod
    def listar_usuarios_de_sala(sala_id):
        return db.listar_usuarios_de_sala(sala_id)
    
    @staticmethod
    def listar_salas(usuario_id=None, solo_publicas=False):
        """
        Lista las salas disponibles.
        
        Args:
            usuario_id: Si se proporciona, lista solo las salas a las que pertenece el usuario
            solo_publicas: Si es True, lista solo las salas públicas
            
        Returns:
            Lista de salas que cumplen con los criterios
        """
        return db.listar_salas(usuario_id, solo_publicas)
    
    @staticmethod
    def agregar_usuario_a_sala(usuario_id, sala_id, rol='miembro'):
        """
        Agrega un usuario a una sala.
        
        Args:
            usuario_id: ID del usuario a agregar
            sala_id: ID de la sala a la que se agregará el usuario
            rol: Rol del usuario en la sala (por defecto 'miembro')
            
        Returns:
            True si se agregó correctamente, False si ya era miembro
        """
        return db.agregar_usuario_a_sala(usuario_id, sala_id, rol)

    @staticmethod
    def eliminar_usuario_de_sala(usuario_id, sala_id):
        """
        Elimina un usuario de una sala.
        
        Args:
            usuario_id: ID del usuario a eliminar
            sala_id: ID de la sala de la que se eliminará el usuario
            
        Returns:
            True si se eliminó correctamente, False si el usuario no estaba en la sala
        """
        return db.eliminar_usuario_de_sala(usuario_id, sala_id)