# ArchWeave Agent, local finisher for Microsoft 365 Copilot output.
# Takes the SVG the agent produced (file path, or clipboard if no path), saves it under out\,
# runs the checker when a plan.json sits beside it, renders PNG with headless Edge, opens the PNG.
# Usage:
#   .\finish.ps1                      SVG is on the clipboard (copy the code block in Copilot)
#   .\finish.ps1 .\out\my-diagram.svg
#   .\finish.ps1 -Plan .\out\plan.json .\out\my-diagram.svg
param(
  [string]$Svg = "",
  [string]$Plan = "",
  [double]$Scale = 1.3
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # diagram-skill\
$skill = Join-Path $root ".github\skills\archweave"
$outDir = Join-Path $root "out"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

if (-not $Svg) {
  $clip = Get-Clipboard -Raw
  if (-not $clip -or $clip -notmatch "<svg") { throw "No SVG path given and clipboard holds no <svg ...> markup. Copy the SVG code block from Copilot first." }
  # strip a markdown fence if the user copied the whole block
  $clip = $clip -replace '^\s*```[a-zA-Z]*\s*', '' -replace '\s*```\s*$', ''
  $m = [regex]::Match($clip, '<title>([^<]+)</title>')
  $slug = if ($m.Success) { ($m.Groups[1].Value -replace '[^A-Za-z0-9]+', '-').Trim('-').ToLower() } else { "diagram" }
  if ($slug.Length -gt 60) { $slug = $slug.Substring(0, 60) }
  $stamp = Get-Date -Format "yyyyMMdd-HHmm"
  $Svg = Join-Path $outDir "$slug-$stamp.svg"
  [System.IO.File]::WriteAllText($Svg, $clip, (New-Object System.Text.UTF8Encoding $false))
  Write-Output "Saved clipboard SVG to $Svg"
}
$Svg = (Resolve-Path $Svg).Path

# quick static guards even without a plan
$text = Get-Content -Raw $Svg
# same list as scripts/check-diagram.py; this runs even when no plan.json is present, before Edge opens the file
$guards = @(
  @('<script[\s>]',                               'a <script> element'),
  @('<animate',                                   'an <animate*> element'),
  @('<set[\s/>]',                                 'a <set> (SMIL) element'),
  @('<foreignObject',                             'a <foreignObject> element'),
  @('<!DOCTYPE|<!ENTITY',                         'a DOCTYPE or entity declaration'),
  @('\son[a-z]+\s*=',                             'an event handler attribute (on*=)'),
  @('javascript:',                                'a javascript: URL'),
  @('https?://(?!www\.w3\.org/)',                 'an external http(s) URL'),
  @('file:',                                      'a file: URL'),
  @('@\s*import|@\s*font-face',                   '@import or @font-face'),
  @('<image[^>]*href="(?!data:)',                 'an <image> that is not inline data:'),
  @('(?<![\w:-])(?:xlink:)?href\s*=\s*"(?!#|data:)', 'an href that is not a local #id or data: URL'),
  @('url\(\s*["'']?(?!#)',                        'a url() that is not a local #id')
)
foreach ($g in $guards) {
  if ($text -match $g[0]) { throw "Refusing to render: SVG contains $($g[1])" }
}
if ($text -notmatch 'data-meta="true"') { Write-Warning "Metadata stamp missing (no data-meta group)." }

# full checker when a plan exists
if (-not $Plan) { $cand = Join-Path (Split-Path $Svg) "plan.json"; if (Test-Path $cand) { $Plan = $cand } }
if ($Plan) {
  $pyCmd = $null; $pyArgs = @()
  if (Get-Command python -ErrorAction SilentlyContinue) { $pyCmd = "python" }
  elseif (Get-Command py -ErrorAction SilentlyContinue) { $pyCmd = "py"; $pyArgs = @("-3") }
  if ($pyCmd) {
    & $pyCmd @pyArgs (Join-Path $skill "scripts\check-diagram.py") $Plan $Svg
    if ($LASTEXITCODE -ne 0) { Write-Warning "Checker reported failures. Paste them back to Copilot and ask for a repair." }
  } else { Write-Warning "python not found (tried python, then py -3); skipping plan check." }
}

& (Join-Path $skill "scripts\render-png.ps1") -Svg $Svg -Scale $Scale
$png = [System.IO.Path]::ChangeExtension($Svg, ".png")
if (Test-Path $png) { Start-Process $png }
