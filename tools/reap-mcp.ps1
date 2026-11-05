<#
  reap-mcp.ps1 - kill stale MCP server processes left behind by OpenCode sessions.

  The ai-memory and websearch MCP servers are python children of opencode-cli.
  They exit on stdin EOF (server.py reads `for line in sys.stdin`), but the client
  keeps the pipe open across sessions, so a new session adds a second pair and the
  older one keeps answering with whatever code it imported at boot.

  Rule: per kind, keep the newest -KeepNewest processes and kill the rest, never
  touching anything younger than -GuardMinutes, so a fresh spawn is never raced
  and the pair serving the current session always survives.

  WARNING: run it only from the scheduled task or when no window needs the tools.
  Killing a pair the live client is still registered to removes the MCP tools from
  that session until the app restarts (seen 2026-11-05).
#>
param(
  [switch]$Apply,
  [int]$GuardMinutes = 10,
  [int]$KeepNewest = 1,
  [string]$LogPath = (Join-Path $PSScriptRoot 'reap-mcp.log')
)

$patterns = @(
  @{ Kind = 'ai-memory'; Pat = 'adapters[\\/]mcp[\\/]server\.py' },
  @{ Kind = 'websearch'; Pat = 'mcp[\\/]websearch[\\/]server\.py' }
)
$cutoff = (Get-Date).AddMinutes(-$GuardMinutes)
$groups = @{}

foreach ($proc in (Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue)) {
  if (-not $proc.CommandLine) { continue }
  foreach ($rule in $patterns) {
    if ($proc.CommandLine -notmatch $rule.Pat) { continue }
    if (-not $groups.ContainsKey($rule.Kind)) { $groups[$rule.Kind] = @() }
    $groups[$rule.Kind] += [pscustomobject]@{
      Pid     = $proc.ProcessId
      Kind    = $rule.Kind
      Started = $proc.CreationDate
    }
    break
  }
}

$victims = @()
foreach ($kind in $groups.Keys) {
  $all = @($groups[$kind] | Sort-Object Started -Descending)
  $keep = $all | Select-Object -First $KeepNewest
  foreach ($p in ($all | Select-Object -Skip $KeepNewest)) {
    $age = if ($p.Started) { [math]::Round(((Get-Date) - $p.Started).TotalMinutes) } else { -1 }
    if ($p.Started -and $p.Started -gt $cutoff) {
      Write-Output ("skip (fresh, {0} min): {1} pid {2}" -f $age, $p.Kind, $p.Pid)
      continue
    }
    $victims += [pscustomobject]@{ Pid = $p.Pid; Kind = $p.Kind; AgeMin = $age }
  }
  foreach ($k in $keep) {
    $age = if ($k.Started) { [math]::Round(((Get-Date) - $k.Started).TotalMinutes) } else { -1 }
    Write-Output ("keep (newest, {0} min): {1} pid {2}" -f $age, $k.Kind, $k.Pid)
  }
}

if (-not $victims) {
  Write-Output 'reap: nothing to kill'
  return
}

foreach ($v in $victims) {
  if ($Apply) {
    Stop-Process -Id $v.Pid -Force -ErrorAction SilentlyContinue
    $line = "{0} killed {1} pid {2} (age {3} min)" -f (Get-Date -Format o), $v.Kind, $v.Pid, $v.AgeMin
  } else {
    $line = "{0} would kill {1} pid {2} (age {3} min)" -f (Get-Date -Format o), $v.Kind, $v.Pid, $v.AgeMin
  }
  Write-Output $line
  if ($Apply) { Add-Content -Path $LogPath -Value $line -Encoding utf8 }
}
