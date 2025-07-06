"""
Ejemplos de uso de SQLAlchemy con el módulo database.py

Este script muestra cómo realizar operaciones comunes con los modelos de Usuario, Sala y Mensaje.
"""
from database import db, Usuario, Sala, Mensaje
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

def crear_datos_ejemplo():
    """Función para crear datos de ejemplo en la base de datos"""
    with db.session_scope() as session:
        # Crear algunos usuarios con contraseñas hasheadas
        usuarios_data = [
            ("ana_garcia", "segura123"),
            ("carlos_lopez", "contraseñaSegura456"),
            ("luis_martinez", "miClave789*")
        ]
        
        usuarios = []
        for nombre, clave in usuarios_data:
            clave_hash = generate_password_hash(clave)
            usuario = Usuario(nombre=nombre, clave=clave_hash)
            usuarios.append(usuario)
        
        # Agregar usuarios a la sesión
        session.add_all(usuarios)
        
        # Asignar a variables para uso posterior
        usuario1, usuario2, usuario3 = usuarios
        
        # Crear algunas salas
        sala1 = Sala(nombre="General", privada=False)
        sala2 = Sala(nombre="Proyecto X", privada=True)
        
        # Agregar salas a la sesión
        session.add_all([sala1, sala2])
        session.flush()  # Para obtener los IDs generados
        
        # Añadir usuarios a las salas (relación muchos a muchos)
        # Usando la relación directa para evitar problemas con la tabla de asociación
        sala1.miembros.extend([usuario1, usuario2])
        sala2.miembros.extend([usuario1, usuario3])
        
        # Si necesitas asignar roles específicos, puedes hacerlo después
        # Primero obtenemos la tabla de asociación a través de los metadatos
        from sqlalchemy import Table, MetaData
        metadata = MetaData()
        usuarios_salas = Table('usuarios_salas', metadata, autoload_with=db.engine)
        
        # Luego actualizamos los roles específicos
        stmt = usuarios_salas.update().where(
            (usuarios_salas.c.usuario_id == usuario1.id) & 
            (usuarios_salas.c.sala_id == sala1.id)
        ).values(rol='admin')
        session.execute(stmt)
        
        stmt = usuarios_salas.update().where(
            (usuarios_salas.c.usuario_id == usuario2.id) & 
            (usuarios_salas.c.sala_id == sala1.id)
        ).values(rol='miembro')
        session.execute(stmt)
        
        stmt = usuarios_salas.update().where(
            (usuarios_salas.c.usuario_id == usuario1.id) & 
            (usuarios_salas.c.sala_id == sala2.id)
        ).values(rol='admin')
        session.execute(stmt)
        
        stmt = usuarios_salas.update().where(
            (usuarios_salas.c.usuario_id == usuario3.id) & 
            (usuarios_salas.c.sala_id == sala2.id)
        ).values(rol='miembro')
        session.execute(stmt)
        
        # Crear algunos mensajes
        mensajes = [
            Mensaje(
                contenido="¡Hola a todos! ¿Cómo están?",
                sala_id=sala1.id,
                usuario_id=usuario1.id,
                fecha_envio=datetime.now(timezone.utc) - timedelta(minutes=30)
            ),
            Mensaje(
                contenido="¡Hola Ana! Todo bien, ¿y tú?",
                sala_id=sala1.id,
                usuario_id=usuario2.id,
                fecha_envio=datetime.now(timezone.utc) - timedelta(minutes=25)
            ),
            Mensaje(
                contenido="¿Alguien ha avanzado con el módulo de autenticación?",
                sala_id=sala2.id,
                usuario_id=usuario1.id,
                fecha_envio=datetime.now(timezone.utc) - timedelta(hours=1)
            )
        ]
        
        session.add_all(mensajes)
        
        print("Datos de ejemplo creados correctamente.")

def ejemplos_consulta():
    """Ejemplos de consultas a la base de datos"""
    with db.session_scope() as session:
        # 1. Obtener todos los usuarios
        print("\n--- Todos los usuarios ---")
        usuarios = session.query(Usuario).all()
        for usuario in usuarios:
            print(f"ID: {usuario.id}, Nombre: {usuario.nombre}")
        
        # 2. Obtener un usuario por nombre
        print("\n--- Buscar usuario por nombre ---")
        usuario = session.query(Usuario).filter(Usuario.nombre == "ana_garcia").first()
        if usuario:
            print(f"Encontrado: {usuario.nombre} (ID: {usuario.id})")
        
        # 3. Obtener salas de un usuario
        print("\n--- Salas de un usuario ---")
        usuario = session.query(Usuario).filter(Usuario.nombre == "ana_garcia").first()
        if usuario:
            print(f"Salas de {usuario.nombre}:")
            for sala in usuario.salas:
                print(f"- {sala.nombre} (Privada: {sala.privada})")
        
        # 4. Obtener mensajes de una sala con información del usuario
        print("\n--- Mensajes de la sala General ---")
        mensajes = (
            session.query(Mensaje, Usuario)
            .join(Usuario, Mensaje.usuario_id == Usuario.id)
            .join(Sala, Mensaje.sala_id == Sala.id)
            .filter(Sala.nombre == "General")
            .order_by(Mensaje.fecha_envio)
            .all()
        )
        
        for mensaje, usuario in mensajes:
            print(f"[{mensaje.fecha_envio}] {usuario.nombre}: {mensaje.contenido}")

def ejemplos_actualizacion_eliminacion():
    """Ejemplos de actualización y eliminación de registros"""
    with db.session_scope() as session:
        # 1. Actualizar un registro
        usuario = session.query(Usuario).filter(Usuario.nombre == "carlos_lopez").first()
        if usuario:
            usuario.nombre = "carlos_lopez_actualizado"
            print(f"Usuario actualizado: {usuario.nombre}")
        
        # 2. Eliminar un mensaje
        mensaje = session.query(Mensaje).order_by(Mensaje.fecha_envio).first()
        if mensaje:
            session.delete(mensaje)
            print(f"Mensaje eliminado: {mensaje.id}")

def main():
    # Inicializar la base de datos (crea las tablas si no existen)
    db.init_db()
    
    # Crear datos de ejemplo
    crear_datos_ejemplo()
    
    # Ejecutar ejemplos de consultas
    ejemplos_consulta()
    
    # Ejemplos de actualización y eliminación
    ejemplos_actualizacion_eliminacion()

if __name__ == "__main__":
    main()
