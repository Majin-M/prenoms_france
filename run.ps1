# =============================================================================
# Pipeline complet : ingestion -> dbt build (modèles + tests) -> export JSON
# Les graphiques sont dessinés par le portfolio, à partir de exports/.
# =============================================================================
# Utilisation (depuis la racine du dépôt, environnement virtuel activé) :
#     .\run.ps1
# S'arrête à la première étape en échec, avec le code de sortie 1.
# =============================================================================

$ErrorActionPreference = "Stop"
$racine = $PSScriptRoot
$debut = Get-Date

function Lancer-Etape([string]$nom, [scriptblock]$commande) {
    Write-Host ""
    Write-Host "=== $nom ===" -ForegroundColor Cyan
    & $commande
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Échec de l'étape « $nom » (code $LASTEXITCODE). Pipeline interrompu." -ForegroundColor Red
        exit 1
    }
}

Set-Location $racine

Lancer-Etape "1/3 Ingestion INSEE -> raw.prenoms" { python ingest.py }

# dbt se lance depuis dbt/ : profiles.yml y indique la base par un chemin relatif (../data)
Push-Location (Join-Path $racine "dbt")
try {
    Lancer-Etape "2/3 dbt build : modèles et tests" { dbt build --profiles-dir . }
} finally {
    Pop-Location
}

Lancer-Etape "3/3 Export JSON -> exports/" { python export.py }

$duree = (Get-Date) - $debut
Write-Host ""
Write-Host ("Pipeline terminé en {0:N0} s." -f $duree.TotalSeconds) -ForegroundColor Green
