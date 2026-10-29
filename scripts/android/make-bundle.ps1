<#
.SYNOPSIS
  Build the single file you carry to the phone: android-bundle.tar.gz.

.DESCRIPTION
  Packs the memory repo (code + corpus), the Termux setup script, the phone
  opencode.jsonc and the keyless websearch MCP server into one archive. The
  phone side is then two commands: transfer, `bash setup.sh`.

  memory/profile.md is left out unless -WithPersonal: it describes you, and a
  phone is a device that gets lost.

.EXAMPLE
  pwsh -File scripts/android/make-bundle.ps1
  pwsh -File scripts/android/make-bundle.ps1 -WithPersonal -Out D:\phone\bundle.tar.gz
#>
[CmdletBinding()]
param(
  [switch]$WithPersonal,
  [string]$Out = "E:\AI\memory\android-bundle.tar.gz"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$stage = Join-Path $env:TEMP "opencode\android-bundle"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path "$stage\config", "$stage\websearch" | Out-Null

Write-Host "staging repo (code + corpus, no .git/tmp/output)"
& robocopy $repo "$stage\repo" /E /XD .git tmp output __pycache__ node_modules .venv /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with $LASTEXITCODE" }

if (-not $WithPersonal) {
  Remove-Item -Force "$stage\repo\memory\profile.md" -ErrorAction SilentlyContinue
}

Copy-Item "$PSScriptRoot\setup-termux.sh" "$stage\setup.sh"
Copy-Item "$PSScriptRoot\opencode.phone.jsonc" "$stage\config\opencode.jsonc"
Copy-Item "E:\AI\mcp\websearch\server.py" "$stage\websearch\server.py"

# LF endings matter on the phone: a CRLF shebang fails with "bad interpreter".
$script = Get-Content "$stage\setup.sh" -Raw
[IO.File]::WriteAllText("$stage\setup.sh", ($script -replace "`r`n", "`n"), (New-Object System.Text.UTF8Encoding($false)))

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
if (Test-Path $Out) { Remove-Item -Force $Out }
& tar -czf $Out -C $stage .

$size = (Get-Item $Out).Length / 1MB
$files = (& tar -tzf $Out | Measure-Object).Count
$corpus = (& tar -tzf $Out | Where-Object { $_ -match '^\./repo/knowledge/.+\.md$' }).Count

Write-Host ("bundle: {0}  ({1:N2} MB, {2} entries, {3} notes)" -f $Out, $size, $files, $corpus)
Write-Host ("personal notes: {0}" -f ($(if ($WithPersonal) { "included" } else { "excluded" })))
Remove-Item -Recurse -Force $stage
