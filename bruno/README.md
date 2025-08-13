# Colección Bruno - Invierte Ya API

Esta colección de Bruno contiene todos los endpoints de la API de Invierte Ya para gestión de fondos de inversión.

## 🚀 Configuración Inicial

### 1. Instalar Bruno

Descarga e instala Bruno desde: https://www.usebruno.com/

### 2. Abrir la Colección

1. Abre Bruno
2. Selecciona "Open Collection"
3. Navega hasta la carpeta `bruno` de este proyecto
4. Selecciona la carpeta completa

### 3. Configurar Entornos

La colección incluye dos entornos:

- **Production**: `https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod`
- **Local**: `http://localhost:8000`

## 📋 Flujo de Pruebas Recomendado

### 1. Configuración Inicial
```
1. Initialize Funds (crear fondos de prueba)
2. API Info (verificar que la API esté funcionando)
3. Health Check (verificar estado de la API)
```

### 2. Autenticación
```
1. Auth/Register (crear una cuenta)
   - El token se guarda automáticamente en la variable `authToken`
2. Auth/Login (alternativamente, iniciar sesión con cuenta existente)
```

### 3. Gestión de Fondos
```
1. Funds/List Funds (ver fondos disponibles)
2. Funds/Subscribe to Fund (suscribirse a un fondo)
3. Funds/Cancel Subscription (cancelar suscripción)
```

### 4. Gestión de Dinero
```
1. Users/Deposit Money (depositar dinero en la cuenta)
   - Monto mínimo: 10,000 COP
   - Monto máximo: 10,000,000 COP
```

### 5. Información del Usuario
```
1. Users/Get User Info (información del perfil)
2. Users/Get User Transactions (historial de transacciones)
3. Users/Get User Subscriptions (suscripciones activas)
```

## 🔐 Autenticación

Los endpoints que requieren autenticación usan Bearer Token:

- El token se obtiene automáticamente al hacer Register o Login
- Se guarda en la variable de entorno `authToken`
- Se incluye automáticamente en las requests que lo requieren

## 📝 Variables de Entorno

### Variables Disponibles:
- `baseUrl`: URL base de la API
- `authToken`: Token JWT para autenticación (se actualiza automáticamente)

### Personalizar Variables:
1. Ve a la pestaña "Environments" en Bruno
2. Selecciona el entorno que deseas modificar
3. Actualiza las variables según sea necesario

## 🧪 Tests Automáticos

Cada endpoint incluye tests básicos que verifican:
- Código de estado HTTP correcto
- Estructura de respuesta esperada
- Guardado automático de tokens de autenticación

## 📚 Documentación

Cada endpoint incluye documentación detallada con:
- Descripción del endpoint
- Parámetros requeridos y opcionales
- Ejemplos de respuesta
- Códigos de error posibles

## 🔧 Solución de Problemas

### Error 401 (Unauthorized)
- Asegúrate de haber ejecutado Register o Login primero
- Verifica que la variable `authToken` tenga un valor

### Error 404 (Not Found)
- Verifica que el `baseUrl` sea correcto
- Asegúrate de que la API esté ejecutándose

### Error de Conexión
- Para entorno Local: Asegúrate de que el servidor local esté ejecutándose
- Para entorno Production: Verifica tu conexión a internet

## 📞 Soporte

Para más información sobre la API, consulta:
- Documentación Swagger: `/docs/swagger.yaml`
- Swagger UI: `/docs/swagger-ui.html`