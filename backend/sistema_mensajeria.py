#!/usr/bin/env python3
import sqlite3
from datetime import datetime
import getpass
import os

class SistemaMensajeria:
    def __init__(self, db_name="mensajeria.db"):
        # Obtener la ruta absoluta al directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construir la ruta completa a la base de datos
        self.db_name = os.path.join(script_dir, db_name)
        self.conn = None
        self.cursor = None
        self.usuario_actual = None

    def conectar_db(self):
        """Establece conexión con la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return False

    def desconectar_db(self):
        """Cierra la conexión con la base de datos"""
        if self.conn:
            self.conn.close()

    # ===== MÉTODOS PARA USUARIOS =====
    def registrar_usuario(self):
        """Registra un nuevo usuario en el sistema"""
        print("\n=== REGISTRO DE USUARIO ===")
        nombre = input("Nombre de usuario: ")
        clave = getpass.getpass("Contraseña: ")
        
        try:
            self.cursor.execute(
                "INSERT INTO usuarios (nombre, clave) VALUES (?, ?)",
                (nombre, clave)  # En una aplicación real, deberías hashear la contraseña
            )
            self.conn.commit()
            print("¡Usuario registrado exitosamente!")
            return True
        except sqlite3.IntegrityError:
            print("Error: El nombre de usuario ya existe.")
            return False

    def iniciar_sesion(self):
        """Inicia sesión con un usuario existente"""
        print("\n=== INICIO DE SESIÓN ===")
        nombre = input("Nombre de usuario: ")
        clave = getpass.getpass("Contraseña: ")
        
        self.cursor.execute(
            "SELECT id, nombre FROM usuarios WHERE nombre = ? AND clave = ? AND activo = 1",
            (nombre, clave)
        )
        usuario = self.cursor.fetchone()
        
        if usuario:
            self.usuario_actual = {"id": usuario[0], "nombre": usuario[1]}
            print(f"¡Bienvenido, {usuario[1]}!")
            return True
        else:
            print("Credenciales incorrectas o usuario inactivo.")
            return False

    def listar_usuarios(self):
        """Muestra todos los usuarios registrados"""
        print("\n=== LISTA DE USUARIOS ===")
        self.cursor.execute("SELECT id, nombre, fecha_creado, activo FROM usuarios")
        usuarios = self.cursor.fetchall()
        
        if not usuarios:
            print("No hay usuarios registrados.")
            return
        
        print(f"{'ID':<5} {'NOMBRE':<20} {'FECHA CREACIÓN':<25} {'ESTADO'}")
        print("-" * 60)
        for usuario in usuarios:
            estado = "Activo" if usuario[3] else "Inactivo"
            print(f"{usuario[0]:<5} {usuario[1]:<20} {usuario[2]:<25} {estado}")

    # ===== MÉTODOS PARA SALAS =====
    def crear_sala(self):
        """Crea una nueva sala de chat"""
        if not self.usuario_actual:
            print("Debes iniciar sesión para crear una sala.")
            return
        
        print("\n=== CREAR NUEVA SALA ===")
        nombre = input("Nombre de la sala: ")
        privada = input("¿Es privada? (s/n): ").lower() == 's'
        
        try:
            self.cursor.execute(
                "INSERT INTO salas (nombre, privada) VALUES (?, ?)",
                (nombre, privada)
            )
            sala_id = self.cursor.lastrowid
            
            # El creador de la sala se agrega como administrador
            self.cursor.execute(
                "INSERT INTO usuarios_salas (usuario_id, sala_id, rol) VALUES (?, ?, ?)",
                (self.usuario_actual['id'], sala_id, 'admin')
            )
            
            self.conn.commit()
            print(f"¡Sala '{nombre}' creada exitosamente!")
            return True
        except sqlite3.Error as e:
            print(f"Error al crear la sala: {e}")
            return False

    def listar_salas(self):
        """Muestra todas las salas disponibles"""
        print("\n=== SALAS DISPONIBLES ===")
        self.cursor.execute("""
            SELECT s.id, s.nombre, s.privada, COUNT(us.usuario_id) as miembros
            FROM salas s
            LEFT JOIN usuarios_salas us ON s.id = us.sala_id
            GROUP BY s.id
        """)
        salas = self.cursor.fetchall()
        
        if not salas:
            print("No hay salas creadas aún.")
            return
        
        print(f"{'ID':<5} {'NOMBRE':<20} {'TIPO':<10} MIEMBROS")
        print("-" * 40)
        for sala in salas:
            tipo = "Privada" if sala[2] else "Pública"
            print(f"{sala[0]:<5} {sala[1]:<20} {tipo:<10} {sala[3]}")

    # ===== MÉTODOS PARA MENSAJES =====
    def enviar_mensaje(self):
        """Envía un mensaje a una sala"""
        if not self.usuario_actual:
            print("Debes iniciar sesión para enviar mensajes.")
            return
        
        self.listar_salas()
        try:
            sala_id = int(input("\nID de la sala: "))
            contenido = input("Mensaje: ")
            
            # Verificar que el usuario pertenezca a la sala
            self.cursor.execute(
                "SELECT 1 FROM usuarios_salas WHERE usuario_id = ? AND sala_id = ?",
                (self.usuario_actual['id'], sala_id)
            )
            if not self.cursor.fetchone():
                print("No tienes acceso a esta sala o no existe.")
                return
            
            self.cursor.execute(
                """
                INSERT INTO mensajes (sala_id, usuario_id, contenido)
                VALUES (?, ?, ?)
                """,
                (sala_id, self.usuario_actual['id'], contenido)
            )
            self.conn.commit()
            print("Mensaje enviado correctamente!")
        except ValueError:
            print("Por favor ingresa un ID de sala válido.")
        except sqlite3.Error as e:
            print(f"Error al enviar el mensaje: {e}")

    def ver_mensajes_sala(self):
        """Muestra los mensajes de una sala específica"""
        if not self.usuario_actual:
            print("Debes iniciar sesión para ver mensajes.")
            return
        
        self.listar_salas()
        try:
            sala_id = int(input("\nID de la sala para ver mensajes: "))
            
            # Verificar que el usuario pertenezca a la sala
            self.cursor.execute(
                "SELECT 1 FROM usuarios_salas WHERE usuario_id = ? AND sala_id = ?",
                (self.usuario_actual['id'], sala_id)
            )
            if not self.cursor.fetchone():
                print("No tienes acceso a esta sala o no existe.")
                return
            
            # Obtener nombre de la sala
            self.cursor.execute("SELECT nombre FROM salas WHERE id = ?", (sala_id,))
            nombre_sala = self.cursor.fetchone()[0]
            
            print(f"\n=== MENSAJES EN LA SALA: {nombre_sala.upper()} ===")
            
            # Obtener mensajes de la sala
            self.cursor.execute("""
                SELECT m.contenido, u.nombre, m.fecha_envio
                FROM mensajes m
                JOIN usuarios u ON m.usuario_id = u.id
                WHERE m.sala_id = ?
                ORDER BY m.fecha_envio
            """, (sala_id,))
            
            mensajes = self.cursor.fetchall()
            
            if not mensajes:
                print("No hay mensajes en esta sala aún.")
                return
            
            for mensaje in mensajes:
                print(f"\n[{mensaje[2]}] {mensaje[1]}:")
                print(f"  {mensaje[0]}")
                
        except ValueError:
            print("Por favor ingresa un ID de sala válido.")
        except sqlite3.Error as e:
            print(f"Error al obtener los mensajes: {e}")

    # ===== MENÚ PRINCIPAL =====
    def mostrar_menu_principal(self):
        """Muestra el menú principal del sistema"""
        if not self.usuario_actual:
            print("\n=== MENÚ PRINCIPAL ===")
            print("1. Iniciar sesión")
            print("2. Registrarse")
            print("3. Salir")
            
            try:
                opcion = int(input("\nSelecciona una opción: "))
                return opcion
            except ValueError:
                print("Por favor ingresa un número válido.")
                return 0
        else:
            print(f"\n=== MENÚ PRINCIPAL - Usuario: {self.usuario_actual['nombre']} ===")
            print("1. Ver salas")
            print("2. Crear sala")
            print("3. Ver mensajes de una sala")
            print("4. Enviar mensaje")
            print("5. Ver usuarios")
            print("6. Cerrar sesión")
            print("7. Salir")
            
            try:
                opcion = int(input("\nSelecciona una opción: "))
                return opcion + 2  # Ajustar para mantener la coherencia con el menú de no autenticado
            except ValueError:
                print("Por favor ingresa un número válido.")
                return 0

    def ejecutar(self):
        """Ejecuta el sistema de mensajería"""
        if not self.conectar_db():
            print("No se pudo conectar a la base de datos. Saliendo...")
            return
        
        try:
            while True:
                opcion = self.mostrar_menu_principal()
                
                if not self.usuario_actual:
                    # Menú para usuarios no autenticados
                    if opcion == 1:  # Iniciar sesión
                        self.iniciar_sesion()
                    elif opcion == 2:  # Registrarse
                        self.registrar_usuario()
                    elif opcion == 3:  # Salir
                        print("¡Hasta luego!")
                        break
                    else:
                        print("Opción no válida. Intenta de nuevo.")
                else:
                    # Menú para usuarios autenticados
                    if opcion == 3:  # Ver salas
                        self.listar_salas()
                    elif opcion == 4:  # Crear sala
                        self.crear_sala()
                    elif opcion == 5:  # Ver mensajes de una sala
                        self.ver_mensajes_sala()
                    elif opcion == 6:  # Enviar mensaje
                        self.enviar_mensaje()
                    elif opcion == 7:  # Ver usuarios
                        self.listar_usuarios()
                    elif opcion == 8:  # Cerrar sesión
                        print(f"Sesión cerrada. ¡Hasta luego, {self.usuario_actual['nombre']}!")
                        self.usuario_actual = None
                    elif opcion == 9:  # Salir
                        print("¡Hasta luego!")
                        break
                    else:
                        print("Opción no válida. Intenta de nuevo.")
                
                input("\nPresiona Enter para continuar...")
                
        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
        finally:
            self.desconectar_db()


if __name__ == "__main__":
    # Obtener la ruta al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "mensajeria.db")
    
    # Verificar si la base de datos existe, si no, ejecutar el script de inicialización
    if not os.path.exists(db_path):
        print("La base de datos no existe. Creando estructura inicial...")
        import subprocess
        # Asegurarse de que db_init.py se ejecute desde el directorio correcto
        subprocess.run(["python3", os.path.join(script_dir, "db_init.py")], cwd=script_dir)
        input("Base de datos creada. Presiona Enter para continuar...")
    
    # Iniciar el sistema
    sistema = SistemaMensajeria()
    sistema.ejecutar()
