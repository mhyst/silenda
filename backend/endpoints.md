# Documentación de Endpoints

## Endpoints de Autenticación

### Login

- **Ruta**: `/api/auth/login`
- **Método**: `POST`
- **Descripción**: Inicia sesión de un usuario.
- **Cuerpo de la petición**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Respuestas**:
  - `200 OK`: Retorna un token JWT y la información del usuario.
  - `400 BAD REQUEST`: Si faltan credenciales.
  - `401 UNAUTHORIZED`: Si el usuario o la contraseña son incorrectos.

## Endpoints de Usuario

### Obtener Usuario Actual

- **Ruta**: `/api/user/me`
- **Método**: `GET`
- **Descripción**: Devuelve la información del usuario autenticado actualmente.
- **Encabezados**: 
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `200 OK`: Información del usuario.
  - `401 UNAUTHORIZED`: Si el token es inválido o ha expirado.

### Actualizar Usuario Actual

- **Ruta**: `/api/user/me`
- **Método**: `PATCH`
- **Descripción**: Actualiza el nombre de usuario y/o la contraseña del usuario autenticado.
- **Cuerpo de la petición**:
  ```json
  {
    "username": "string",  // Opcional
    "password": "string"   // Opcional
  }
  ```
- **Encabezados**: 
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `200 OK`: Usuario actualizado correctamente.
  - `400 BAD REQUEST`: Si los datos proporcionados no son válidos. 
  - `401 UNAUTHORIZED`: Si el token es inválido o ha expirado.

## Endpoints de Salas

### Obtener Salas

- **Ruta**: `/api/rooms`
- **Método**: `GET`
- **Descripción**: Obtiene todas las salas disponibles a las que pertenece el usuario autenticado.
- **Encabezados**: 
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `200 OK`: Lista de salas.

### Crear Sala

- **Ruta**: `/api/rooms`
- **Método**: `POST`
- **Descripción**: Crea una nueva sala.
- **Cuerpo de la petición**:
  ```json
  {
    "nombre": "string",
    "privada": true // Opcional (por defecto true)
  }
  ```
- **Encabezados**: 
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `201 CREATED`: Sala creada exitosamente.
  - `400 BAD REQUEST`: Si el nombre no está proporcionado.

## Endpoints de Mensajes

### Obtener Mensajes de una Sala

- **Ruta**: `/api/rooms/<int:room_id>/messages`
- **Método**: `GET`
- **Descripción**: Obtiene mensajes de una sala con paginación hacia atrás.
- **Parámetros de consulta**:
  - `before`: ID del mensaje a partir del cual cargar más antiguos (opcional)
  - `limit`: Número máximo de mensajes a devolver (máximo 100)
- **Encabezados**:
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `200 OK`: Lista de mensajes.

### Enviar Mensaje a una Sala

- **Ruta**: `/api/rooms/<int:room_id>/messages`
- **Método**: `POST`
- **Descripción**: Envía un mensaje a una sala.
- **Cuerpo de la petición**:
  ```json
  {
    "contenido": "string"
  }
  ```
- **Encabezados**: 
  - `Authorization: Bearer <JWT>`
- **Respuestas**:
  - `201 CREATED`: Mensaje creado exitosamente.
  - `400 BAD REQUEST`: Si el contenido no está proporcionado.