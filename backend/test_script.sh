#!/bin/bash

# Configuración
API_BASE="https://192.168.1.10:11443"
USERNAME="mhyst"
PASSWORD="telojuro12"

# Archivos temporales
TEMP_LOGIN_RESPONSE=$(mktemp)
TEMP_VERIFY_RESPONSE=$(mktemp)
TEMP_USER_PROFILE_RESPONSE=$(mktemp)
TEMP_USER_SEARCH_RESPONSE=$(mktemp)

# Función de limpieza
cleanup() {
    rm -f "$TEMP_LOGIN_RESPONSE" "$TEMP_VERIFY_RESPONSE" "$TEMP_USER_PROFILE_RESPONSE" "$TEMP_USER_SEARCH_RESPONSE"
}

# Registrar limpieza al salir
trap cleanup EXIT

# Función para mostrar respuestas
show_response() {
    echo -e "\n=== Respuesta HTTP ($1) ==="
    echo "Código de estado: $2"
    echo "Contenido:"
    if [ -s "$3" ]; then
        if jq -e . >/dev/null 2>&1 < "$3"; then
            # Es un JSON válido
            jq . < "$3"
        else
            # No es un JSON, mostrarlo como texto plano
            cat "$3"
            echo -e "\n[Nota: La respuesta no es un JSON válido]"
        fi
    else
        echo "[La respuesta está vacía]"
    fi
}

echo "=== Iniciando sesión en $API_BASE ==="
# Hacer la petición de login
HTTP_CODE=$(curl -s -k -w "\n%{http_code}" -o "$TEMP_LOGIN_RESPONSE" -X POST \
    "${API_BASE}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}"
)

# Extraer el código de estado
HTTP_STATUS=$(echo "$HTTP_CODE" | tail -n1)

show_response "Login" "$HTTP_STATUS" "$TEMP_LOGIN_RESPONSE"

# Verificar si el login fue exitoso
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "Error: Falló el inicio de sesión"
    exit 1
fi

# Extraer el token JWT
TOKEN=$(jq -r '.access_token' < "$TEMP_LOGIN_RESPONSE" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "Error: No se pudo extraer el token de acceso de la respuesta"
    exit 1
fi

echo -e "\n=== Token JWT obtenido ==="
echo "$TOKEN"

echo -e "\n=== Verificando token ==="
# Usar el token para verificar la autenticación
HTTP_CODE=$(curl -s -k -w "\n%{http_code}" -o "$TEMP_VERIFY_RESPONSE" -X POST \
    "${API_BASE}/api/auth/verify" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json"
)

# Extraer el código de estado
HTTP_STATUS=$(echo "$HTTP_CODE" | tail -n1)

show_response "Verificación" "$HTTP_STATUS" "$TEMP_VERIFY_RESPONSE"

if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "Error: Falló la verificación del token"
    exit 1
fi

# Obtener el ID del usuario actual para pruebas
USER_ID=$(jq -r '.user_id' < "$TEMP_LOGIN_RESPONSE" 2>/dev/null)

if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
    echo "Error: No se pudo extraer el ID de usuario de la respuesta de login"
    exit 1
fi

echo -e "\n=== Probando obtener perfil de usuario (ID: $USER_ID) ==="
HTTP_CODE=$(curl -s -k -w "\n%{http_code}" -o "$TEMP_USER_PROFILE_RESPONSE" -X GET \
    "${API_BASE}/api/user/${USER_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json"
)
HTTP_STATUS=$(echo "$HTTP_CODE" | tail -n1)
show_response "Perfil de usuario" "$HTTP_STATUS" "$TEMP_USER_PROFILE_RESPONSE"

if [ "$HTTP_STATUS" -ne 200 ]; then
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
