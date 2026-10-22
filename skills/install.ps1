# Installs the memory skill into each harness that supports skills.
#
# The canonical copy is skills/knowledge-base/SKILL.md in this repository.
# Harnesses: Hermes (D:\Hermes\skills\memory\knowledge-base) and OpenCode
# (~/.config/opencode/skills/knowledge-base). Existing copies are backed up.
param(
  [ValidateSet('all', 'hermes', 'opencode')]
  [string]$Only = 'all',
  [string]$HermesHome = 'D:\Hermes',
  [string]$OpenCodeSkills = (Join-Path $env:USERPROFILE '.config\opencode\skills')
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repo 'skills\knowledge-base\SKILL.md'
if (-not (Test-Path $source)) { throw "skill not found: $source" }

function Install-Skill($target) {
  New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
  if (Test-Path $target) {
    $bak = "$target.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
    Copy-Item $target $bak -Force
    Write-Host "  backed up: $bak"
  }
  Copy-Item $source $target -Force
  Write-Host "  installed: $target"
}

if ($Only -in 'all', 'hermes') {
  Install-Skill (Join-Path $HermesHome 'skills\memory\knowledge-base\SKILL.md')
}

if ($Only -in 'all', 'opencode') {
  Install-Skill (Join-Path $OpenCodeSkills 'knowledge-base\SKILL.md')
}

Write-Host 'done'
