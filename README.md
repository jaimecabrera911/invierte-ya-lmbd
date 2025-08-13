# Invierte Ya - Sistema de Fondos

API para gestión de Fondos Voluntarios de Pensión (FPV) y Fondos de Inversión Colectiva (FIC) desarrollada con FastAPI y desplegada en AWS Lambda usando SAM.

## Características

- **FastAPI**: Framework web moderno y rápido para construir APIs
- **AWS Lambda**: Función serverless para escalabilidad automática
- **DynamoDB**: Base de datos NoSQL para almacenamiento de datos
- **API Gateway**: Gestión de endpoints y routing
- **SAM**: Serverless Application Model para deployment

## Estructura del Proyecto

```
invierte-ya-lmbd/
├── src/                    # Código fuente principal
│   ├── __init__.py        # Inicialización del paquete
│   └── app.py             # Aplicación FastAPI principal
├── tests/                 # Pruebas unitarias y de integración
├── docs/                  # Documentación del proyecto
├── scripts/               # Scripts de automatización
│   └── deploy.sh         # Script de despliegue automatizado
├── dependencies/          # Dependencias Python (no incluir en git)
├── .gitignore            # Archivos y directorios ignorados por git
├── README.md             # Este archivo
├── requirements.txt      # Dependencias Python
├── samconfig.toml        # Configuración de SAM
├── template.yaml         # Template de CloudFormation/SAM
└── project.config.json   # Configuración del proyecto
```

### Organización de Dependencias

Las dependencias se mantienen en el directorio `dependencies/` para:
- Mantener el directorio raíz limpio
- Facilitar la gestión de versiones
- Optimizar el proceso de despliegue
- Evitar conflictos con el código fuente

### Script de Despliegue

El script `scripts/deploy.sh` automatiza:
1. Copia temporal de dependencias al directorio raíz
2. Construcción y despliegue con SAM
3. Limpieza automática de archivos temporales
4. Manejo de errores y rollback

## Instalación

1. **Clona el repositorio**
   ```bash
   git clone <repository-url>
   cd invierte-ya-lmbd
   ```

2. **Instala las dependencias**
   ```bash
   # Instalar dependencias para Lambda (Linux x86_64)
   pip install -r requirements.txt -t dependencies/ --platform linux_x86_64 --python-version 3.9 --only-binary=:all:
   ```

3. **Configura AWS CLI**
   ```bash
   aws configure
   ```

4. **Despliega la aplicación**
   ```bash
   # Despliegue guiado (primera vez)
   ./scripts/deploy.sh guided
   
   # Despliegue rápido (dev por defecto)
   ./scripts/deploy.sh
   
   # Despliegue a un ambiente específico
   ./scripts/deploy.sh staging
   ```

## Prerrequisitos

- AWS CLI configurado
- SAM CLI instalado
- Python 3.12
- Cuenta de AWS con permisos para crear recursos Lambda, API Gateway e IAM

## Instalación de SAM CLI

```bash
# macOS
brew install aws-sam-cli

# Windows
choco install aws-sam-cli

# Linux
pip install aws-sam-cli
```

## Despliegue

### 1. Construir la aplicación

```bash
sam build
```

### 2. Desplegar en AWS

#### Primera vez (despliegue guiado)

```bash
sam deploy --guided
```

Esto te pedirá configurar:
- Stack name (ej: `invierte-ya-stack`)
- AWS Region (ej: `us-east-1`)
- Environment parameter (dev/staging/prod)
- Confirmación de cambios
- Permitir creación de roles IAM

#### Despliegues posteriores

```bash
sam deploy
```

#### Desplegar en un entorno específico

```bash
# Desarrollo
sam deploy --parameter-overrides Environment=dev

# Staging
sam deploy --parameter-overrides Environment=staging

# Producción
sam deploy --parameter-overrides Environment=prod
```

### 3. Probar la función

Después del despliegue, obtendrás una URL del API Gateway. Puedes probarla:

```bash
curl https://tu-api-gateway-url.execute-api.region.amazonaws.com/Prod/
```

## Desarrollo Local

### Ejecutar localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API localmente
sam local start-api
```

La API estará disponible en `http://localhost:3000`

### Invocar función localmente

```bash
sam local invoke InvierteYaFunction
```

## Comandos Útiles

### Ver logs de la función

```bash
sam logs -n InvierteYaFunction --stack-name tu-stack-name --tail
```

### Eliminar el stack

```bash
aws cloudformation delete-stack --stack-name tu-stack-name
```

### Validar template

```bash
sam validate
```

## Configuración del Template

El template de CloudFormation incluye:

- **Función Lambda**: Con FastAPI y Mangum como adaptador
- **API Gateway**: Para exponer la función como API REST
- **DynamoDB**: Tabla para almacenar datos de inversiones
- **Roles IAM**: Creados automáticamente con permisos para DynamoDB
- **Parámetros**: Environment y TableName configurables
- **Outputs**: URLs y ARNs para referencia

### Parámetros Configurables

- `Environment`: Entorno de despliegue (dev, staging, prod)
- `TableName`: Nombre base para la tabla de DynamoDB (default: invierte-ya-table)

### Recursos Creados

- Lambda Function: `invierte-ya-lambda-{Environment}`
- DynamoDB Table: `{TableName}-{Environment}`
- API Gateway: Automático por SAM
- IAM Role: Automático por SAM con permisos DynamoDB

## Estructura de la Función Lambda

La función utiliza:
- **FastAPI**: Framework web moderno para Python
- **Mangum**: Adaptador ASGI para AWS Lambda
- **Boto3**: SDK de AWS para Python
- **Pydantic**: Validación de datos y serialización

## API Endpoints

La API incluye los siguientes endpoints:

### Endpoints Básicos
- `GET /` - Información general de la API
- `GET /health` - Estado de salud de la API y DynamoDB

### Endpoints de Inversiones
- `POST /investments` - Crear una nueva inversión
- `GET /investments/{investment_id}` - Obtener una inversión por ID
- `GET /users/{user_id}/investments` - Obtener inversiones de un usuario
- `DELETE /investments/{investment_id}` - Eliminar una inversión

### Ejemplo de Uso

```bash
# Crear una inversión
curl -X POST "https://tu-api-url/investments" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": 1000.50,
    "investment_type": "acciones",
    "description": "Inversión en tecnología"
  }'

# Obtener inversiones de un usuario
curl "https://tu-api-url/users/user123/investments"

# Verificar estado de la API
curl "https://tu-api-url/health"
```

## Esquema de DynamoDB

La tabla de DynamoDB tiene la siguiente estructura:

- **Partition Key**: `id` (String) - ID único de la inversión
- **Global Secondary Index**: `UserIndex`
  - **Partition Key**: `user_id` (String)
  - **Sort Key**: `created_at` (String)

### Atributos de la Tabla

- `id`: ID único de la inversión (UUID)
- `user_id`: ID del usuario
- `amount`: Monto de la inversión (Number)
- `investment_type`: Tipo de inversión (String)
- `description`: Descripción opcional (String)
- `created_at`: Fecha de creación (ISO String)
- `updated_at`: Fecha de última actualización (ISO String)

## Troubleshooting

### Error de permisos
Asegúrate de que tu usuario AWS tenga permisos para:
- CloudFormation
- Lambda
- API Gateway
- IAM
- S3 (para artifacts)

### Error de build
Verifica que todas las dependencias estén en `requirements.txt`

### Error de timeout
Ajusta el timeout en el template si tu función necesita más tiempo

## Monitoreo

Los logs de la función están disponibles en CloudWatch Logs:
- Grupo: `/aws/lambda/invierte-ya-lambda-{Environment}`

La tabla de DynamoDB incluye:
- **Point-in-Time Recovery**: Habilitado para recuperación de datos
- **DynamoDB Streams**: Configurado para capturar cambios
- **CloudWatch Metrics**: Métricas automáticas de rendimiento

## Seguridad

- La función tiene permisos mínimos por defecto
- Se recomienda revisar y ajustar los permisos según necesidades
- Usar variables de entorno para configuración sensible
- Implementar autenticación en API Gateway si es necesario