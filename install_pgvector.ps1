# Script to install pgvector binaries into PostgreSQL 17 on Windows
$ErrorActionPreference = 'Stop'

$sourceDir = "$env:TEMP\vector_pg17"
if (-not (Test-Path "$sourceDir\lib\vector.dll")) {
    $url = "https://github.com/andreiramani/pgvector_pgsql_windows/releases/download/0.8.7/vector.v0.8.7-pg17.zip"
    $zipPath = "$env:TEMP\vector_pg17.zip"
    Write-Host "Downloading pgvector v0.8.7 for PostgreSQL 17..."
    Invoke-WebRequest -Uri $url -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $sourceDir -Force
}

$pgDir = "C:\Program Files\PostgreSQL\17"
Write-Host "Copying vector.dll to $pgDir\lib..."
Copy-Item "$sourceDir\lib\vector.dll" "$pgDir\lib\" -Force

Write-Host "Copying extension files to $pgDir\share\extension..."
Copy-Item "$sourceDir\share\extension\vector*" "$pgDir\share\extension\" -Force

if (Test-Path "$sourceDir\include\server\extension") {
    $extInc = "$pgDir\include\server\extension\vector"
    if (-not (Test-Path $extInc)) {
        New-Item -ItemType Directory -Path $extInc -Force | Out-Null
    }
    Copy-Item "$sourceDir\include\server\extension\vector\*" $extInc -Force
}

Write-Host "pgvector files copied successfully!"
Write-Host "Verifying:"
Test-Path "$pgDir\lib\vector.dll"
Test-Path "$pgDir\share\extension\vector.control"
