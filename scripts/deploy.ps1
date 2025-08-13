# Script de despliegue para Invierte Ya
# Copia las dependencias, despliega y limpia

$ErrorActionPreference = "Stop"

Write-Host "Iniciando despliegue de Invierte Ya..." -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "template.yaml")) {
    Write-Host "Error: No se encontro template.yaml. Ejecuta desde el directorio raiz del proyecto." -ForegroundColor Red
    exit 1
}

# Función para limpiar dependencias copiadas
function Cleanup {
    Write-Host "Limpiando dependencias temporales..." -ForegroundColor Yellow
    
    # Limpiar directorios temporales
    Get-ChildItem -Directory | Where-Object { 
        $_.Name -notin @("src", "tests", "docs", "scripts", "dependencies", ".git", ".aws-sam") 
    } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Limpiar archivos .py temporales (excepto los del proyecto)
    Get-ChildItem -File "*.py" | Where-Object { 
        $_.Name -notin @("six.py", "typing_extensions.py") 
    } | Remove-Item -Force -ErrorAction SilentlyContinue
    
    # Limpiar directorios dist-info
    Get-ChildItem -Directory "*-*.dist-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Configurar trap para limpiar en caso de error
trap { Cleanup }

Write-Host "Construyendo y desplegando..." -ForegroundColor Cyan

# Desplegar usando SAM
if ($args[0] -eq "guided") {
    sam deploy --guided
} else {
    $environment = if ($args[0]) { $args[0] } else { "default" }
    sam deploy --config-env $environment
}

Write-Host "Despliegue completado exitosamente!" -ForegroundColor Green

# Limpiar al final
Cleanup