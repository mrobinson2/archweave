# ArchWeave: render SVG to PNG with headless Edge or Chrome on Windows.
# Usage: .\render-png.ps1 <path\to\diagram.svg> [-Scale 1.3] [-Out <path.png>]
# No install needed; Edge ships with Windows. Nothing leaves the laptop.
param(
  [Parameter(Mandatory = $true)][string]$Svg,
  [double]$Scale = 1.3,
  [string]$Out = ""
)
$ErrorActionPreference = "Stop"

$svgPath = (Resolve-Path $Svg).Path
if (-not $Out) { $Out = [System.IO.Path]::ChangeExtension($svgPath, ".png") }
$outPath = [System.IO.Path]::GetFullPath($Out)

# read width/height from the <svg> root
$head = Get-Content -Path $svgPath -Raw
$w = [regex]::Match($head, '<svg[^>]*\bwidth="(\d+)').Groups[1].Value
$h = [regex]::Match($head, '<svg[^>]*\bheight="(\d+)').Groups[1].Value
if (-not $w -or -not $h) { throw "SVG root needs numeric width and height" }

$candidates = @(
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
if ($env:ARCHWEAVE_BROWSER) { $candidates = @($env:ARCHWEAVE_BROWSER) + $candidates }
$browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { throw "No Edge or Chrome found. Set ARCHWEAVE_BROWSER to the executable path." }

$uri = "file:///" + ($svgPath -replace '\\', '/')
$profile = Join-Path $env:TEMP ("archweave-profile-" + [guid]::NewGuid().ToString("N"))
$args = @(
  "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
  "--user-data-dir=$profile",
  "--window-size=$w,$h",
  "--force-device-scale-factor=$Scale",
  "--screenshot=$outPath",
  $uri
)
& $browser @args 2>$null | Out-Null
Remove-Item -Recurse -Force $profile -ErrorAction SilentlyContinue

if (-not (Test-Path $outPath)) { throw "Render failed; no PNG at $outPath" }
$size = (Get-Item $outPath).Length
Write-Output ("PNG {0} ({1:N0} bytes) from {2} at {3}x{4} scale {5}" -f $outPath, $size, (Split-Path $browser -Leaf), $w, $h, $Scale)
