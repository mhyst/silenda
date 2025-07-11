# Documentación de WebSockets

La aplicación utiliza Socket.IO para gestionar conexiones en tiempo real mediante WebSockets. Esto permite una comunicación bidireccional eficiente entre el cliente y el servidor.

## Eventos de Socket.IO

### Conexión

- **Evento**: `connect`
- **Descripción**: Se activa cuando un cliente se conecta al servidor.
- **Acciones**:
  1. Decodificar el token JWT pasado como parámetro en la consulta.
  2. Obtener la identidad del usuario desde el token.
  3. Unir al usuario a una sala privada basada en su identidad.
  4. Unir al usuario a todas las salas de chat a las que pertenece.
- **Impresión en consola**: "Usuario [identidad] conectado y unido a sus salas."

### Desconexión

- **Evento**: `disconnect`
- **Descripción**: Se activa cuando un cliente se desconecta.
- **Acciones**:
  1. Obtener la identidad del usuario desde el token.
  2. Sacar al usuario de su sala privada.
  3. Sacar al usuario de todas las salas de chat a las que pertenece.
- **Impresión en consola**: "Usuario [identidad] desconectado y liberado de sus salas."

### Join Room

- **Evento**: `join_room`
- **Descripción**: Permite a un usuario unirse a una sala específica.
- **Datos recibidos**: `room_id` (ID de la sala a unirse)
- **Acciones**: Une al usuario a la sala especificada.
- **Impresión en consola**: "Usuario [identidad] unido a la sala [room_id]"

### Leave Room

- **Evento**: `leave_room`
- **Descripción**: Permite a un usuario salir de una sala específica.
- **Datos recibidos**: `room_id` (ID de la sala de la cual salir)
- **Acciones**: Saca al usuario de la sala especificada.
- **Impresión en consola**: "Usuario [identidad] liberado de la sala [room_id]"

### Nuevo Mensaje

- **Evento**: `nuevo_mensaje`
- **Descripción**: Se activa al enviar un nuevo mensaje en una sala.
- **Datos recibidos**: `data` (datos del mensaje)
- **Impresión en consola**: "Usuario [identidad] envio un mensaje: [data]"

### Mensaje Eliminado

- **Evento**: `mensaje_eliminado`
- **Descripción**: Se activa al eliminar un mensaje existente.
- **Datos recibidos**: `data` (datos del mensaje eliminado)
- **Impresión en consola**: "Usuario [identidad] elimino un mensaje: [data]"

### Mensaje Actualizado

- **Evento**: `mensaje_actualizado`
- **Descripción**: Se activa al actualizar un mensaje existente.
- **Datos recibidos**: `data` (datos del mensaje actualizado)
- **Impresión en consola**: "Usuario [identidad] actualizo un mensaje: [data]"

## Consideraciones

- Durante la conexión, el servidor autentica al usuario usando un token JWT que se espera que el cliente pase como parámetro de consulta.
- Cada usuario tiene su propia sala privada basada en su identidad para manejar mensajes personales o directos.
- A pesar de la funcionalidad de WebSockets, la autenticación y autorización siguen dependiendo de los tokens JWT, por lo que se asume que el cliente maneja estos tokens de manera segura.

Este documento proporciona un resumen de cómo se manejan los eventos de WebSockets en la aplicación y qué acciones específicas se llevan a cabo cuando se activan estos eventos.