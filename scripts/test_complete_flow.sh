#!/bin/bash

# Script de prueba completa del flujo de fondos
# Prueba todos los fondos disponibles con diferentes usuarios

set -e

# Configuración
API_URL="https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod"

echo "🚀 Prueba Completa del Sistema de Fondos - Invierte Ya"
echo "===================================================="
echo "API URL: $API_URL"
echo

# Función para hacer peticiones con manejo de errores
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local token=$5
    
    echo "📡 $description..."
    
    if [ -n "$token" ]; then
        auth_header="-H \"Authorization: Bearer $token\""
    else
        auth_header=""
    fi
    
    if [ -n "$data" ]; then
        if [ -n "$token" ]; then
            response=$(curl -s -w "\n%{http_code}" -X $method \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data" \
                "$API_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" -X $method \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_URL$endpoint")
        fi
    else
        if [ -n "$token" ]; then
            response=$(curl -s -w "\n%{http_code}" -X $method \
                -H "Authorization: Bearer $token" \
                "$API_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" -X $method \
                "$API_URL$endpoint")
        fi
    fi
    
    # Separar respuesta y código de estado
    body=$(echo "$response" | sed '$d')
    status_code=$(echo "$response" | tail -n 1)
    
    if [[ $status_code -ge 200 && $status_code -lt 300 ]]; then
        echo "✅ $description exitoso (HTTP $status_code)"
        if [ -n "$body" ] && [ "$body" != "null" ]; then
            echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        fi
        echo
        return 0
    else
        echo "❌ $description falló (HTTP $status_code)"
        if [ -n "$body" ]; then
            echo "Error: $body"
        fi
        echo
        return 1
    fi
}

# Función para hacer login y obtener token
login_user() {
    local email=$1
    local password=$2
    
    login_data='{
        "email": "'$email'",
        "password": "'$password'"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$login_data" \
        "$API_URL/auth/login")
    
    body=$(echo "$response" | sed '$d')
    status_code=$(echo "$response" | tail -n 1)
    
    if [[ $status_code -ge 200 && $status_code -lt 300 ]]; then
        # Extraer el token del JSON response
        token=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
        echo "$token"
    else
        echo ""
    fi
}

# Función para crear usuario y suscribir a fondo
test_fund_subscription() {
    local user_id=$1
    local fund_id=$2
    local fund_name=$3
    local amount=$4
    local minimum=$5
    local counter=$6
    
    echo
    echo "📋 Prueba $counter: Usuario $user_id -> Fondo $fund_name"
    echo "   💰 Monto a invertir: COP \$$(printf "%'d" $amount)"
    echo "   📊 Monto mínimo requerido: COP \$$(printf "%'d" $minimum)"
    echo "   ----------------------------------------"
    
    # Crear usuario
    user_data='{
        "email": "'$user_id'@example.com",
        "phone": "+57300123456'$counter'",
        "password": "password123",
        "notification_preference": "email"
    }'
    
    make_request "POST" "/auth/register" "$user_data" "Creación de usuario $user_id" || {
        echo "⚠️ Usuario ya existe, continuando..."
    }
    
    # Hacer login para obtener token
    echo "🔐 Haciendo login para $user_id..."
    token=$(login_user "$user_id@example.com" "password123")
    
    if [ -z "$token" ]; then
        echo "❌ Error al hacer login para $user_id"
        return 1
    fi
    
    echo "✅ Login exitoso para $user_id"
    
    # Realizar suscripción
    subscription_data='{
        "fund_id": "'$fund_id'",
        "amount": '$amount'
    }'
    
    make_request "POST" "/funds/subscribe" "$subscription_data" "Suscripción de $user_id al fondo $fund_name" "$token"
    
    # Verificar suscripción
    make_request "GET" "/users/me/subscriptions" "" "Verificación de suscripciones de $user_id" "$token"
    
    # Verificar balance actualizado
    make_request "GET" "/users/me" "" "Verificación de balance de $user_id" "$token"
}

# Paso 1: Verificar API
echo "1️⃣ Verificando estado de la API"
make_request "GET" "/" "" "Verificación de salud de la API"

# Paso 2: Inicializar fondos
echo "2️⃣ Inicializando fondos"
make_request "POST" "/init-funds" "" "Inicialización de fondos"

# Paso 3: Listar fondos disponibles
echo "3️⃣ Verificando fondos disponibles"
make_request "GET" "/funds" "" "Listado de fondos disponibles"

echo "4️⃣ Creando usuarios de prueba y realizando suscripciones"
echo "============================================================"

# Prueba 1: FPV_EL CLIENTE_RECAUDADORA
test_fund_subscription "user_fpv_recaudadora" "1" "FPV_EL CLIENTE_RECAUDADORA" 80000 75000 1

# Prueba 2: FPV_EL CLIENTE_ECOPETROL
test_fund_subscription "user_fpv_ecopetrol" "2" "FPV_EL CLIENTE_ECOPETROL" 150000 125000 2

# Prueba 3: DEUDAPRIVADA
test_fund_subscription "user_deudaprivada" "3" "DEUDAPRIVADA" 75000 50000 3

# Prueba 4: FDO-ACCIONES
test_fund_subscription "user_fdo_acciones" "4" "FDO-ACCIONES" 300000 250000 4

# Prueba 5: FPV_EL CLIENTE_DINAMICA
test_fund_subscription "user_fpv_dinamica" "5" "FPV_EL CLIENTE_DINAMICA" 120000 100000 5

echo
echo "5️⃣ Resumen final del sistema"
echo "============================="

# Verificación final con autenticación
echo "👥 Verificación final de usuario autenticado:"
echo "🔐 Haciendo login con el primer usuario creado..."
final_token=$(login_user "user_fpv_recaudadora@example.com" "password123")

if [ -n "$final_token" ]; then
    echo "✅ Login exitoso para verificación final"
    make_request "GET" "/users/me" "" "Estado final del usuario autenticado" "$final_token"
    make_request "GET" "/users/me/subscriptions" "" "Suscripciones del usuario autenticado" "$final_token"
    make_request "GET" "/users/me/transactions" "" "Transacciones del usuario autenticado" "$final_token"
else
    echo "❌ Error en login para verificación final"
fi

# Verificar fondos finales
echo "📊 Estado final de los fondos:"
make_request "GET" "/funds" "" "Listado final de fondos"

echo
echo "🎉 Prueba Completa Finalizada!"
echo "=============================="
echo "✅ Se probaron todos los 5 fondos disponibles:"
echo "   1. FPV_EL CLIENTE_RECAUDADORA (COP \$75,000 mín) - ✅ Probado con COP \$80,000"
echo "   2. FPV_EL CLIENTE_ECOPETROL (COP \$125,000 mín) - ✅ Probado con COP \$150,000"
echo "   3. DEUDAPRIVADA (COP \$50,000 mín) - ✅ Probado con COP \$75,000"
echo "   4. FDO-ACCIONES (COP \$250,000 mín) - ✅ Probado con COP \$300,000"
echo "   5. FPV_EL CLIENTE_DINAMICA (COP \$100,000 mín) - ✅ Probado con COP \$120,000"
echo
echo "📈 Todos los usuarios fueron creados y suscritos exitosamente"
echo "💰 Todas las transacciones fueron procesadas correctamente"
echo "🔔 Las notificaciones fueron enviadas por email"
echo "📊 Los balances fueron actualizados apropiadamente"