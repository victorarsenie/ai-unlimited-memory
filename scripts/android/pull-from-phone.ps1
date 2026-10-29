<#
.SYNOPSIS
  Pull the phone's memory corpus and report what differs from this machine's.

.DESCRIPTION
  Fetches a tar of knowledge/ + memory/ from the phone, unpacks it into
  E:\AI\memory\phone-inbox\<timestamp>\, then compares every note with the live
  corpus. It never writes to knowledge/ - it prints what needs a decision:

    NEW       the note does not exist here
    NEWER     the phone's updated: is later than the local one
    DIFF      same updated: but the body differs
    pc-newer  the phone copy is stale (no action, listed only with -Verbose)

  The inbox folder is kept on purpose: the next pull is diffed against the live
  corpus only, but keeping the previous export shows a phone edit that arrived
  twice or was half-merged.

  Phone side, one command each:
    cd ~/memory && tar -czf ~/kb-export.tar.gz knowledge memory
    python -m http.server 8000

  Then run this with -Url http://<phone-ip>:8000/kb-export.tar.gz.

.EXAMPLE
  pwsh -File scripts/android/pull-from-phone.ps1
  pwsh -File scripts/android/pull-from-phone.ps1 -Url http://192.168.100.10:8000/kb-export.tar.gz
#>
[CmdletBinding()]
param(
  [string]$Url = "http://192.168.100.10:8000/kb-export.tar.gz",
  [string]$Live = "E:\AI\memory\ai-unlimited-memory",
  [string]$Inbox = "E:\AI\memory\phone-inbox"
)

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$work = Join-Path $env:TEMP "opencode\phone-pull"
$drop = Join-Path $Inbox $stamp
$tar = Join-Path $work "kb-export.tar.gz"

if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force -Path $work, $drop | Out-Null

Write-Host "fetching $Url"
Invoke-WebRequest -Uri $Url -OutFile $tar -UseBasicParsing -TimeoutSec 60
if (-not (Test-Path $tar)) { throw "download failed" }
$size = (Get-Item $tar).Length
if ($size -lt 1000) { throw "downloaded only $size bytes - wrong URL?" }

Write-Host ("unpacking {0:N0} bytes -> {1}" -f $size, $drop)
& tar -xzf $tar -C $drop
if ($LASTEXITCODE -ne 0) { throw "tar failed with $LASTEXITCODE" }

function FrontMatter([string]$path) {
  $text = Get-Content $path -Raw -Encoding UTF8
  $updated = ""
  if ($text -match '(?m)^updated:\s*(\d{4}-\d{2}-\d{2})') { $updated = $Matches[1] }
  # Body only: the diff should ignore front matter churn.
  $body = ($text -replace '(?s)^---.*?\n---\n', '').Trim()
  [pscustomobject]@{ Updated = $updated; Body = $body }
}

$results = @()
$notes = Get-ChildItem -Path $drop -Recurse -File -Filter *.md |
  Where-Object { $_.FullName -match '\\(knowledge|memory)\\' }

foreach ($note in $notes) {
  $rel = $note.FullName.Substring($drop.Length).TrimStart('\')
  $livePath = Join-Path $Live $rel
  if (-not (Test-Path $livePath)) {
    $results += [pscustomobject]@{ State = "NEW"; Note = $rel; Detail = "absent locally" }
    continue
  }
  $a = FrontMatter $note.FullName
  $b = FrontMatter $livePath
  if ($a.Body -eq $b.Body -and $a.Updated -eq $b.Updated) { continue }
  if ($a.Updated -gt $b.Updated) {
    $results += [pscustomobject]@{ State = "NEWER"; Note = $rel; Detail = "$($b.Updated) -> $($a.Updated)" }
  }
  elseif ($a.Updated -eq $b.Updated) {
    $results += [pscustomobject]@{ State = "DIFF"; Note = $rel; Detail = "same updated:, body differs" }
  }
  else {
    Write-Verbose "pc-newer: $rel ($($a.Updated) < $($b.Updated))"
  }
}

Write-Host ""
if ($results.Count -eq 0) {
  Write-Host "no differences: the phone corpus matches this one"
} else {
  Write-Host ("{0} note(s) need a decision:" -f $results.Count)
  $results | Sort-Object State, Note | Format-Table -AutoSize | Out-String -Width 160 | Write-Host
  Write-Host "merge line-level into knowledge/, never copy a note over a live one:"
  Write-Host "  python kb.py dupes; python kb.py index; python kb.py lint"
}
Write-Host ""
Write-Host "export kept at $drop"
Remove-Item -Recurse -Force $work
exit 0
