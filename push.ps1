# push.ps1 — bump patch version, commit everything, and push to main
param(
    [string]$Message = ""
)

$appYml = "$PSScriptRoot\axe-webhooks\umbrel-app.yml"

# Read current version
$content = Get-Content $appYml -Raw
if ($content -match 'version:\s*"(\d+)\.(\d+)\.(\d+)"') {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
} else {
    Write-Error "Could not find version in umbrel-app.yml"
    exit 1
}

# Bump patch
$newPatch = $patch + 1
$newVersion = "$major.$minor.$newPatch"
$content = $content -replace 'version:\s*"[\d.]+"', "version: `"$newVersion`""
Set-Content $appYml $content -NoNewline

Write-Host "Version bumped: $major.$minor.$patch -> $newVersion" -ForegroundColor Cyan

# Build commit message
if (-not $Message) {
    $Message = "Release v$newVersion"
}

# Commit and push
git add .
git commit -m "$Message (v$newVersion)"
git push origin main
