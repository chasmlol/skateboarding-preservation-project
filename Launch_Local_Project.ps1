Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Python = Join-Path $Root "python\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$ExpectedSourceHash = "066FD6F38C1CD8F7656BA99016A18CEEB7B9E4EEA81AEB2CDE4C6D5431123703"
$ExpectedClientHash = "3735610743A2AAA8557D68286788F0CB4425684D3C959374C1F3B2A579CB884C"

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

function Write-Diag {
    param(
        [string]$Message
    )

    $Now = Get-Date -Format "HH:mm:ss"
    Write-Host "[$Now] $Message"
}

function Test-IsAdministrator {
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($Identity)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-FileSha256 {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-ProcessNameForId {
    param(
        [int]$ProcessId
    )

    try {
        return (Get-Process -Id $ProcessId -ErrorAction Stop).ProcessName
    }
    catch {
        return "unknown"
    }
}

function Write-PortDiagnostics {
    param(
        [string]$Label,
        [int[]]$Ports
    )

    Write-Diag "$Label port listeners:"
    foreach ($Port in $Ports) {
        try {
            $Connections = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
        }
        catch {
            $Connections = @()
        }

        if ($Connections.Count -eq 0) {
            Write-Host "  port ${Port}: no listener"
            continue
        }

        $Owners = $Connections | ForEach-Object {
            "$($_.OwningProcess)/$(Get-ProcessNameForId $_.OwningProcess)"
        } | Sort-Object -Unique
        Write-Host "  port ${Port}: $($Owners -join ', ')"
    }
}

function Write-ExecutableDiagnostics {
    $ClientExe = Join-Path $Root "preservation_client.exe"
    $ClientHash = Get-FileSha256 $ClientExe

    if ($ClientHash) {
        $ClientState = if ($ClientHash -eq $ExpectedClientHash) { "valid" } else { "unexpected" }
        Write-Diag "Existing preservation client: $ClientState ($($ClientHash.Substring(0, 12))...)"
    }
    else {
        Write-Diag "Existing preservation client: missing"
    }

    $Candidates = @(Get-ChildItem -LiteralPath $Root -Filter "*.exe" -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne "preservation_client.exe" })
    Write-Diag "Local executable candidates found: $($Candidates.Count)"

    $Supported = @()
    foreach ($Candidate in $Candidates) {
        $Hash = Get-FileSha256 $Candidate.FullName
        if ($Hash -eq $ExpectedSourceHash) {
            $Supported += $Candidate.Name
        }
    }

    if ($Supported.Count -gt 0) {
        Write-Diag "Supported source executable detected: yes ($($Supported -join ', '))"
    }
    else {
        Write-Diag "Supported source executable detected: no"
    }
}

function Get-ClientCommandLine {
    param(
        [int]$ProcessId
    )

    try {
        $ProcessInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
        return $ProcessInfo.CommandLine
    }
    catch {
        return ""
    }
}

function Get-RunLogText {
    param(
        [string]$Stamp
    )

    $Text = ""
    $Files = @(Get-ChildItem -LiteralPath $LogDir -Filter "*_$Stamp.jsonl" -File -ErrorAction SilentlyContinue)
    foreach ($File in $Files) {
        try {
            $Text += "`n" + (Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop)
        }
        catch {
        }
    }
    return $Text
}

function Count-Text {
    param(
        [string]$Text,
        [string]$Pattern
    )

    return ([regex]::Matches($Text, [regex]::Escape($Pattern))).Count
}

function Get-FirstRegexGroup {
    param(
        [string]$Text,
        [string]$Pattern
    )

    $Match = [regex]::Match($Text, $Pattern)
    if ($Match.Success) {
        return $Match.Groups[1].Value
    }
    return "?"
}

function Get-RunSummary {
    param(
        [string]$Stamp
    )

    $Text = Get-RunLogText $Stamp

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return "no log lines yet"
    }

    $Discovery = Count-Text $Text '"event": "server_discovery_response"'
    $Login = Count-Text $Text '"event": "login_response"'
    $GameData = Count-Text $Text '"event": "game_data_response"'
    $GameDataChunks = Count-Text $Text '"event": "game_data_chunks_response"'
    $Profile = Count-Text $Text '"event": "profile_response"'
    $ProgressionGet = Count-Text $Text '"event": "progression_get"'
    $ProgressionSend = Count-Text $Text '"event": "progression_send"'
    $Inventory = Count-Text $Text '"event": "inventory_response"'
    $Ownables = Count-Text $Text '"event": "ownables_response"'
    $LevelRewards = Count-Text $Text '"event": "level_rewards_response"'
    $SaveLoad = Count-Text $Text '"event": "save_load"'
    $ProfileSave = Count-Text $Text '"key": "Profile"'
    $CustomizationSave = Count-Text $Text '"key": "Customization"'
    $Checkpoints = Count-Text $Text '"event": "bootstrap_checkpoint"'

    $Level = Get-FirstRegexGroup $Text '"event": "level_rewards_response".*?"level": ([0-9.]+)'
    $InventoryCount = Get-FirstRegexGroup $Text '"event": "inventory_response".*?"count": ([0-9]+)'
    $OwnableCount = Get-FirstRegexGroup $Text '"event": "ownables_response".*?"count": ([0-9]+)'
    $ActiveUnlocks = Get-FirstRegexGroup $Text '"customization_active_unlock_count": ([0-9]+)'
    $ProgressionReturned = Get-FirstRegexGroup $Text '"event": "progression_get".*?"returned": ([0-9]+)'
    $ProfileLevel = Get-FirstRegexGroup $Text '"event": "profile_response".*?"level": ([0-9.]+)'

    $Missing = @()
    if ($Discovery -eq 0) { $Missing += "Discovery" }
    if ($Login -eq 0) { $Missing += "Login" }
    if ($GameData -eq 0) { $Missing += "GameData" }
    if ($Profile -eq 0) { $Missing += "Profile" }
    if ($Inventory -eq 0) { $Missing += "Inventory" }
    if ($Ownables -eq 0) { $Missing += "Ownables" }
    if ($LevelRewards -eq 0) { $Missing += "LevelRewards" }
    if ($SaveLoad -eq 0) { $Missing += "SaveLoad" }
    $MissingText = if ($Missing.Count) { $Missing -join "," } else { "none" }

    return "Discovery=$Discovery Login=$Login GameData=$GameData Chunks=$GameDataChunks Profile=$Profile(profileLevel=$ProfileLevel) ProgressionGet=$ProgressionGet(firstReturned=$ProgressionReturned) ProgressionSend=$ProgressionSend Inventory=$Inventory(count=$InventoryCount) Ownables=$Ownables(count=$OwnableCount) LevelRewards=$LevelRewards(level=$Level) SaveLoad=$SaveLoad ProfileSave=$ProfileSave CustomizationSave=$CustomizationSave(active=$ActiveUnlocks) Checkpoints=$Checkpoints Missing=$MissingText"
}

function Write-CurrentRunLogList {
    param(
        [string]$Stamp
    )

    Write-Diag "Current run log files:"
    $Files = @(Get-ChildItem -LiteralPath $LogDir -Filter "*_$Stamp.*" -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($Files.Count -eq 0) {
        Write-Host "  none"
        return
    }

    foreach ($File in $Files) {
        Write-Host "  $($File.Name) ($($File.Length) bytes)"
    }
}

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
    Write-Diag "Diagnostics stamp: $Stamp"
    Write-Diag "Project folder: $Root"
    Write-Diag "Running as administrator: $(Test-IsAdministrator)"
    Write-Diag "PowerShell: $($PSVersionTable.PSVersion)"
    Write-Diag "Python path: $Python"
    Write-Diag "PYTHONPATH: $($env:PYTHONPATH)"
    Write-Diag "Cosmetic max count: $($env:SKATE_COSMETIC_MAX_COUNT)"
    Write-ExecutableDiagnostics
    Write-PortDiagnostics "Before backend start" @(80, 443, 42230, 44325, 50051)

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
    Write-Diag "Backend process ids: $((($Processes | ForEach-Object { $_.Id }) -join ', '))"
    Write-PortDiagnostics "After backend start" @(80, 443, 42230, 44325, 50051)

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
    Write-ExecutableDiagnostics

    Write-Host "Local backend started. Launching preservation client..."
    $ClientStartedAt = Get-Date
    $ClientStdout = Join-Path $LogDir "client_$Stamp.stdout.log"
    $ClientStderr = Join-Path $LogDir "client_$Stamp.stderr.log"
    $ClientArgs = @("-DingoOnline.ClientAutoLoginEnabled", "true")
    Write-Diag "Client launch args: $($ClientArgs -join ' ')"
    $Client = Start-Process -FilePath $ClientExe -ArgumentList $ClientArgs -WorkingDirectory $Root -PassThru -RedirectStandardOutput $ClientStdout -RedirectStandardError $ClientStderr
    Write-Diag "Client process id: $($Client.Id)"
    Start-Sleep -Milliseconds 500
    $ClientCommandLine = Get-ClientCommandLine $Client.Id
    if ($ClientCommandLine) {
        Write-Diag "Client command line: $ClientCommandLine"
    }
    else {
        Write-Diag "Client command line: unavailable"
    }
    Write-Diag "Live backend summary will update every 5 seconds."

    $LastSummary = ""
    while (-not $Client.HasExited) {
        Start-Sleep -Seconds 5
        $Summary = Get-RunSummary $Stamp
        if ($Summary -ne $LastSummary) {
            Write-Diag "Backend summary: $Summary"
            $LastSummary = $Summary
        }
    }

    $ClientRuntime = ((Get-Date) - $ClientStartedAt).TotalSeconds
    $FinalSummary = Get-RunSummary $Stamp
    Write-Diag "Final backend summary: $FinalSummary"
    Write-CurrentRunLogList $Stamp

    $BundlePath = Join-Path $LogDir "diagnostics_$Stamp.zip"
    try {
        $BundleFiles = @(Get-ChildItem -LiteralPath $LogDir -Filter "*_$Stamp.*" -File -ErrorAction SilentlyContinue)
        if ($BundleFiles.Count -gt 0) {
            Compress-Archive -LiteralPath ($BundleFiles | ForEach-Object { $_.FullName }) -DestinationPath $BundlePath -Force
            Write-Diag "Diagnostics bundle: $BundlePath"
        }
    }
    catch {
        Write-Diag "Diagnostics bundle could not be created: $($_.Exception.Message)"
    }

    if (($Client.ExitCode -ne 0) -or ($ClientRuntime -lt 10)) {
        Write-Host "Preservation client exited with code $($Client.ExitCode) after $([Math]::Round($ClientRuntime, 1)) seconds."
        Write-Host "If the game window did not open, send the newest files from the logs folder."
    }
    else {
        Write-Diag "Preservation client exited with code $($Client.ExitCode) after $([Math]::Round($ClientRuntime, 1)) seconds."
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
