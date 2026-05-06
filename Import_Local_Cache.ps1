param(
    [string]$Source
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrimaryDestination = Join-Path $Root "cache\http\0\3768241699"
$ReferenceDestination = Join-Path $Root "reference_cache\http\0\3768215040"
$RequiredFiles = @(
    "index.0",
    "0000000000000002.cache",
    "000000000000000a.cache",
    "0000000000000013.cache",
    "000000000000004d.cache"
)

function Test-CacheRoot {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    foreach ($Required in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $Path $Required))) {
            return $false
        }
    }

    return $true
}

function Resolve-CacheSource {
    param(
        [string]$RequestedSource
    )

    if ($RequestedSource) {
        $Resolved = (Resolve-Path -LiteralPath $RequestedSource -ErrorAction Stop).Path
        if (-not (Test-CacheRoot $Resolved)) {
            throw "Cache source is missing required files: $Resolved"
        }
        return $Resolved
    }

    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Skate\data\cache\http\0\3768241699"),
        (Join-Path $env:LOCALAPPDATA "Skate\data\cache\http\0\3768215040"),
        (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "SkateCPT\data\cache\http\0\3768215040")
    )

    foreach ($Candidate in $Candidates) {
        if (Test-CacheRoot $Candidate) {
            return $Candidate
        }
    }

    throw "No complete local Skate cache was found. Pass -Source <path-to-cache-bucket>."
}

$CacheSource = Resolve-CacheSource $Source
New-Item -ItemType Directory -Force -Path $PrimaryDestination, $ReferenceDestination | Out-Null
Copy-Item -Path (Join-Path $CacheSource "*") -Destination $PrimaryDestination -Recurse -Force
Copy-Item -Path (Join-Path $CacheSource "*") -Destination $ReferenceDestination -Recurse -Force

$FileCount = @(Get-ChildItem -LiteralPath $PrimaryDestination -File -ErrorAction SilentlyContinue).Count
Write-Host "Imported local static cache from:"
Write-Host "  $CacheSource"
Write-Host "Wrote ignored local cache folders:"
Write-Host "  $PrimaryDestination ($FileCount files)"
Write-Host "  $ReferenceDestination"
