[CmdletBinding()]
param(
    [ValidateSet('gpu', 'cpu')][string]$Device = 'gpu',
    [string]$Distro = 'Ubuntu',
    [string[]]$CvatComposeFiles = @(),
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
function Invoke-CheckedDocker {
    param([string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($Arguments -join ' ')" }
}
function Convert-ToLinuxPath([string]$Path) {
    if ($Path.StartsWith('/')) { return $Path }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $converted = & wsl -d $Distro -- wslpath -a -- $resolved.Replace('\', '/')
    if ($LASTEXITCODE -ne 0) { throw "Cannot convert path: $Path" }
    return $converted.Trim()
}
$containerJson = & docker inspect cvat_server
if ($LASTEXITCODE -ne 0) { throw 'The existing cvat_server container must be running.' }
$container = @($containerJson | ConvertFrom-Json)[0]
$labels = $container.Config.Labels
$project = $labels.'com.docker.compose.project'
$projectDirectory = $labels.'com.docker.compose.project.working_dir'
if (-not $project -or -not $projectDirectory) { throw 'Cannot identify the existing CVAT Compose project.' }
if (-not $CvatComposeFiles.Count) {
    $CvatComposeFiles = $labels.'com.docker.compose.project.config_files' -split ','
}
# The integration override may already be listed after a previous deployment.
$linuxRoot = Convert-ToLinuxPath $root
$override = "$linuxRoot/compose.override.yml"
$linuxComposeFiles = @($CvatComposeFiles | ForEach-Object { Convert-ToLinuxPath $_ } | Where-Object { $_ -ne $override })
$networks = @($container.NetworkSettings.Networks.PSObject.Properties.Name)
$network = if ($networks -contains "${project}_cvat") { "${project}_cvat" } else { $networks[0] }
& "$PSScriptRoot/download-model.ps1"
if (-not $SkipBuild) {
    $index = if ($Device -eq 'gpu') { 'https://download.pytorch.org/whl/cu118' } else { 'https://download.pytorch.org/whl/cpu' }
    Invoke-CheckedDocker -Arguments @('build', '--progress', 'plain', '--build-arg', "TORCH_INDEX_URL=$index", '-t', "cvat.mobilesam.base:$Device", $root)
}
$preflight = @('run', '--rm', '-e', "MOBILESAM_DEVICE=$(if ($Device -eq 'gpu') { 'cuda' } else { 'cpu' })")
if ($Device -eq 'gpu') { $preflight += @('--gpus', 'all') }
$preflight += @("cvat.mobilesam.base:$Device", 'python', '-c', 'import json; from model_handler import ModelHandler; print(json.dumps(ModelHandler().info))')
Invoke-CheckedDocker -Arguments $preflight
$cache = Join-Path $root '.cache'
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$nuctl = Join-Path $cache 'nuctl'
if (-not (Test-Path -LiteralPath $nuctl)) {
    Invoke-WebRequest -Uri 'https://github.com/nuclio/nuclio/releases/download/1.16.3/nuctl-1.16.3-linux-amd64' -OutFile "$nuctl.partial"
    Move-Item -LiteralPath "$nuctl.partial" -Destination $nuctl
}
$nuctlSha256 = '519df095e6e6f400093814bd45695242cebb3fa62e3dc96b3ec3929f4313ed9f'
if ((Get-FileHash -LiteralPath $nuctl -Algorithm SHA256).Hash.ToLowerInvariant() -ne $nuctlSha256) {
    throw 'Nuclio CLI checksum mismatch. Move the cached binary aside and download it again.'
}
$linuxProjectDirectory = Convert-ToLinuxPath $projectDirectory
& wsl -d $Distro -- bash "$linuxRoot/scripts/deploy.sh" $linuxRoot $Device $project $linuxProjectDirectory $network @linuxComposeFiles
if ($LASTEXITCODE -ne 0) { throw 'Nuclio deployment failed; see the output above.' }
Write-Host 'MobileSAM deployed. Refresh CVAT and select MobileSAM Local (points) under AI Tools / Interactors.'
