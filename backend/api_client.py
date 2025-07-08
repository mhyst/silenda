#!/usr/bin/env python3
import os
import json
import time
import threading
import queue
import signal
import sys
import requests
import websocket
from requests.exceptions import RequestException
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime

class WebSocketClient:
    def __init__(self, base_url, token, on_message=None, on_error=None, on_close=None, on_open=None):
        """
        Inicializa el cliente WebSocket.
        
        Args:
            base_url (str): URL base de la API
            token (str): Token de autenticación JWT
            on_message (callable): Función a llamar cuando se recibe un mensaje
            on_error (callable): Función a llamar cuando ocurre un error
            on_close (callable): Función a llamar cuando se cierra la conexión
            on_open (callable): Función a llamar cuando se abre la conexión
        """
        # Convertir http/https a ws/wss
        parsed_url = urlparse(base_url)
        scheme = 'wss' if parsed_url.scheme == 'https' else 'ws'
        ws_url = urlunparse((scheme, parsed_url.netloc, '/ws', '', '', ''))
        
        self.ws_url = ws_url
        self.token = token
        self.ws = None
        self.running = False
        self.thread = None
        self.message_queue = queue.Queue()
        
        # Configurar manejadores de eventos
        self.on_message_callback = on_message or self._default_on_message
        self.on_error_callback = on_error or self._default_on_error
        self.on_close_callback = on_close or self._default_on_close
        self.on_open_callback = on_open or self._default_on_open
        
        # Configurar WebSocket
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
            header=[f'Authorization: Bearer {token}']
        )
    
    def _on_message(self, ws, message):
        """Manejador de mensajes WebSocket."""
        try:
            data = json.loads(message)
            self.message_queue.put(data)
            self.on_message_callback(data)
        except json.JSONDecodeError:
            print(f"\n[WebSocket] Mensaje no válido: {message}")
    
    def _on_error(self, ws, error):
        """Manejador de errores WebSocket."""
        self.on_error_callback(error)
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Manejador de cierre de conexión WebSocket."""
        self.running = False
        self.on_close_callback(close_status_code, close_msg)
    
    def _on_open(self, ws):
        """Manejador de apertura de conexión WebSocket."""
        self.running = True
        self.on_open_callback()
    
    def _default_on_message(self, data):
        """Manejador de mensajes por defecto."""
        print(f"\n[WebSocket] Mensaje recibido: {json.dumps(data, indent=2)}")
    
    def _default_on_error(self, error):
        """Manejador de errores por defecto."""
        print(f"\n[WebSocket] Error: {error}")
    
    def _default_on_close(self, close_status_code, close_msg):
        """Manejador de cierre por defecto."""
        print(f"\n[WebSocket] Conexión cerrada: {close_status_code} - {close_msg}")
    
    def _default_on_open(self):
        """Manejador de apertura por defecto."""
        print("\n[WebSocket] Conectado al servidor")
    
    def start(self):
        """Inicia el cliente WebSocket en un hilo separado."""
        if self.thread and self.thread.is_alive():
            print("El cliente WebSocket ya está en ejecución")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_forever, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Detiene el cliente WebSocket."""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=1)
    
    def _run_forever(self):
        """Bucle principal del cliente WebSocket."""
        while self.running:
            try:
                self.ws.run_forever(
                    sslopt={"cert_reqs": False},
                    ping_interval=30,
                    ping_timeout=10
                )
            except Exception as e:
                print(f"Error en WebSocket: {e}")
                time.sleep(5)  # Esperar antes de reconectar
    
    def send(self, data):
        """Envía datos a través del WebSocket."""
        if self.ws and self.running:
            if isinstance(data, dict):
                data = json.dumps(data)
            self.ws.send(data)
    
    def get_message(self, timeout=0.1):
        """Obtiene un mensaje de la cola de mensajes."""
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None


class APIClient:
    def __init__(self, base_url, verify_ssl=True):
        """
        Inicializa el cliente de la API.
        
        Args:
            base_url (str): URL base de la API (ej: 'https://192.168.1.10:11443')
            verify_ssl (bool): Verificar certificados SSL (por defecto: True)
        """
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.token = None
        self.user_id = None
        self.username = None
        self.role = None
        self.current_room = None
        self.ws_client = None
        self.ws_thread = None
        self.running = False
        self.message_handlers = {}
        
        # Configurar manejo de señales para una salida limpia
        signal.signal(signal.SIGINT, self._signal_handler)

    def _make_request(self, method, endpoint, data=None, params=None, headers=None):
        """
        Realiza una petición HTTP a la API.
        
        Args:
            method (str): Método HTTP (get, post, put, delete)
            endpoint (str): Ruta del endpoint (ej: '/api/auth/login')
            data (dict, optional): Datos a enviar en el cuerpo de la petición
            params (dict, optional): Parámetros de consulta
            
        Returns:
            tuple: (status_code, response_data)
        """
        url = urljoin(self.base_url, endpoint)
        headers = headers or {}
        
        # Añadir el token de autenticación si está disponible
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, params=params, headers=headers, verify=self.verify_ssl)
            elif method.lower() == 'post':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, json=data, headers=headers, verify=self.verify_ssl)
            elif method.lower() == 'put':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers, verify=self.verify_ssl)
            elif method.lower() == 'delete':
                response = requests.delete(url, headers=headers, verify=self.verify_ssl)
            else:
                return 400, {'error': 'Método HTTP no soportado'}
            
            # Intentar parsear la respuesta como JSON
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
                
            return response.status_code, response_data
            
        except RequestException as e:
            return 0, {'error': f'Error de conexión: {str(e)}'}
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para una salida limpia."""
        print("\nCerrando el cliente...")
        self.disconnect_websocket()
        sys.exit(0)
    
    def _on_websocket_message(self, message):
        """Manejador de mensajes WebSocket."""
        try:
            event_type = message.get('event')
            if event_type in self.message_handlers:
                self.message_handlers[event_type](message)
            else:
                print(f"\n[WebSocket] Evento no manejado '{event_type}': {json.dumps(message, indent=2)}")
        except Exception as e:
            print(f"Error al procesar mensaje WebSocket: {e}")
    
    def on(self, event_type, handler):
        """Registra un manejador para un tipo de evento WebSocket."""
        self.message_handlers[event_type] = handler
    
    def connect_websocket(self):
        """Inicia la conexión WebSocket."""
        if not self.token:
            print("Error: Debe iniciar sesión primero")
            return False
        
        if self.ws_client and hasattr(self.ws_client, 'running') and self.ws_client.running:
            print("Ya hay una conexión WebSocket activa")
            return True
        
        try:
            self.ws_client = WebSocketClient(
                base_url=self.base_url,
                token=self.token,
                on_message=self._on_websocket_message,
                on_error=lambda e: print(f"\n[WebSocket] Error: {e}"),
                on_close=lambda c, m: print(f"\n[WebSocket] Conexión cerrada: {c} - {m}"),
                on_open=lambda: print("\n[WebSocket] Conectado al servidor")
            )
            
            # Iniciar el cliente WebSocket en un hilo separado
            self.ws_client.start()
            
            # Registrar manejadores por defecto
            self._register_default_handlers()
            
            print("\n[+] Conexión WebSocket establecida")
            return True
            
        except Exception as e:
            print(f"Error al conectar WebSocket: {e}")
            return False
    
    def _register_default_handlers(self):
        """Registra manejadores por defecto para eventos comunes."""
        self.on('message', lambda msg: self._handle_message_event(msg))
        self.on('room_updated', lambda msg: self._handle_room_updated(msg))
        self.on('user_joined', lambda msg: self._handle_user_event('unido', msg))
        self.on('user_left', lambda msg: self._handle_user_event('abandonado', msg))
    
    def _handle_message_event(self, message):
        """Maneja eventos de mensajes recibidos."""
        room_id = message.get('room_id')
        sender = message.get('sender', {})
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        # Formatear la marca de tiempo si está disponible
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%H:%M:%S')
            except (ValueError, AttributeError):
                pass
        
        # Mostrar el mensaje si estamos en la sala correspondiente
        if not self.current_room or str(self.current_room) == str(room_id):
            print(f"\n[{timestamp}] {sender.get('username', 'Desconocido')}: {content}")
        else:
            print(f"\n[Mensaje en sala {room_id}] {sender.get('username', 'Alguien')}: {content[:30]}...")
    
    def _handle_room_updated(self, message):
        """Maneja eventos de actualización de sala."""
        room_id = message.get('room_id')
        updates = message.get('updates', {})
        
        if 'name' in updates:
            print(f"\n[!] La sala {room_id} ha sido renombrada a: {updates['name']}")
        if 'private' in updates:
            status = 'privada' if updates['private'] else 'pública'
            print(f"\n[!] La sala {room_id} ahora es {status}")
    
    def _handle_user_event(self, action, message):
        """Maneja eventos de entrada/salida de usuarios."""
        room_id = message.get('room_id')
        username = message.get('user', {}).get('username', 'Alguien')
        
        if not self.current_room or str(self.current_room) == str(room_id):
            print(f"\n[!] {username} ha {action} la sala")
    
    def disconnect_websocket(self):
        """Cierra la conexión WebSocket."""
        if self.ws_client:
            self.ws_client.stop()
            self.ws_client = None
            print("\n[+] Conexión WebSocket cerrada")
    
    def send_websocket_message(self, event_type, data=None):
        """Envía un mensaje a través del WebSocket."""
        if not self.ws_client or not hasattr(self.ws_client, 'running') or not self.ws_client.running:
            print("Error: No hay una conexión WebSocket activa")
            return False
        
        message = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'user_id': self.user_id,
            'username': self.username
        }
        
        if data:
            message.update(data)
        
        try:
            self.ws_client.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"Error al enviar mensaje WebSocket: {e}")
            return False
    
    def login(self, username, password):
        """Inicia sesión en la API."""
        endpoint = '/api/auth/login'
        data = {'username': username, 'password': password}
        
        status_code, response = self._make_request('post', endpoint, data=data)
        
        if status_code == 200:
            self.token = response.get('access_token')
            self.user_id = response.get('user_id')
            self.username = response.get('username')
            print(f"\n[+] Sesión iniciada como {self.username} (ID: {self.user_id}")
            
            # Conectar WebSocket después de iniciar sesión
            if input("¿Desea habilitar notificaciones en tiempo real? (s/n): ").lower() == 's':
                self.connect_websocket()
        
        return status_code, response
    
    def verify_token(self):
        """Verifica si el token actual es válido."""
        if not self.token:
            return 401, {'error': 'No hay token de autenticación'}
            
        endpoint = '/api/auth/verify'
        return self._make_request('post', endpoint)
    
    def get_current_user(self):
        """Obtiene la información del usuario actual."""
        endpoint = '/api/auth/me'
        return self._make_request('get', endpoint)
    
    def update_current_user(self, username=None, password=None):
        """Actualiza la información del usuario actual."""
        endpoint = '/api/auth/me'
        data = {}
        if username:
            data['username'] = username
        if password:
            data['password'] = password
            
        return self._make_request('put', endpoint, data=data)
    
    def get_user_profile(self, user_id):
        """Obtiene el perfil de un usuario por su ID."""
        endpoint = f'/api/user/{user_id}'
        return self._make_request('get', endpoint)
    
    def search_users(self, query, limit=10):
        """Busca usuarios por nombre."""
        endpoint = '/api/users/search'
        params = {'query': query, 'limit': limit}
        return self._make_request('get', endpoint, params=params)
    
    # Métodos para salas
    def get_rooms(self):
        """Obtiene todas las salas disponibles."""
        endpoint = '/api/rooms'
        return self._make_request('get', endpoint)
    
    def get_room(self, room_id):
        """Obtiene información de una sala específica."""
        endpoint = f'/api/rooms/{room_id}'
        return self._make_request('get', endpoint)
    
    def create_room(self, name, private=True):
        """Crea una nueva sala."""
        endpoint = '/api/rooms'
        data = {'nombre': name, 'privada': private}
        return self._make_request('post', endpoint, data=data)
    
    def join_room(self, room_id):
        """Se une a una sala."""
        endpoint = f'/api/rooms/{room_id}/join'
        status_code, response = self._make_request('post', endpoint)
        if status_code == 200:
            self.current_room = room_id
        return status_code, response
    
    def leave_room(self, room_id):
        """Abandona una sala."""
        endpoint = f'/api/rooms/{room_id}/leave'
        status_code, response = self._make_request('post', endpoint)
        if status_code == 200 and self.current_room == room_id:
            self.current_room = None
        return status_code, response
    
    def update_room(self, room_id, name=None, private=None):
        """Actualiza los detalles de una sala."""
        endpoint = f'/api/rooms/{room_id}'
        data = {}
        if name is not None:
            data['nombre'] = name
        if private is not None:
            data['privada'] = private
            
        return self._make_request('put', endpoint, data=data)
    
    def delete_room(self, room_id):
        """Elimina una sala."""
        endpoint = f'/api/rooms/{room_id}'
        return self._make_request('delete', endpoint)
    
    def get_room_members(self, room_id):
        """Obtiene los miembros de una sala."""
        endpoint = f'/api/rooms/{room_id}/members'
        return self._make_request('get', endpoint)
    
    # Métodos para mensajes
    def get_room_messages(self, room_id, before=None, limit=50):
        """Obtiene mensajes de una sala."""
        endpoint = f'/api/rooms/{room_id}/messages'
        params = {'limit': limit}
        if before:
            params['before'] = before
            
        return self._make_request('get', endpoint, params=params)
    
    def send_message(self, room_id, content):
        """Envía un mensaje a una sala."""
        # Si hay conexión WebSocket, usarla para enviar el mensaje en tiempo real
        if self.ws_client and hasattr(self.ws_client, 'running') and self.ws_client.running:
            success = self.send_websocket_message('send_message', {
                'room_id': room_id,
                'content': content
            })
            
            if success:
                return 200, {'status': 'success', 'message': 'Mensaje enviado (WebSocket)'}
            else:
                print("No se pudo enviar el mensaje por WebSocket, intentando por HTTP...")
        
        # Si no hay WebSocket o falló, usar HTTP
        endpoint = f'/api/rooms/{room_id}/messages'
        data = {'contenido': content}
        return self._make_request('post', endpoint, data=data)
    
    def get_message(self, message_id):
        """Obtiene un mensaje específico."""
        endpoint = f'/api/messages/{message_id}'
        return self._make_request('get', endpoint)
    
    def edit_message(self, message_id, content):
        """Edita un mensaje existente."""
        endpoint = f'/api/messages/{message_id}'
        data = {'contenido': content}
        return self._make_request('put', endpoint, data=data)
    
    def delete_message(self, message_id):
        """Elimina un mensaje."""
        endpoint = f'/api/messages/{message_id}'
        return self._make_request('delete', endpoint)

def print_response(status_code, response):
    """Muestra la respuesta de la API de forma formateada."""
    print(f"\n=== Respuesta ({status_code}) ===")
    if isinstance(response, dict) or isinstance(response, list):
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print(response)

def clear_screen():
    """Limpia la pantalla de la consola."""
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(api_client):
    """Muestra el menú principal."""
    while True:
        clear_screen()
        print("=== MENÚ PRINCIPAL ===")
        print(f"Usuario: {api_client.username if api_client.username else 'No autenticado'}")
        print(f"Sala actual: {api_client.current_room if api_client.current_room else 'Ninguna'}")
        print("\n1. Autenticación")
        print("2. Perfil de usuario")
        print("3. Salas")
        if api_client.current_room:
            print("4. Mensajes (sala actual)")
        print("0. Salir")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '0':
            print("¡Hasta luego!")
            break
        elif choice == '1':
            auth_menu(api_client)
        elif choice == '2':
            profile_menu(api_client)
        elif choice == '3':
            rooms_menu(api_client)
        elif choice == '4' and api_client.current_room:
            messages_menu(api_client)
        else:
            input("\nOpción no válida. Presione Enter para continuar...")

def auth_menu(api_client):
    """Muestra el menú de autenticación."""
    while True:
        clear_screen()
        print("=== AUTENTICACIÓN ===")
        print("1. Iniciar sesión")
        print("2. Verificar token")
        print("0. Volver al menú principal")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            username = input("\nUsuario: ").strip()
            password = input("Contraseña: ").strip()
            
            status_code, response = api_client.login(username, password)
            print_response(status_code, response)
            
            if status_code != 200:
                input("\nPresione Enter para continuar...")
        elif choice == '2':
            if not api_client.token:
                print("\nError: No hay token de autenticación")
            else:
                status_code, response = api_client.verify_token()
                print_response(status_code, response)
            
            input("\nPresione Enter para continuar...")
        else:
            input("\nOpción no válida. Presione Enter para continuar...")

def profile_menu(api_client):
    """Muestra el menú de perfil de usuario."""
    if not api_client.token:
        print("\nError: Debe iniciar sesión primero")
        input("Presione Enter para continuar...")
        return
    
    while True:
        clear_screen()
        print("=== PERFIL DE USUARIO ===")
        print("1. Ver mi perfil")
        print("2. Buscar usuarios")
        print("3. Ver perfil de usuario por ID")
        print("4. Actualizar mi perfil")
        print("0. Volver al menú principal")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            status_code, response = api_client.get_current_user()
            print_response(status_code, response)
            input("\nPresione Enter para continuar...")
        elif choice == '2':
            query = input("\nIngrese el nombre a buscar: ").strip()
            if len(query) < 2:
                print("La búsqueda debe tener al menos 2 caracteres")
            else:
                limit = input("Límite de resultados (por defecto 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                
                status_code, response = api_client.search_users(query, limit)
                print_response(status_code, response)
            
            input("\nPresione Enter para continuar...")
        elif choice == '3':
            user_id = input("\nIngrese el ID del usuario: ").strip()
            if user_id:
                status_code, response = api_client.get_user_profile(user_id)
                print_response(status_code, response)
            else:
                print("ID de usuario no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '4':
            print("\nDeje en blanco los campos que no desee actualizar")
            username = input("Nuevo nombre de usuario: ").strip() or None
            password = input("Nueva contraseña: ").strip() or None
            
            if username or password:
                status_code, response = api_client.update_current_user(username, password)
                print_response(status_code, response)
                
                if status_code == 200 and username:
                    api_client.username = username
            else:
                print("No se especificaron cambios")
            
            input("\nPresione Enter para continuar...")
        else:
            input("\nOpción no válida. Presione Enter para continuar...")

def rooms_menu(api_client):
    """Muestra el menú de salas."""
    if not api_client.token:
        print("\nError: Debe iniciar sesión primero")
        input("Presione Enter para continuar...")
        return
    
    while True:
        clear_screen()
        print("=== SALAS ===")
        print("1. Listar salas")
        print("2. Ver detalles de una sala")
        print("3. Crear sala")
        print("4. Unirse a una sala")
        print("5. Abandonar sala actual")
        print("6. Actualizar sala")
        print("7. Eliminar sala")
        print("8. Ver miembros de una sala")
        print("0. Volver al menú principal")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            status_code, response = api_client.get_rooms()
            print_response(status_code, response)
            input("\nPresione Enter para continuar...")
        elif choice == '2':
            room_id = input("\nIngrese el ID de la sala: ").strip()
            if room_id:
                status_code, response = api_client.get_room(room_id)
                print_response(status_code, response)
            else:
                print("ID de sala no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '3':
            name = input("\nNombre de la sala: ").strip()
            if name:
                private = input("¿Sala privada? (s/n): ").strip().lower() == 's'
                status_code, response = api_client.create_room(name, private)
                print_response(status_code, response)
            else:
                print("El nombre de la sala no puede estar vacío")
            
            input("\nPresione Enter para continuar...")
        elif choice == '4':
            room_id = input("\nIngrese el ID de la sala a la que desea unirse: ").strip()
            if room_id:
                if api_client.current_room:
                    print(f"Ya estás en la sala {api_client.current_room}. Debes salir primero.")
                else:
                    status_code, response = api_client.join_room(room_id)
                    print_response(status_code, response)
                    
                    if status_code == 200:
                        api_client.current_room = room_id
            else:
                print("ID de sala no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '5':
            if not api_client.current_room:
                print("\nNo estás en ninguna sala")
            else:
                room_id = api_client.current_room
                confirm = input(f"\n¿Está seguro de que desea abandonar la sala {room_id}? (s/n): ").strip().lower()
                if confirm == 's':
                    status_code, response = api_client.leave_room(room_id)
                    print_response(status_code, response)
                    
                    if status_code == 200:
                        api_client.current_room = None
            
            input("\nPresione Enter para continuar...")
        elif choice == '6':
            room_id = input("\nIngrese el ID de la sala a actualizar: ").strip()
            if room_id:
                print("\nDeje en blanco los campos que no desee actualizar")
                name = input("Nuevo nombre de la sala: ").strip() or None
                private_str = input("¿Hacer privada? (s/n/enter para no cambiar): ").strip().lower()
                private = {'s': True, 'n': False}.get(private_str, None)
                
                status_code, response = api_client.update_room(room_id, name, private)
                print_response(status_code, response)
            else:
                print("ID de sala no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '7':
            room_id = input("\nIngrese el ID de la sala a eliminar: ").strip()
            if room_id:
                confirm = input(f"¿Está seguro de que desea eliminar la sala {room_id}? (s/n): ").strip().lower()
                if confirm == 's':
                    status_code, response = api_client.delete_room(room_id)
                    print_response(status_code, response)
                    
                    if status_code == 200 and api_client.current_room == room_id:
                        api_client.current_room = None
            else:
                print("ID de sala no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '8':
            room_id = input("\nIngrese el ID de la sala: ").strip()
            if room_id:
                status_code, response = api_client.get_room_members(room_id)
                print_response(status_code, response)
            else:
                print("ID de sala no válido")
            
            input("\nPresione Enter para continuar...")
        else:
            input("\nOpción no válida. Presione Enter para continuar...")

def messages_menu(api_client):
    """Muestra el menú de mensajes."""
    if not api_client.token:
        print("\nError: Debe iniciar sesión primero")
        input("Presione Enter para continuar...")
        return
    
    if not api_client.current_room:
        print("\nError: Debe unirse a una sala primero")
        input("Presione Enter para continuar...")
        return
    
    room_id = api_client.current_room
    
    while True:
        clear_screen()
        print(f"=== MENSAJES (Sala: {room_id}) ===")
        print("1. Ver mensajes recientes")
        print("2. Enviar mensaje")
        print("3. Ver mensaje por ID")
        print("4. Editar mensaje")
        print("5. Eliminar mensaje")
        print("0. Volver al menú principal")
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            limit = input("\nNúmero de mensajes a mostrar (por defecto 50): ").strip()
            limit = int(limit) if limit.isdigit() else 50
            
            before = input("ID del mensaje más reciente a cargar (opcional): ").strip()
            before = before if before else None
            
            status_code, response = api_client.get_room_messages(room_id, before, limit)
            print_response(status_code, response)
            
            input("\nPresione Enter para continuar...")
        elif choice == '2':
            content = input("\nMensaje: ").strip()
            if content:
                status_code, response = api_client.send_message(room_id, content)
                print_response(status_code, response)
            else:
                print("El mensaje no puede estar vacío")
            
            input("\nPresione Enter para continuar...")
        elif choice == '3':
            message_id = input("\nIngrese el ID del mensaje: ").strip()
            if message_id:
                status_code, response = api_client.get_message(message_id)
                print_response(status_code, response)
            else:
                print("ID de mensaje no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '4':
            message_id = input("\nIngrese el ID del mensaje a editar: ").strip()
            if message_id:
                content = input("Nuevo contenido del mensaje: ").strip()
                if content:
                    status_code, response = api_client.edit_message(message_id, content)
                    print_response(status_code, response)
                else:
                    print("El contenido del mensaje no puede estar vacío")
            else:
                print("ID de mensaje no válido")
            
            input("\nPresione Enter para continuar...")
        elif choice == '5':
            message_id = input("\nIngrese el ID del mensaje a eliminar: ").strip()
            if message_id:
                confirm = input(f"¿Está seguro de que desea eliminar el mensaje {message_id}? (s/n): ").strip().lower()
                if confirm == 's':
                    status_code, response = api_client.delete_message(message_id)
                    print_response(status_code, response)
            else:
                print("ID de mensaje no válido")
            
            input("\nPresione Enter para continuar...")
        else:
            input("\nOpción no válida. Presione Enter para continuar...")

def setup_signal_handlers(api_client):
    """Configura los manejadores de señales para una salida limpia."""
    def signal_handler(sig, frame):
        print("\nCerrando el cliente...")
        api_client.disconnect_websocket()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

def main():
    import sys
    import argparse
    
    # Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Cliente para la API de chat')
    parser.add_argument('--url', default='https://192.168.1.10:11443',
                      help='URL base de la API (por defecto: https://192.168.1.10:11443)')
    parser.add_argument('--no-ssl-verify', action='store_false', dest='verify_ssl',
                      help='Desactivar verificación SSL')
    parser.add_argument('--websocket', action='store_true',
                      help='Habilitar WebSocket automáticamente')
    
    args = parser.parse_args()
    
    # Crear cliente de la API
    api_client = APIClient(args.url, verify_ssl=args.verify_ssl)
    
    # Configurar manejadores de señales
    setup_signal_handlers(api_client)
    
    # Mostrar banner
    print("""
    ███████╗██╗██╗     ███████╗███╗   ██╗██████╗  █████╗ 
    ██╔════╝██║██║     ██╔════╝████╗  ██║██╔══██╗██╔══██╗
    ███████╗██║██║     █████╗  ██╔██╗ ██║██║  ██║███████║
    ╚════██║██║██║     ██╔══╝  ██║╚██╗██║██║  ██║██╔══██║
    ███████║██║███████╗███████╗██║ ╚████║██████╔╝██║  ██║
    ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝
    Cliente de chat interactivo - Silenda
    """)
    
    # Ejecutar menú principal
    try:
        # Si se especificó --websocket, intentar conectar después del login
        if args.websocket:
            def auto_connect_ws():
                import time
                time.sleep(1)  # Esperar un poco después del login
                if api_client.token:
                    print("\nConectando con WebSocket...")
                    api_client.connect_websocket()
            
            # Iniciar el menú principal
            import threading
            threading.Thread(target=auto_connect_ws, daemon=True).start()
        
        main_menu(api_client)
    except KeyboardInterrupt:
        print("\n\n¡Hasta luego!")
        api_client.disconnect_websocket()
        sys.exit(0)

if __name__ == "__main__":
    main()
