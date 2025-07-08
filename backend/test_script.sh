#!/bin/bash

# Configuración
API_BASE="${1:-https://192.168.1.10:11443}"
USERNAME="${2:-mhyst}"
PASSWORD="${3:-telojuro12}"

# Archivos temporales
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"; exit' EXIT INT TERM

# Archivos temporales
TEMP_LOGIN_RESPONSE="$TEMP_DIR/login.json"
TEMP_VERIFY_RESPONSE="$TEMP_DIR/verify.json"
TEMP_USER_PROFILE_RESPONSE="$TEMP_DIR/profile.json"
TEMP_USER_SEARCH_RESPONSE="$TEMP_DIR/search.json"
TEMP_ROOMS_RESPONSE="$TEMP_DIR/rooms.json"
TEMP_ROOM_RESPONSE="$TEMP_DIR/room.json"
TEMP_MESSAGES_RESPONSE="$TEMP_DIR/messages.json"
TEMP_MESSAGE_RESPONSE="$TEMP_DIR/message.json"
TEMP_UPDATE_RESPONSE="$TEMP_DIR/update.json"
TEMP_DELETE_RESPONSE="$TEMP_DIR/delete.json"

# Función para mostrar respuestas
show_response() {
    echo -e "\n=== $1 ==="
    echo "URL: $2"
    echo "Método: $3"
    echo "Código de estado: $4"
    echo "Respuesta:"
    
    local response_file="$5"
    
    if [ -s "$response_file" ]; then
        if jq -e . >/dev/null 2>&1 < "$response_file"; then
            # Es un JSON válido, mostrarlo con formato
            jq . < "$response_file"
        else
            # No es un JSON, mostrarlo como texto plano
            cat "$response_file"
            echo -e "\n[Nota: La respuesta no es un JSON válido]"
        fi
    else
        echo "[La respuesta está vacía]"
    fi
    
    echo ""
}

# Función para hacer peticiones HTTP
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"  # JSON data para POST/PUT
    local output_file="$4"
    
    local url="${API_BASE}${endpoint}"
    local curl_cmd=("curl" "-s" "-k" "-w" "\n%{http_code}" "-o" "$output_file")
    
    # Añadir el método HTTP
    curl_cmd+=("-X" "$method")
    
    # Añadir headers
    curl_cmd+=("-H" "Content-Type: application/json")
    
    # Añadir token de autenticación si está disponible
    if [ -n "$TOKEN" ]; then
        curl_cmd+=("-H" "Authorization: Bearer ${TOKEN}")
    fi
    
    # Añadir datos para POST/PUT
    if [ -n "$data" ] && { [ "$method" = "POST" ] || [ "$method" = "PUT" ] || [ "$method" = "PATCH" ]; }; then
        curl_cmd+=("-d" "$data")
    fi
    
    # Añadir la URL
    curl_cmd+=("$url")
    
    # Ejecutar el comando y capturar la salida
    local http_code=$("${curl_cmd[@]}" | tail -n1)
    
    # Mostrar la respuesta
    show_response "${method} ${endpoint}" "$url" "$method" "$http_code" "$output_file"
    
    # Devolver el código de estado HTTP
    return $((http_code >= 200 && http_code < 300 ? 0 : 1))
}

# Función para esperar entrada del usuario
press_enter() {
    echo -e "\n$1"
    read -p "Presione Enter para continuar..."
}

# Función para probar la autenticación
test_auth() {
    echo "=== PRUEBAS DE AUTENTICACIÓN ==="
    
    # 1. Iniciar sesión
    echo "\n1. Probando inicio de sesión..."
    make_request "POST" "/api/auth/login" "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}" "$TEMP_LOGIN_RESPONSE"
    
    # Extraer el token JWT
    TOKEN=$(jq -r '.access_token' < "$TEMP_LOGIN_RESPONSE" 2>/dev/null)
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "Error: No se pudo extraer el token de acceso de la respuesta"
        return 1
    fi
    
    # 2. Verificar token
    echo "\n2. Verificando token..."
    make_request "POST" "/api/auth/verify" "" "$TEMP_VERIFY_RESPONSE"
    
    # 3. Obtener perfil del usuario actual
    echo "\n3. Obteniendo perfil del usuario actual..."
    make_request "GET" "/api/auth/me" "" "$TEMP_USER_PROFILE_RESPONSE"
    
    # Extraer el ID de usuario
    USER_ID=$(jq -r '.id' < "$TEMP_USER_PROFILE_RESPONSE" 2>/dev/null)
    
    if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
        echo "Error: No se pudo extraer el ID de usuario de la respuesta"
        return 1
    fi
    
    press_enter "Pruebas de autenticación completadas."
}

# Función para probar los endpoints de usuario
test_users() {
    echo "=== PRUEBAS DE USUARIOS ==="
    
    if [ -z "$TOKEN" ] || [ -z "$USER_ID" ]; then
        echo "Error: Debe iniciar sesión primero"
        return 1
    fi
    
    # 1. Buscar usuarios
    echo "\n1. Buscando usuarios..."
    make_request "GET" "/api/users/search?query=${USERNAME:0:3}&limit=5" "" "$TEMP_USER_SEARCH_RESPONSE"
    
    # 2. Obtener perfil de usuario por ID
    echo "\n2. Obteniendo perfil de usuario (ID: $USER_ID)..."
    make_request "GET" "/api/user/$USER_ID" "" "$TEMP_USER_PROFILE_RESPONSE"
    
    # 3. Actualizar perfil de usuario
    echo "\n3. Actualizando perfil de usuario..."
    make_request "PUT" "/api/auth/me" "{\"username\": \"${USERNAME}_test\"}" "$TEMP_UPDATE_RESPONSE"
    
    # Revertir el cambio
    make_request "PUT" "/api/auth/me" "{\"username\": \"${USERNAME}\"}" "$TEMP_UPDATE_RESPONSE"
    
    press_enter "Pruebas de usuarios completadas."
}

# Función para probar los endpoints de salas
test_rooms() {
    echo "=== PRUEBAS DE SALAS ==="
    
    if [ -z "$TOKEN" ]; then
        echo "Error: Debe iniciar sesión primero"
        return 1
    fi
    
    # 1. Obtener todas las salas
    echo "\n1. Obteniendo todas las salas..."
    make_request "GET" "/api/rooms" "" "$TEMP_ROOMS_RESPONSE"
    
    # Extraer el ID de la primera sala si existe
    local room_id=$(jq -r 'if .[0] then .[0].id else empty end' < "$TEMP_ROOMS_RESPONSE" 2>/dev/null)
    
    # 2. Crear una nueva sala
    echo "\n2. Creando una nueva sala..."
    make_request "POST" "/api/rooms" "{\"nombre\": \"Sala de prueba $(date +%s)\", \"privada\": true}" "$TEMP_ROOM_RESPONSE"
    
    # Extraer el ID de la sala recién creada
    local new_room_id=$(jq -r '.id' < "$TEMP_ROOM_RESPONSE" 2>/dev/null)
    
    if [ -n "$new_room_id" ] && [ "$new_room_id" != "null" ]; then
        room_id=$new_room_id
    fi
    
    if [ -z "$room_id" ] || [ "$room_id" = "null" ]; then
        echo "Advertencia: No se pudo obtener un ID de sala para continuar con las pruebas"
        return 1
    fi
    
    # 3. Obtener detalles de la sala
    echo "\n3. Obteniendo detalles de la sala (ID: $room_id)..."
    make_request "GET" "/api/rooms/$room_id" "" "$TEMP_ROOM_RESPONSE"
    
    # 4. Unirse a la sala
    echo "\n4. Uniéndose a la sala (ID: $room_id)..."
    make_request "POST" "/api/rooms/$room_id/join" "" "$TEMP_UPDATE_RESPONSE"
    
    # 5. Enviar un mensaje a la sala
    echo "\n5. Enviando un mensaje a la sala..."
    make_request "POST" "/api/rooms/$room_id/messages" "{\"contenido\": \"Este es un mensaje de prueba $(date)\"}" "$TEMP_MESSAGE_RESPONSE"
    
    # Extraer el ID del mensaje
    local message_id=$(jq -r '.id' < "$TEMP_MESSAGE_RESPONSE" 2>/dev/null)
    
    # 6. Obtener mensajes de la sala
    echo "\n6. Obteniendo mensajes de la sala..."
    make_request "GET" "/api/rooms/$room_id/messages?limit=10" "" "$TEMP_MESSAGES_RESPONSE"
    
    # 7. Actualizar la sala (solo si es administrador)
    echo "\n7. Actualizando la sala..."
    make_request "PUT" "/api/rooms/$room_id" "{\"nombre\": \"Sala actualizada $(date +%s)\"}" "$TEMP_UPDATE_RESPONSE"
    
    # 8. Obtener miembros de la sala
    echo "\n8. Obteniendo miembros de la sala..."
    make_request "GET" "/api/rooms/$room_id/members" "" "$TEMP_ROOM_RESPONSE"
    
    # 9. Abandonar la sala
    echo "\n9. Abandonando la sala..."
    make_request "POST" "/api/rooms/$room_id/leave" "" "$TEMP_UPDATE_RESPONSE"
    
    # 10. Eliminar la sala (solo si es administrador)
    echo "\n10. Eliminando la sala..."
    make_request "DELETE" "/api/rooms/$room_id" "" "$TEMP_DELETE_RESPONSE"
    
    press_enter "Pruebas de salas completadas."
}

# Función para probar los endpoints de mensajes
test_messages() {
    echo "=== PRUEBAS DE MENSAJES ==="
    
    if [ -z "$TOKEN" ]; then
        echo "Error: Debe iniciar sesión primero"
        return 1
    fi
    
    # 1. Obtener todas las salas
    echo "\n1. Obteniendo salas disponibles..."
    make_request "GET" "/api/rooms" "" "$TEMP_ROOMS_RESPONSE"
    
    # Extraer el ID de la primera sala
    local room_id=$(jq -r 'if .[0] then .[0].id else empty end' < "$TEMP_ROOMS_RESPONSE" 2>/dev/null)
    
    if [ -z "$room_id" ] || [ "$room_id" = "null" ]; then
        echo "Advertencia: No hay salas disponibles. Creando una nueva sala..."
        make_request "POST" "/api/rooms" "{\"nombre\": \"Sala de prueba mensajes $(date +%s)\", \"privada\": false}" "$TEMP_ROOM_RESPONSE"
        room_id=$(jq -r '.id' < "$TEMP_ROOM_RESPONSE" 2>/dev/null)
    fi
    
    if [ -z "$room_id" ] || [ "$room_id" = "null" ]; then
        echo "Error: No se pudo obtener o crear una sala para las pruebas de mensajes"
        return 1
    fi
    
    # 2. Unirse a la sala
    echo "\n2. Uniéndose a la sala (ID: $room_id)..."
    make_request "POST" "/api/rooms/$room_id/join" "" "$TEMP_UPDATE_RESPONSE"
    
    # 3. Enviar un mensaje
    echo "\n3. Enviando un mensaje..."
    make_request "POST" "/api/rooms/$room_id/messages" "{\"contenido\": \"Mensaje de prueba $(date)\"}" "$TEMP_MESSAGE_RESPONSE"
    
    # Extraer el ID del mensaje
    local message_id=$(jq -r '.id' < "$TEMP_MESSAGE_RESPONSE" 2>/dev/null)
    
    if [ -z "$message_id" ] || [ "$message_id" = "null" ]; then
        echo "Advertencia: No se pudo obtener el ID del mensaje"
    else
        # 4. Obtener el mensaje por ID
        echo "\n4. Obteniendo mensaje por ID: $message_id"
        make_request "GET" "/api/messages/$message_id" "" "$TEMP_MESSAGE_RESPONSE"
        
        # 5. Editar el mensaje
        echo "\n5. Editando el mensaje..."
        make_request "PUT" "/api/messages/$message_id" "{\"contenido\": \"Mensaje editado $(date)\"}" "$TEMP_UPDATE_RESPONSE"
        
        # 6. Eliminar el mensaje
        echo "\n6. Eliminando el mensaje..."
        make_request "DELETE" "/api/messages/$message_id" "" "$TEMP_DELETE_RESPONSE"
    fi
    
    # 7. Obtener mensajes de la sala
    echo "\n7. Obteniendo mensajes de la sala..."
    make_request "GET" "/api/rooms/$room_id/messages?limit=10" "" "$TEMP_MESSAGES_RESPONSE"
    
    # 8. Abandonar la sala
    echo "\n8. Abandonando la sala..."
    make_request "POST" "/api/rooms/$room_id/leave" "" "$TEMP_UPDATE_RESPONSE"
    
    press_enter "Pruebas de mensajes completadas."
}

# Función para mostrar el menú
show_menu() {
    clear
    echo "=== MENÚ DE PRUEBAS DE LA API ==="
    echo "1. Probar autenticación"
    echo "2. Probar usuarios"
    echo "3. Probar salas"
    echo "4. Probar mensajes"
    echo "5. Ejecutar todas las pruebas"
    echo "0. Salir"
    echo ""
    echo "URL base: $API_BASE"
    echo "Usuario: $USERNAME"
    echo ""
}

# Función principal
main() {
    # Verificar si se proporcionaron argumentos para ejecutar pruebas específicas
    if [ "$1" = "--auth" ]; then
        test_auth
    elif [ "$1" = "--users" ]; then
        test_users
    elif [ "$1" = "--rooms" ]; then
        test_rooms
    elif [ "$1" = "--messages" ]; then
        test_messages
    elif [ "$1" = "--all" ]; then
        test_auth
        test_users
        test_rooms
        test_messages
    else
        # Mostrar menú interactivo
        while true; do
            show_menu
            read -p "Seleccione una opción: " choice
            
            case $choice in
                1) test_auth ;;
                2) test_users ;;
                3) test_rooms ;;
                4) test_messages ;;
                5) 
                    test_auth
                    test_users
                    test_rooms
                    test_messages
                    ;;
                0) exit 0 ;;
                *) echo "Opción no válida. Intente de nuevo." ;;
            esac
            
            if [ "$choice" != "0" ]; then
                read -p "Presione Enter para continuar..."
            fi
        done
    fi
}

# Ejecutar la función principal
main "$@"
    echo "Error: Falló al obtener el perfil del usuario"
    exit 1
fi

# Extraer el nombre de usuario para la búsqueda
USERNAME_FOR_SEARCH=$(jq -r '.username' < "$TEMP_LOGIN_RESPONSE" 2>/dev/null)
SEARCH_QUERY="${USERNAME_FOR_SEARCH:0:3}"  # Usar los primeros 3 caracteres del nombre de usuario

echo -e "\n=== Probando búsqueda de usuarios (query: $SEARCH_QUERY) ==="
HTTP_CODE=$(curl -s -k -w "\n%{http_code}" -o "$TEMP_USER_SEARCH_RESPONSE" -X GET \
    "${API_BASE}/api/users/search?query=${SEARCH_QUERY}&limit=5" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json"
)
HTTP_STATUS=$(echo "$HTTP_CODE" | tail -n1)
show_response "Búsqueda de usuarios" "$HTTP_STATUS" "$TEMP_USER_SEARCH_RESPONSE"

if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "Error: Falló la búsqueda de usuarios"
    exit 1
fi

echo -e "\n=== Pruebas completadas exitosamente ===\n"

# Mostrar resumen
echo "=== Resumen de pruebas ==="
echo "1. Inicio de sesión: Éxito"
echo "2. Verificación de token: Éxito"
echo "3. Obtención de perfil de usuario: $([ "$HTTP_STATUS" -eq 200 ] && echo "Éxito" || echo "Falló")"
SEARCH_COUNT=$(jq '.results | length' < "$TEMP_USER_SEARCH_RESPONSE" 2>/dev/null || echo "0")
echo "4. Búsqueda de usuarios: Encontrados $SEARCH_COUNT resultados"
