from database import db, Mensaje
from services.salas import SalaService

class MensajesService:

    @staticmethod
    def obtener_mensaje_por_id(mensaje_id):
        """
        Obtiene un mensaje por su ID.
        
        Args:
            mensaje_id: ID del mensaje a buscar
            
        Returns:
            El mensaje encontrado o None si no existe
        """
        return db.get_mensaje_por_id(mensaje_id)

    @staticmethod
    def agregar_mensaje(contenido, sala_id, usuario_id):
        """
        Agrega un mensaje a una sala.
        
        Args:
            contenido: Contenido del mensaje
            sala_id: ID de la sala
            usuario_id: ID del usuario que envía el mensaje
            
        Returns:
            El mensaje creado
        """
        return db.agregar_mensaje(contenido, sala_id, usuario_id)
    
    @staticmethod
    def obtener_mensajes_por_sala(sala_id, limite=100):
        """
        Obtiene los mensajes de una sala.
        
        Args:
            sala_id: ID de la sala
            limite: Número máximo de mensajes a devolver (por defecto 100)
            
        Returns:
            Lista de mensajes ordenados por fecha de envío (más recientes primero)
        """
        return db.get_mensajes_por_sala(sala_id, limite)
        
    @staticmethod
    def obtener_mensajes_paginados(sala_id, antes_de_id=None, limite=50):
        """
        Obtiene mensajes de una sala con paginación hacia atrás.
        
        Args:
            sala_id: ID de la sala
            antes_de_id: ID del mensaje a partir del cual cargar mensajes más antiguos.
                        Si es None, devuelve los mensajes más recientes.
            limite: Número máximo de mensajes a devolver (por defecto 50)
            
        Returns:
            Lista de mensajes ordenados por fecha de envío (más recientes primero)
        """
        return db.get_mensajes_paginados(sala_id, antes_de_id, limite)
        
    @staticmethod
    def eliminar_mensaje(mensaje_id, usuario_id):
        """
        Elimina un mensaje si el usuario es el autor o un administrador de la sala.
        
        Args:
            mensaje_id: ID del mensaje a eliminar
            usuario_id: ID del usuario que solicita la eliminación
            
        Returns:
            bool: True si el mensaje fue eliminado, False si el usuario no tiene permisos
            
        Raises:
            ValueError: Si el mensaje no existe
        """
        mensaje = db.get_mensaje_por_id(mensaje_id)
        if not mensaje:
            raise ValueError("Mensaje no encontrado")
            
        # Verificar si el usuario es el autor del mensaje
        if mensaje.usuario_id == usuario_id:
            return db.eliminar_mensaje_por_id(mensaje_id)
            
        # Si no es el autor, verificar si es administrador de la sala
        if SalaService.es_admin(mensaje.sala_id, usuario_id):
            return db.eliminar_mensaje_por_id(mensaje_id)
            
        return False
        
    @staticmethod
    def editar_mensaje(mensaje_id, usuario_id, nuevo_contenido):
        """
        Edita el contenido de un mensaje si el usuario es el autor.
        
        Args:
            mensaje_id: ID del mensaje a editar
            usuario_id: ID del usuario que solicita la edición
            nuevo_contenido: Nuevo contenido del mensaje
            
        Returns:
            El mensaje actualizado si se pudo editar, None si no se tienen permisos
            
        Raises:
            ValueError: Si el mensaje no existe
        """
        mensaje = db.get_mensaje_por_id(mensaje_id)
        if not mensaje:
            raise ValueError("Mensaje no encontrado")
            
        # Solo el autor puede editar el mensaje
        if mensaje.usuario_id == usuario_id:
            return db.actualizar_mensaje(mensaje_id, nuevo_contenido)
            
        return None
    