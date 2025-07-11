#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import requests
import os
import ssl
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para las sesiones

from datetime import datetime as dt

def datetimeformat(value, format='%d/%m/%Y %H:%M'):
    """Filtro para formatear fechas en las plantillas.
    
    Args:
        value: Valor de fecha a formatear (puede ser string, datetime o date)
        format: Formato de salida (por defecto: 'dd/mm/yyyy HH:MM')
    """
    if value is None:
        return ''
    
    # Si es un string, intentar convertirlo a datetime
    if isinstance(value, str):
        try:
            # Intentar con formato ISO
            if 'T' in value:
                value = dt.fromisoformat(value.replace('Z', '+00:00'))
            else:
                # Intentar con formato de fecha simple
                value = dt.strptime(value, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return value
    
    # Si es un objeto date o datetime, formatearlo
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    
    return value

# Filtro personalizado para convertir datos a JSON en las plantillas
def to_json_filter(data):
    return json.dumps(data, ensure_ascii=False)

# Aplicar filtros a la aplicación Flask
app.jinja_env.filters['tojson'] = to_json_filter
app.jinja_env.filters['datetimeformat'] = datetimeformat

# Configuración de la API
API_BASE_URL = 'https://90.175.164.116:11443'  # Ajusta según sea necesario

# Configuración de SSL
SSL_VERIFY = False  # Cambiar a True en producción con certificados válidos

# Configurar la sesión de requests para manejar reintentos
session_requests = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
)
session_requests.mount('https://', HTTPAdapter(max_retries=retry_strategy))

# Decorador para verificar si el usuario está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta de inicio
@app.route('/')
def index():
    return redirect(url_for('login'))

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validar que se hayan proporcionado credenciales
        if not username or not password:
            return render_template('login.html', error='Por favor ingrese usuario y contraseña')
        
        # Intentar autenticación con la API
        try:
            response = session_requests.post(
                f'{API_BASE_URL}/api/auth/login',
                json={'username': username, 'password': password},
                verify=SSL_VERIFY,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Almacenar el token en la sesión
                session['access_token'] = data['access_token']
                session['user_id'] = data['user_id']
                session['username'] = data['username']
                return redirect(url_for('chat'))
            else:
                return render_template('login.html', error='Usuario o contraseña incorrectos')
                
        except requests.exceptions.RequestException as e:
            return render_template('login.html', error='Error al conectar con el servidor')
    
    return render_template('login.html')

# Ruta del chat (requiere autenticación)
def make_api_request(method, endpoint, data=None, json_data=None):
    """
    Realiza una petición a la API con el token de autenticación.
    
    Args:
        method: Método HTTP (get, post, put, delete)
        endpoint: Endpoint de la API (sin la URL base)
        data: Datos del formulario (opcional)
        json_data: Datos en formato JSON (opcional)
        
    Returns:
        Tupla con (código de estado, datos de la respuesta)
    """
    headers = {
        'Authorization': f"Bearer {session.get('access_token')}",
        'Content-Type': 'application/json'
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.lower() == 'get':
            response = session_requests.get(
                url,
                headers=headers,
                verify=SSL_VERIFY,
                timeout=10
            )
        elif method.lower() == 'post':
            response = session_requests.post(
                url,
                headers=headers,
                json=json_data,
                verify=SSL_VERIFY,
                timeout=10
            )
        elif method.lower() == 'put':
            response = session_requests.put(
                url,
                headers=headers,
                json=json_data,
                verify=SSL_VERIFY,
                timeout=10
            )
        elif method.lower() == 'delete':
            response = session_requests.delete(
                url,
                headers=headers,
                verify=SSL_VERIFY,
                timeout=10
            )
        else:
            return 405, {'error': 'Método no permitido'}
            
        return response.status_code, response.json() if response.content else {}
        
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición a la API: {str(e)}")
        return 500, {'error': 'Error al conectar con el servidor'}

@app.route('/chat')
@login_required
def chat():
    # Obtener las salas del usuario
    status_code, response_data = make_api_request('get', '/api/rooms')
    
    if status_code == 200:
        rooms = response_data
    else:
        # Si hay un error, mostramos un array vacío y pasamos el mensaje de error
        rooms = []
        error_message = response_data.get('msg', 'Error al cargar las salas')
        return render_template('chat.html', 
                            username=session.get('username'),
                            rooms=rooms,
                            error=error_message)
    
    return render_template('chat.html', 
                         username=session.get('username'),
                         rooms=rooms)

# Ruta de cierre de sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Configuración para desarrollo con SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')  # Asegúrate de tener estos archivos
    
    app.run(
        host='0.0.0.0',
        port=11444,  # Puerto para el frontend
        debug=True,
        ssl_context=context
    )
