#!/bin/bash

# Script de despliegue para Invierte Ya
# Copia las dependencias, despliega y limpia

set -e

echo "🚀 Iniciando despliegue de Invierte Ya..."

# Verificar que estamos en el directorio correcto
if [ ! -f "template.yaml" ]; then
    echo "❌ Error: No se encontró template.yaml. Ejecuta desde el directorio raíz del proyecto."
    exit 1
fi

# Función para limpiar dependencias copiadas
cleanup() {
    echo "🧹 Limpiando dependencias temporales..."
    find . -maxdepth 1 -type d -name "*" ! -name "." ! -name "src" ! -name "tests" ! -name "docs" ! -name "scripts" ! -name "dependencies" ! -name ".git" ! -name ".aws-sam" -exec rm -rf {} + 2>/dev/null || true
    find . -maxdepth 1 -name "*.py" ! -name "*.py" -exec rm -f {} + 2>/dev/null || true
    find . -maxdepth 1 -type d -name "*-*.dist-info" -exec rm -rf {} + 2>/dev/null || true
}

# Configurar trap para limpiar en caso de error
trap cleanup EXIT

echo "📦 Copiando dependencias..."
# Copiar dependencias al directorio raíz para el empaquetado
cp -r dependencies/* .

echo "🔨 Construyendo y desplegando..."
# Desplegar usando SAM
if [ "$1" = "guided" ]; then
    sam deploy --guided
else
    ENVIRONMENT=${1:-dev}
    sam deploy --config-env $ENVIRONMENT
fi

echo "✅ Despliegue completado exitosamente!"