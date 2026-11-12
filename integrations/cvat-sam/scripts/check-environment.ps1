[CmdletBinding()]
param([string]$Distro = 'Ubuntu')
$ErrorActionPreference = 'Stop'
docker version --format 'Docker client {{.Client.Version}}, server {{.Server.Version}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is unavailable.' }
docker inspect cvat_server --format 'CVAT image: {{.Config.Image}}; Compose project: {{index .Config.Labels "com.docker.compose.project"}}'
if ($LASTEXITCODE -ne 0) { throw 'The cvat_server container was not found.' }
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
wsl -d $Distro -- bash -lc 'command -v docker; uname -m'
docker run --rm --gpus all --entrypoint nvidia-smi cvat/server:v2.74.1
if ($LASTEXITCODE -ne 0) { Write-Warning 'GPU is unavailable inside Docker; deploy with -Device cpu.' }
docker stats --no-stream --format '{{.Name}} | {{.MemUsage}}'
