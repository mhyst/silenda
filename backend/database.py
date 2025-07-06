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

# Crear una instancia global del gestor de base de datos
db = DatabaseManager()

def init_db():
    """Función de conveniencia para inicializar la base de datos"""
    db.init_db()

if __name__ == "__main__":
    # Si se ejecuta directamente, inicializar la base de datos
    init_db()
    print("Base de datos inicializada correctamente.")
