"""
Módulo de soporte para la base de datos usando SQLAlchemy.
Proporciona modelos y funciones de acceso a datos para el sistema de mensajería.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime
import os
from contextlib import contextmanager
import threading

# Configuración de la base de datos
Base = declarative_base()

# Tabla de relación muchos a muchos entre usuarios y salas
usuarios_salas = Table(
    'usuarios_salas',
    Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('sala_id', Integer, ForeignKey('salas.id'), primary_key=True),
    Column('rol', String(20), default='miembro'),
    Column('fecha_union', DateTime, default=datetime.utcnow)
)

class Usuario(Base):
    """Modelo de usuario del sistema"""
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    clave = Column(String(100), nullable=False)  # Almacenará el hash de la contraseña
    fecha_creado = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    salas = relationship('Sala', secondary=usuarios_salas, back_populates='miembros')
    mensajes = relationship('Mensaje', back_populates='usuario')
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, nombre='{self.nombre}')>"
        
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'fecha_creado': self.fecha_creado,
            'activo': self.activo
        }

class Sala(Base):
    """Modelo de sala de chat"""
    __tablename__ = 'salas'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    privada = Column(Boolean, default=True)
    fecha_creado = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    miembros = relationship('Usuario', secondary=usuarios_salas, back_populates='salas')
    mensajes = relationship('Mensaje', back_populates='sala', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Sala(id={self.id}, nombre='{self.nombre}', privada={self.privada})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'privada': self.privada,
            'fecha_creado': self.fecha_creado
        }
            

class Mensaje(Base):
    """Modelo de mensaje en el chat"""
    __tablename__ = 'mensajes'
    
    id = Column(Integer, primary_key=True)
    contenido = Column(String(1000), nullable=False)
    fecha_envio = Column(DateTime, default=datetime.utcnow)
    
    # Claves foráneas
    sala_id = Column(Integer, ForeignKey('salas.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Relaciones
    sala = relationship('Sala', back_populates='mensajes')
    usuario = relationship('Usuario', back_populates='mensajes')
    
    def __repr__(self):
        return f"<Mensaje(id={self.id}, usuario_id={self.usuario_id}, sala_id={self.sala_id})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'contenido': self.contenido,
            'fecha_envio': self.fecha_envio,
            'sala_id': self.sala_id,
            'usuario_id': self.usuario_id
        }

class DatabaseManager:
    """Clase para gestionar la conexión y sesiones de la base de datos"""
    
    def __init__(self, db_url=None):
        # Usar SQLite por defecto si no se especifica otra URL
        if db_url is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mensajeria.db')
            db_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(db_url, echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    _local = threading.local()

    @classmethod
    def set_session(cls, session):
        cls._local.session = session

    @classmethod
    def get_session(cls):
        return getattr(cls._local, 'session', None)
    
    def init_db(self):
        """Crea todas las tablas en la base de datos"""
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def session_scope(self):
        """Proporciona un contexto transaccional para las operaciones de base de datos"""
        session = self.Session()
        try:
            DatabaseManager.set_session(session)
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Métodos de utilidad para operaciones comunes
    
    def get_usuario_por_nombre(self, nombre):
        session = DatabaseManager.get_session()
        """Obtiene un usuario por su nombre de usuario"""
        return session.query(Usuario).filter(Usuario.nombre == nombre).first()

    def get_usuario_por_id(self, id):
        session = DatabaseManager.get_session()
        """Obtiene un usuario por su ID"""
        return session.query(Usuario).get(id)
 
    def crear_usuario(self, nombre, clave_hash):
        session = DatabaseManager.get_session()
        """Crea un nuevo usuario"""
        usuario = Usuario(nombre=nombre, clave=clave_hash)
        session.add(usuario)
        session.flush()  # Para obtener el ID del usuario creado
        return usuario
    
    def listar_usuarios(self):
        session = DatabaseManager.get_session()
        """Obtiene todos los usuarios"""
        return session.query(Usuario).all()
        
    def buscar_usuarios_por_nombre(self, query, limit=10):
        session = DatabaseManager.get_session()
        """
        Busca usuarios cuyo nombre contenga la cadena de búsqueda.
        
        Args:
            query (str): Texto a buscar en los nombres de usuario
            limit (int): Número máximo de resultados a devolver
            
        Returns:
            List[Usuario]: Lista de usuarios que coinciden con la búsqueda
        """
        if not query or len(query.strip()) < 2:
            return []
            
        search = f"%{query}%"
        return (session.query(Usuario)
                .filter(Usuario.nombre.ilike(search), Usuario.activo == True)
                .order_by(Usuario.nombre)
                .limit(limit)
                .all())
    
    def actualizar_usuario(self, usuario):
        """Actualiza un usuario"""
        session = DatabaseManager.get_session()
        session.add(usuario)
        session.flush()
        return usuario
    
    def get_sala_por_id(self, sala_id):
        session = DatabaseManager.get_session()
        """Obtiene una sala por su ID"""
        return session.query(Sala).get(sala_id)

    def listar_salas(self, usuario_id=None, solo_publicas=False):
        session = DatabaseManager.get_session()
        """Lista las salas disponibles"""
        query = session.query(Sala)
        
        if usuario_id:
            # Filtrar salas a las que pertenece el usuario
            query = query.join(Sala.miembros).filter(Usuario.id == usuario_id)
        elif solo_publicas:
            # Filtrar solo salas públicas
            query = query.filter(Sala.privada == False)
        
        return query.all()
    
    def crear_sala(self, nombre, privada=True, usuario_creador_id=None):
        session = DatabaseManager.get_session()
        """Crea una nueva sala y asigna al usuario como administrador"""
        sala = Sala(nombre=nombre, privada=privada)
        session.add(sala)
        session.flush()  # Para obtener el ID de la sala
            
        if usuario_creador_id:
            # Añadir al creador como administrador
            stmt = usuarios_salas.insert().values(
                usuario_id=usuario_creador_id,
                sala_id=sala.id,
                rol='admin'
            )
            session.execute(stmt)
            
        return sala
    
    def actualizar_sala(self, sala_id, nombre=None, privada=None):
        session = DatabaseManager.get_session()
        sala = session.query(Sala).get(sala_id)
        if not sala:
            raise ValueError("Sala no encontrada")
        
        if nombre:
            sala.nombre = nombre
        if privada:
            sala.privada = privada
        
        session.add(sala)
        session.flush()
        return sala
    
    def eliminar_sala(self, sala_id):
        session = DatabaseManager.get_session()
        sala = session.query(Sala).get(sala_id)
        if not sala:
            raise ValueError("Sala no encontrada")
        session.delete(sala)
        session.flush()
        return sala
    
    def es_admin(self, sala_id, usuario_id):
        session = DatabaseManager.get_session()
        return session.query(usuarios_salas).filter(
            usuarios_salas.c.sala_id == sala_id,
            usuarios_salas.c.usuario_id == usuario_id,
            usuarios_salas.c.rol == 'admin'
        ).first() is not None

    def agregar_usuario_a_sala(self, usuario_id, sala_id, rol='miembro'):
        """
        Agrega un usuario a una sala.
        
        Args:
            usuario_id: ID del usuario a agregar
            sala_id: ID de la sala a la que se agregará el usuario
            rol: Rol del usuario en la sala (por defecto 'miembro')
            
        Returns:
            True si se agregó correctamente, False si ya era miembro
        """
        sala = self.get_sala_por_id(sala_id)
        usuario = self.get_usuario_por_id(usuario_id)
        
        if not sala or not usuario:
            raise ValueError("Sala o usuario no encontrado")
        
        # Verificar si el usuario ya es miembro
        if usuario in sala.miembros:
            return False
        
        session = DatabaseManager.get_session()
        
        # Agregar el usuario a la sala con el rol especificado
        stmt = usuarios_salas.insert().values(
            usuario_id=usuario_id,
            sala_id=sala_id,
            rol=rol
        )
        session.execute(stmt)
        session.commit()
        return True
    
    def eliminar_usuario_de_sala(self, usuario_id, sala_id):
        session = DatabaseManager.get_session()
        """Elimina un usuario de una sala"""
        stmt = usuarios_salas.delete().where(
            and_(
                usuarios_salas.c.usuario_id == usuario_id,
                usuarios_salas.c.sala_id == sala_id
            )
        )
        session.execute(stmt)
        session.commit()
        return result.rowcount > 0

    def listar_usuarios_de_sala(self, sala_id):
        session = DatabaseManager.get_session()
        return session.query(Usuario).join(usuarios_salas).filter(usuarios_salas.c.sala_id == sala_id).all()
    
    def agregar_mensaje(self, contenido, sala_id, usuario_id):
        session = DatabaseManager.get_session()
        """Agrega un nuevo mensaje a una sala"""
        mensaje = Mensaje(
            contenido=contenido,
            sala_id=sala_id,
            usuario_id=usuario_id
            )
        session.add(mensaje)
        return mensaje
    
    def get_mensajes_por_sala(self, sala_id, limite=100):
        """Obtiene los mensajes de una sala específica"""
        session = DatabaseManager.get_session()
        return (
                session.query(Mensaje)
                .filter(Mensaje.sala_id == sala_id)
                .order_by(Mensaje.fecha_envio.desc())
                .limit(limite)
                .all()
            )
            
    def get_mensajes_paginados(self, sala_id, antes_de_id=None, limite=50):
        """
        Obtiene mensajes de una sala con paginación hacia atrás.
        
        Args:
            sala_id: ID de la sala
            antes_de_id: ID del mensaje a partir del cual cargar mensajes más antiguos
            limite: Número máximo de mensajes a devolver
            
        Returns:
            Lista de mensajes ordenados por fecha de envío (más recientes primero)
        """
        session = DatabaseManager.get_session()
        query = (
            session.query(Mensaje)
            .filter(Mensaje.sala_id == sala_id)
        )
        
        if antes_de_id:
            # Obtener la fecha del mensaje de referencia
            mensaje_ref = session.query(Mensaje).get(antes_de_id)
            if mensaje_ref:
                query = query.filter(Mensaje.fecha_envio < mensaje_ref.fecha_envio)
        
        return (
            query.order_by(Mensaje.fecha_envio.desc())
            .limit(limite)
            .all()
        )
        
    def get_mensaje_por_id(self, mensaje_id):
        """
        Obtiene un mensaje por su ID.
        
        Args:
            mensaje_id: ID del mensaje a buscar
            
        Returns:
            El mensaje encontrado o None si no existe
        """
        session = DatabaseManager.get_session()
        return session.query(Mensaje).get(mensaje_id)
        
    def eliminar_mensaje_por_id(self, mensaje_id):
        """
        Elimina un mensaje por su ID.
        
        Args:
            mensaje_id: ID del mensaje a eliminar
            
        Returns:
            bool: True si el mensaje fue eliminado, False si no se encontró
        """
        session = DatabaseManager.get_session()
        mensaje = session.query(Mensaje).get(mensaje_id)
        if mensaje:
            session.delete(mensaje)
            session.commit()
            return True
        return False
        
    def actualizar_mensaje(self, mensaje_id, nuevo_contenido):
        """
        Actualiza el contenido de un mensaje.
        
        Args:
            mensaje_id: ID del mensaje a actualizar
            nuevo_contenido: Nuevo contenido del mensaje
            
        Returns:
            El mensaje actualizado o None si no se encontró
        """
        session = DatabaseManager.get_session()
        mensaje = session.query(Mensaje).get(mensaje_id)
        if mensaje:
            mensaje.contenido = nuevo_contenido
            session.commit()
            return mensaje
        return None

# Crear una instancia global del gestor de base de datos
db = DatabaseManager()

def init_db():
    """Función de conveniencia para inicializar la base de datos"""
    db.init_db()

if __name__ == "__main__":
    # Si se ejecuta directamente, inicializar la base de datos
    init_db()
    print("Base de datos inicializada correctamente.")
