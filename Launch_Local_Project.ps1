Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Python = Join-Path $Root "python\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$env:PYTHONPATH = Join-Path $Root "vendor"

$env:SKATE_DATA_CHUNKS_MODE = "requested"
$env:SKATE_CUSTOMIZATION_INVENTORY_STATIC_CHUNK = "1"
$env:SKATE_CUSTOMIZATION_INVENTORY_STATIC_CONTAINS_FILTER = "1"
$env:SKATE_CUSTOMIZATION_INVENTORY_STATIC_ALL_COSMETICS = "1"
$env:SKATE_CUSTOMIZATION_STATIC_AS_OWNABLE = "1"
$env:SKATE_MANIFEST_OWNABLE_ASSET_CHUNK_ID = "1db14f7dba1f130d9470982116c025c8b73092dc"
$env:SKATE_MANIFEST_ALL_COSMETICS = "1"
$env:SKATE_MANIFEST_EQUIPPED_COSMETICS = "1"
$env:SKATE_FORCE_SYNTHETIC_CUSTOMIZATION_SAVE = "1"
$env:SKATE_IGNORE_LEARNED_CUSTOMIZATION_SAVE = "1"
$env:SKATE_COSMETIC_MODE = "balanced"
$env:SKATE_COSMETIC_MAX_COUNT = "56"
$env:SKATE_COSMETIC_LIMITS = "DeckGraphic=8,Truck=4,WheelGraphic=4,DeckGripColor=4,DeckGripCutout=4,WheelColor=4,TopShirt=15,TopJacket=8,BottomPants=15,BottomShorts=8,ShoeSneaker=15,HeadwearHat=12,HeadwearHelmet=3,EyewearGlasses=3,Sock=3,OutfitOveralls=3,CustBody=4,CustSkinType=6,CustHairScalp=4,CustHead=3,CustEye=3"
$env:SKATE_INVENTORY_MODE = "all"
$env:SKATE_INVENTORY_UI_CATEGORY_ALIASES = "0"
$env:SKATE_INVENTORY_INCLUDE_OWNABLE_IDS = "0"
$env:SKATE_INVENTORY_INCLUDE_STACK_HASH = "0"
$env:SKATE_INVENTORY_INCLUDE_STORE_PRODUCTS = "0"
$env:SKATE_BODYTYPE_LOCAL_ITEMS = "0"
$env:SKATE_CLOTHING_LOCAL_FIT_ITEMS = "0"
$env:SKATE_CUSTOMIZATION_PRESENTABLES_STATIC_CHUNK = "0"
$env:SKATE_DATA_CHUNKS_APPEND_CUSTOMIZATION_PRESENTABLES = "0"
$env:SKATE_PRESENTABLES_OWNABLE_MANIFEST = "0"
$env:SKATE_DATA_CHUNKS_APPEND_PRESENTABLES_OWNABLES = "0"
$env:SKATE_SPOOF_SKATER_CATEGORY_AS_BOARD = "0"

function Start-Backend {
    param(
        [string]$Name,
        [string[]]$Arguments
    )

    $stdout = Join-Path $LogDir "$Name.stdout.log"
    $stderr = Join-Path $LogDir "$Name.stderr.log"
    return Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
}

function Assert-BackendRunning {
    param(
        [System.Diagnostics.Process[]]$Processes
    )

    foreach ($Process in $Processes) {
        if ($Process.HasExited) {
            throw "A backend process exited early. Check the latest files in logs."
        }
    }
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Processes = @()

try {
    $Processes += Start-Backend "port80" @(
        "mock_dingo_probe.py",
        "--server-only",
        "--host", "127.0.0.1",
        "--port", "80",
        "--address-mode", "http",
        "--names", "verbose",
        "--log", "logs\port80_$Stamp.jsonl"
    )

    $Processes += Start-Backend "rpc" @(
        "mock_dingo_probe.py",
        "--server-only",
        "--host", "127.0.0.1",
        "--port", "50051",
        "--address-mode", "bare",
        "--names", "verbose",
        "--tls-auto",
        "--log", "logs\rpc_$Stamp.jsonl"
    )

    $Processes += Start-Backend "tls" @(
        "tls_probe.py",
        "--ports", "443", "42230", "44325",
        "--host", "0.0.0.0",
        "--tls12",
        "--cert", "local_gos_server_chain.pem",
        "--key", "local_gos_server_key.pem",
        "--cert443", "local_gos_server_192_chain.pem",
        "--key443", "local_gos_server_192_key.pem",
        "--keep-blaze-open",
        "--blaze-mode", "fire2_auto_full_config",
        "--log", "logs\tls_$Stamp.jsonl"
    )

    $PidFile = Join-Path $Root "local_backend_pids.json"
    $Processes | Select-Object Id, ProcessName, StartTime | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding UTF8

    Start-Sleep -Seconds 2
    Assert-BackendRunning $Processes

    $ClientExe = Join-Path $Root "preservation_client.exe"
    $Patcher = Join-Path $Root "Create_Local_Backend_Exe.py"

    if (Test-Path -LiteralPath $Patcher) {
        Write-Host "Preparing preservation client..."
        & $Python $Patcher
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create preservation_client.exe."
        }
    }

    if (-not (Test-Path -LiteralPath $ClientExe)) {
        throw "No supported local executable was found or generated."
    }

    Write-Host "Local backend started. Launching preservation client..."
    $ClientStartedAt = Get-Date
    $Client = Start-Process -FilePath $ClientExe -ArgumentList @("-DingoOnline.ClientAutoLoginEnabled", "true") -WorkingDirectory $Root -PassThru
    $Client.WaitForExit()
    $ClientRuntime = ((Get-Date) - $ClientStartedAt).TotalSeconds

    if (($Client.ExitCode -ne 0) -or ($ClientRuntime -lt 10)) {
        Write-Host "Preservation client exited with code $($Client.ExitCode) after $([Math]::Round($ClientRuntime, 1)) seconds."
        Write-Host "If the game window did not open, send the newest files from the logs folder."
    }
}
finally {
    foreach ($Process in $Processes) {
        try {
            if ($Process -and -not $Process.HasExited) {
                Stop-Process -Id $Process.Id -Force
            }
        }
        catch {
        }
    }
}
