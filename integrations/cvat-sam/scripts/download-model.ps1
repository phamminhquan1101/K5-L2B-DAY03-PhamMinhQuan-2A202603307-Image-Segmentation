[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $root 'weights/mobile_sam.pt'
$expected = '6dbb90523a35330fedd7f1d3dfc66f995213d81b29a5ca8108dbcdd4e37d6c2f'
$url = 'https://raw.githubusercontent.com/ChaoningZhang/MobileSAM/f706ad9c4eb7f219c00d9050e46328518ffb65d2/weights/mobile_sam.pt'
New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
if (Test-Path -LiteralPath $destination) {
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $expected) {
        Write-Host 'MobileSAM checkpoint already verified.'
        return
    }
    throw "Checkpoint checksum mismatch: $destination. Move this file aside before downloading again."
}
$partial = "$destination.partial"
Invoke-WebRequest -Uri $url -OutFile $partial
if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw "Downloaded checkpoint failed SHA256 verification: $partial"
}
Move-Item -LiteralPath $partial -Destination $destination
Write-Host "Verified MobileSAM checkpoint: $destination"
