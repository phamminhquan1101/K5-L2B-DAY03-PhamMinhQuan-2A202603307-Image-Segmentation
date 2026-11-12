[CmdletBinding()]
param([ValidateSet('gpu', 'cpu')][string]$Device = 'gpu', [switch]$SkipCvat)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$repo = (Resolve-Path (Join-Path $root '../..')).Path
$output = Join-Path $root 'runtime'
New-Item -ItemType Directory -Force -Path $output | Out-Null
docker run --rm "cvat.mobilesam.base:$Device" python -m unittest discover -s /opt/mobilesam/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Mask protocol tests failed.' }
$function = Invoke-RestMethod -Uri 'http://localhost:8070/api/functions/pth-mobilesam-local' -Headers @{
    'x-nuclio-project-name' = 'cvat'
    'x-nuclio-function-namespace' = 'nuclio'
}
$port = $function.status.httpPort
if (-not $port) { throw 'Nuclio did not return an HTTP port for MobileSAM.' }
$imagePath = Join-Path $repo 'data/tiers/easy_semantic/images/7ee6d192-89e2408b.jpg'
$mountedImage = '/test/7ee6d192-89e2408b.jpg'
docker run --rm --mount "type=bind,source=$imagePath,target=$mountedImage,readonly" --mount "type=bind,source=$output,target=/output" "cvat.mobilesam.base:$Device" python /opt/mobilesam/smoke-test.py --image $mountedImage --point 640 600 --negative 640 150 --repeat 5 --url "http://host.docker.internal:$port" --output /output
if ($LASTEXITCODE -ne 0) { throw 'Nuclio HTTP smoke test failed.' }
if (-not $SkipCvat) {
    Get-Content -LiteralPath "$PSScriptRoot/verify-cvat.py" -Raw | docker exec -i cvat_server python manage.py shell
    if ($LASTEXITCODE -ne 0) { throw 'CVAT integration verification failed.' }
    docker cp cvat_server:/tmp/mobilesam-cvat-verification.json "$output/cvat-api-verification.json"
    if ($LASTEXITCODE -ne 0) { throw 'Cannot copy the CVAT verification result.' }
}
Write-Host "Verification results: $output"
