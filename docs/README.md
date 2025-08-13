# 📚 Documentación de la API - Invierte Ya

Esta carpeta contiene la documentación completa de la API del sistema de fondos de inversión.

## 📁 Archivos de Documentación

### 🔧 `swagger.yaml`
Especificación OpenAPI 3.0.3 completa de la API que incluye:
- Definición de todos los endpoints
- **Sistema de autenticación JWT Bearer**
- Esquemas de datos (request/response)
- Ejemplos de uso
- Códigos de error
- Validaciones de parámetros
- **Ejemplos completos de request y response para todos los endpoints**
- **Casos de error comunes con mensajes descriptivos**

### 📄 `swagger.json`
La misma especificación OpenAPI 3.0.3 en formato JSON. Útil para:
- Integración con herramientas que prefieren JSON
- Importación en Postman, Insomnia u otras herramientas
- Generación automática de código cliente
- Procesamiento programático de la especificación

### 🌐 `swagger-ui.html`
Interfaz web interactiva para explorar y probar la API:
- Visualización amigable de la documentación
- Capacidad de probar endpoints directamente
- Ejemplos detallados de request y response
- Validación de parámetros
- Ejecutar llamadas de prueba con datos de ejemplo

## 🚀 Cómo Usar la Documentación

### Opción 1: Visualización Local
1. Abre el archivo `swagger-ui.html` en tu navegador web
2. La interfaz cargará automáticamente la especificación desde `swagger.yaml`
3. Explora los endpoints y prueba las funcionalidades

### Opción 2: Swagger Editor Online
1. Ve a [editor.swagger.io](https://editor.swagger.io/)
2. Copia y pega el contenido de `swagger.yaml` o `swagger.json`
3. Explora la documentación en el editor online

### Opción 3: Herramientas de Desarrollo
```bash
# Instalar swagger-ui-serve globalmente
npm install -g swagger-ui-serve

# Servir la documentación localmente
swagger-ui-serve swagger.yaml
```

### Opción 4: Integración Programática
- **Postman**: Importar `swagger.yaml` o `swagger.json` para generar una colección automáticamente
- **Insomnia**: Importar cualquiera de los dos formatos de especificación OpenAPI
- **VS Code**: Usar extensiones como "OpenAPI (Swagger) Editor"
- **Generadores de código**: Usar `swagger.json` con herramientas como Swagger Codegen

```bash
# Validar especificación
swagger-codegen validate -i docs/swagger.json

# Generar cliente en Python
swagger-codegen generate -i docs/swagger.json -l python -o ./client

# Generar cliente en JavaScript
swagger-codegen generate -i docs/swagger.json -l javascript -o ./js-client
```

## 🎯 Endpoints Disponibles

### 🏥 Salud & Estado
- `GET /` - Información básica de la API
- `GET /health` - Verificación de salud del sistema

### 🔐 Autenticación
- `POST /auth/register` - Registrar nuevo usuario y obtener token JWT
- `POST /auth/login` - Iniciar sesión y obtener token JWT

### 👥 Gestión de Usuarios
- `POST /users` - Crear nuevo usuario (legacy, usar /auth/register)
- `GET /users/{user_id}` - Obtener información de usuario 🔒

### 💰 Fondos de Inversión
- `GET /funds` - Listar todos los fondos disponibles
- `POST /funds/subscribe` - Suscribirse a un fondo 🔒
- `POST /funds/cancel` - Cancelar suscripción a un fondo 🔒

### 📊 Transacciones & Suscripciones
- `GET /users/{user_id}/transactions` - Historial de transacciones 🔒
- `GET /users/{user_id}/subscriptions` - Suscripciones activas 🔒

### ⚙️ Administración
- `POST /init-funds` - Inicializar fondos predefinidos (desarrollo)

> 🔒 = Requiere autenticación JWT Bearer token

## 💼 Fondos Disponibles

| ID | Nombre | Categoría | Monto Mínimo |
|----|--------|-----------|-------------|
| 1 | FPV_EL CLIENTE_RECAUDADORA | FPV | COP $75,000 |
| 2 | FPV_EL CLIENTE_ECOPETROL | FPV | COP $125,000 |
| 3 | DEUDAPRIVADA | FIC | COP $50,000 |
| 4 | FDO-ACCIONES | FIC | COP $250,000 |
| 5 | FPV_EL CLIENTE_DINAMICA | FPV | COP $100,000 |

### 📝 Categorías de Fondos
- **FPV**: Fondos de Pensiones Voluntarias
- **FIC**: Fondos de Inversión Colectiva

## 🔗 URLs de la API

### 🌐 Producción
```
https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod
```

### 🏠 Desarrollo Local
```
http://localhost:3000
```

## 📋 Ejemplos de Uso

La documentación Swagger incluye ejemplos completos para todos los endpoints. Aquí algunos casos principales:

### 🔐 Autenticación

#### Registrar Usuario
```bash
curl -X POST "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "juan_perez_123",
    "email": "juan.perez@email.com",
    "phone": "+573001234567",
    "password": "password123",
    "notification_preference": "EMAIL"
  }'
```

#### Iniciar Sesión
```bash
curl -X POST "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "juan_perez_123",
    "password": "password123"
  }'
```

### Usar Token JWT
Para endpoints protegidos, incluye el token en el header:
```bash
curl -X GET "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/users/juan_perez_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Crear Usuario (Legacy)
```bash
curl -X POST "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "juan_perez_123",
    "email": "juan.perez@email.com",
    "phone": "+573001234567",
    "notification_preference": "email"
  }'
```

### Suscribirse a un Fondo
```bash
curl -X POST "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/funds/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "juan_perez_123",
    "fund_id": "2",
    "amount": 125000
  }'
```

### Consultar Suscripciones
```bash
curl "https://jwnazw2b41.execute-api.us-east-1.amazonaws.com/Prod/users/juan_perez_123/subscriptions"
```

### Ejemplos Incluidos en Swagger
La documentación incluye ejemplos para:
- ✅ **Casos exitosos**: Respuestas típicas de operaciones correctas
- ❌ **Casos de error**: Validaciones fallidas, recursos no encontrados, errores del servidor
- 📊 **Diferentes escenarios**: Múltiples fondos, usuarios, montos de inversión
- 🔄 **Flujos completos**: Desde creación de usuario hasta cancelación de suscripciones

## 🛠️ Herramientas Recomendadas

### Para Desarrollo
- **Postman**: Importa el archivo `swagger.yaml` para crear una colección
- **Insomnia**: Soporta importación directa de OpenAPI
- **Thunder Client** (VS Code): Extensión para pruebas de API

### Para Documentación
- **Swagger Editor**: Editor online para OpenAPI
- **Redoc**: Generador de documentación alternativo
- **Stoplight Studio**: Herramienta visual para APIs

## 🔍 Validaciones y Reglas de Negocio

### Usuarios
- `user_id`: Alfanumérico, 3-50 caracteres
- `email`: Formato de email válido
- `phone`: Formato internacional (+país + número)
- Balance inicial: COP $500,000

### Suscripciones
- Monto mínimo según el fondo
- Usuario debe tener balance suficiente
- No puede estar ya suscrito al mismo fondo
- Fondo debe estar activo

### Transacciones
- Se registran automáticamente
- Incluyen balance antes y después
- Estado: `completed` o `failed`
- Generan notificaciones automáticas

## 🚨 Códigos de Error Comunes

La documentación incluye ejemplos detallados para todos los códigos de error:

| Código | Descripción |
|--------|-----------|
| 400 | Datos de entrada inválidos (formato de email, teléfono), saldo insuficiente, monto menor al mínimo, fondo no disponible |
| 404 | Usuario no encontrado, fondo no encontrado, suscripción no encontrada |
| 409 | Usuario ya existe en el sistema, usuario ya suscrito al fondo |
| 500 | Errores de base de datos, fallos en la inicialización, errores de conectividad |

Cada error incluye mensajes descriptivos en español para facilitar la depuración.

## 📞 Soporte

Para preguntas sobre la API o reportar problemas:
- **Email**: support@invierteya.com
- **Documentación**: Este directorio
- **Pruebas**: Ejecutar `./scripts/test_complete_flow.sh`

---

**Nota**: Esta documentación se actualiza automáticamente con cada cambio en la API. Siempre consulta la versión más reciente.