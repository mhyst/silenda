# Documentación de la API de Mensajería

## Tabla de Contenidos
- [1. Autenticación](#1-autenticación)
- [2. WebSocket Connection](#2-websocket-connection)
- [3. Eventos WebSocket](#3-eventos-websocket)
  - [Eventos del Cliente](#eventos-del-cliente-enviados-por-el-frontend)
  - [Eventos del Servidor](#eventos-del-servidor-recibidos-por-el-frontend)
- [4. REST API](#4-rest-api)
- [5. Códigos de Estado HTTP](#5-códigos-de-estado-http)
- [6. Manejo de Errores](#6-manejo-de-errores)
- [7. Consideraciones de Implementación](#7-consideraciones-de-implementación)

## 1. Autenticación

### Login
- **Método**: `POST`
- **Ruta**: `/api/auth/login`
- **Body**:
  ```json
  {
    "username": "usuario",
    "password": "contraseña123"
  }
  ```
- **Respuesta exitosa**:
  ```json
  {
    "token": "jwt.token.aqui",
    "user": {
      "id": "user123",
      "name": "Nombre Usuario",
      "email": "usuario@ejemplo.com"
    }
  }
  ```

## 2. WebSocket Connection

- **URL**: `wss://tudominio.com/ws` (o `ws://` para desarrollo)
- **Autenticación**: El token JWT debe enviarse en el header `Authorization: Bearer <token>`

## 3. Eventos WebSocket

### Eventos del Cliente (enviados por el frontend)

#### Unirse a una conversación
```json
{
  "event": "join_conversation",
  "data": {
    "conversationId": "conv123"
  }
}
```

#### Enviar mensaje
```json
{
  "event": "send_message",
  "data": {
    "conversationId": "conv123",
    "content": "Hola, ¿cómo estás?",
    "timestamp": "2025-07-10T07:17:19Z"
  }
}
```

#### Marcar mensaje como leído
```json
{
  "event": "mark_as_read",
  "data": {
    "messageId": "msg456",
    "conversationId": "conv123"
  }
}
```

#### Escribiendo...
```json
{
  "event": "typing",
  "data": {
    "conversationId": "conv123",
    "isTyping": true
  }
}
```

### Eventos del Servidor (recibidos por el frontend)

#### Nuevo mensaje
```json
{
  "event": "new_message",
  "data": {
    "id": "msg789",
    "conversationId": "conv123",
    "senderId": "user456",
    "content": "Hola, ¿cómo estás?",
    "timestamp": "2025-07-10T07:17:20Z",
    "status": "delivered"
  }
}
```

#### Mensaje leído
```json
{
  "event": "message_read",
  "data": {
    "messageId": "msg789",
    "conversationId": "conv123",
    "readBy": "user123",
    "readAt": "2025-07-10T07:18:00Z"
  }
}
```

#### Usuario escribiendo
```json
{
  "event": "user_typing",
  "data": {
    "conversationId": "conv123",
    "userId": "user456",
    "isTyping": true
  }
}
```

#### Estado de conexión
```json
{
  "event": "connection_status",
  "data": {
    "userId": "user456",
    "isOnline": true,
    "lastSeen": "2025-07-10T07:17:30Z"
  }
}
```

## 4. REST API

### Obtener conversaciones
- **Método**: `GET`
- **Ruta**: `/api/conversations`
- **Query Params**:
  - `limit`: Número de conversaciones a devolver (opcional)
  - `offset`: Número de conversaciones a saltar (opcional)
- **Respuesta**:
  ```json
  {
    "conversations": [
      {
        "id": "conv123",
        "participants": ["user123", "user456"],
        "lastMessage": {
          "content": "Hola, ¿cómo estás?",
          "senderId": "user456",
          "timestamp": "2025-07-10T07:17:20Z"
        },
        "unreadCount": 2
      }
    ]
  }
  ```

### Obtener mensajes de una conversación
- **Método**: `GET`
- **Ruta**: `/api/conversations/:conversationId/messages`
- **Query Params**:
  - `before`: Fecha ISO para obtener mensajes anteriores a esta fecha (opcional)
  - `limit`: Número de mensajes a devolver (por defecto: 50)
- **Respuesta**:
  ```json
  {
    "messages": [
      {
        "id": "msg789",
        "conversationId": "conv123",
        "senderId": "user456",
        "content": "Hola, ¿cómo estás?",
        "timestamp": "2025-07-10T07:17:20Z",
        "status": "read"
      }
    ],
    "hasMore": true
  }
  ```

### Crear nueva conversación
- **Método**: `POST`
- **Ruta**: `/api/conversations`
- **Body**:
  ```json
  {
    "participantIds": ["user456", "user789"]
  }
  ```
- **Respuesta**:
  ```json
  {
    "id": "conv124",
    "participants": ["user123", "user456", "user789"],
    "createdAt": "2025-07-10T07:20:00Z"
  }
  ```

## 5. Códigos de Estado HTTP

- `200 OK`: Petición exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Error en los datos de la petición
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: No autorizado
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## 6. Manejo de Errores

Todas las respuestas de error siguen el formato:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Descripción legible del error",
    "details": {}
  }
}
```

## 7. Consideraciones de Implementación

1. **Reconexión**: El cliente debe manejar la reconexión automática si la conexión WebSocket se pierde.
2. **Mensajes no enviados**: Almacenar localmente los mensajes que no se pudieron enviar e intentar reenviarlos.
3. **Estado de conexión**: Mostrar indicadores visuales cuando el usuario está desconocido o tiene problemas de conexión.
4. **Notificaciones**: Usar la API de notificaciones del navegador para mensajes recibidos cuando la aplicación está en segundo plano.
5. **Optimización**: Implementar paginación para cargar mensajes antiguos bajo demanda.
6. **Persistencia**: Almacenar mensajes localmente para acceso sin conexión.
7. **Sincronización**: Sincronizar el estado local con el servidor al reconectar.

---

*Documentación actualizada el 10 de Julio de 2025*
