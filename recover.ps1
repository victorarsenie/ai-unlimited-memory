# Reinstalls the memory layer into every harness after a config loss.
#
# The data (knowledge/, memory/, the SQLite archive) never lives in a harness
# config, so losing ~/.config/opencode or D:\Hermes loses wiring, not memory.
# This script puts the wiring back and verifies it.
#
#   powershell -NoProfile -File recover.ps1 -Check     # report only
#   powershell -NoProfile -File recover.ps1             # reinstall all harnesses
#   powershell -NoProfile -File recover.ps1 -Harness opencode
param(
  [ValidateSet('all', 'opencode', 'hermes')]
  [string]$Harness = 'all',
  [switch]$Check
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$ok = $true

function Section($title) { Write-Host ""; Write-Host "== $title" -ForegroundColor Cyan }
function Pass($msg) { Write-Host "  ok    $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "  MISS  $msg" -ForegroundColor Yellow; $script:ok = $false }

Section "data (must survive without any harness config)"
if ($repo -ne 'E:\AI\memory\ai-unlimited-memory') {
  Write-Host "  note  repo is not at the default path; both adapters fall back to" -ForegroundColor Yellow
  Write-Host "        E:\AI\memory\ai-unlimited-memory unless MEMORY_HOME is set." -ForegroundColor Yellow
  Write-Host "        Set it before starting a harness:  setx MEMORY_HOME `"$repo`"" -ForegroundColor Yellow
}
foreach ($p in @('kb.py', 'knowledge\INDEX.md', 'memory\rules.md', 'memory\profile.md')) {
  if (Test-Path (Join-Path $repo $p)) { Pass $p } else { Fail $p }
}
$notes = @(Get-ChildItem (Join-Path $repo 'knowledge') -Filter *.md -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -ne 'INDEX.md' }).Count
Pass "$notes knowledge note(s)"
$mapSize = (Get-Item (Join-Path $repo 'knowledge\INDEX.md') -ErrorAction SilentlyContinue).Length
if ($mapSize) { Pass "map $mapSize bytes (regenerate: python kb.py index)" }

Section "harness wiring"
$pluginsDir = Join-Path $env:USERPROFILE '.config\opencode\plugins'
$configDir = Split-Path $pluginsDir -Parent
$pluginShim = Join-Path $pluginsDir 'knowledge-index.ts'
$ocAgents = Join-Path $configDir 'AGENTS.md'
$ocSkill = Join-Path $env:USERPROFILE '.config\opencode\skills\knowledge-base\SKILL.md'
$hermesHook = 'D:\Hermes\agent-hooks\knowledge-index.py'
$hermesSkill = 'D:\Hermes\skills\memory\knowledge-base\SKILL.md'
$hermesConfig = 'D:\Hermes\config.yaml'
$ocConfig = Join-Path $configDir 'opencode.jsonc'

$targets = @()
if ($Harness -in 'all', 'opencode') {
  $targets += @{ name = 'opencode plugin shim'; path = $pluginShim; script = 'adapters\opencode\install.ps1' }
  $targets += @{ name = 'opencode AGENTS.md'; path = $ocAgents; script = $null }
  $targets += @{ name = 'opencode skill'; path = $ocSkill; script = $null }
}
if ($Harness -in 'all', 'hermes') {
  $targets += @{ name = 'hermes hook'; path = $hermesHook; script = 'adapters\hermes\install.ps1' }
  $targets += @{ name = 'hermes skill'; path = $hermesSkill; script = $null }
}

foreach ($t in $targets) {
  if (Test-Path $t.path) { Pass "$($t.name): $($t.path)" } else { Fail "$($t.name): $($t.path)" }
}

if (-not $Check) {
  Section "reinstalling"
  $skillsScript = Join-Path $repo 'skills\install.ps1'
  if ($Harness -eq 'all') {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $skillsScript
  } else {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $skillsScript -Only $Harness
  }
  foreach ($t in $targets) {
    if ($t.script) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo $t.script)
    }
  }
  Section "after reinstall"
  foreach ($t in $targets) {
    if (Test-Path $t.path) { Pass "$($t.name)" } else { Fail "$($t.name)" }
  }
}

Section "MCP tools (OpenCode registers these in opencode.jsonc)"
$mcpText = if (Test-Path $ocConfig) { Get-Content $ocConfig -Raw } else { '' }
if ($mcpText -match '"ai-memory"') {
  Pass "ai-memory entry present in $ocConfig"
} else {
  Fail "ai-memory entry missing - paste this into the mcp.servers block of opencode.jsonc:"
  $py = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not $py) { $py = 'C:/Users/victo/AppData/Local/Programs/Python/Python312/python.exe' }
  $py = $py -replace '\\', '/'
  $snippet = @"
    "ai-memory": {
      "type": "local",
      "command": ["$py", "$($repo -replace '\\','/')/adapters/mcp/server.py"],
      "disabled": false
    }
"@
  Write-Host $snippet
}

Section "Hermes hook registration"
if (Test-Path $hermesConfig) {
  $cfg = Get-Content $hermesConfig -Raw
  $want = $hermesHook -replace '\\', '/'
  if ($cfg -match [regex]::Escape($want)) { Pass "pre_llm_call -> $want" }
  else { Fail "pre_llm_call hook missing from $hermesConfig" }
  if ($cfg -match '(?m)^hooks_auto_accept:\s*true') { Pass "hooks_auto_accept true" }
  else { Fail "hooks_auto_accept is not true (non-interactive runs skip the hook)" }
} else {
  Fail "Hermes config not found: $hermesConfig"
}

Section "verification"
Push-Location $repo
try {
  & python kb.py lint
  & python kb.py stats | Select-Object -First 5
  $node = (Get-Command node -ErrorAction SilentlyContinue).Source
  if ($node) {
    $uri = 'file:///' + (($repo + '\adapters\opencode\knowledge-index.js') -replace '\\', '/')
    $js = "const m = await import('$uri'); const t = m.buildContext(process.cwd()); console.log('  ok    plugin builds ' + t.length + ' chars, rules=' + t.includes('Operating rules (every harness)') + ', truncated=' + t.includes('[truncated]'));"
    & node --input-type=module -e $js
  }
  if (Test-Path (Join-Path $repo 'adapters\hermes\knowledge-index.py')) {
    '{"hook_event_name":"pre_llm_call","cwd":"' + $repo.Replace('\', '\\') + '"}' |
      & python (Join-Path $repo 'adapters\hermes\knowledge-index.py') |
      ForEach-Object {
        $ctx = ($_ | ConvertFrom-Json).context
        Write-Host "  ok    hermes hook builds $($ctx.Length) chars, rules=$($ctx.Contains('Operating rules (every harness)'))"
      }
  }
} finally {
  Pop-Location
}

Section "next"
Write-Host "  restart the harness so it reloads the wiring:"
Write-Host "    opencode service restart        (then reopen the session)"
Write-Host "    restart Hermes desktop / its agent"
Write-Host ""
if ($ok) { Write-Host "recover: wiring complete" -ForegroundColor Green }
else { Write-Host "recover: some wiring is still missing (see MISS above)" -ForegroundColor Yellow }
