# Push the local feeds.txt to the RSS_FEEDS GitHub secret, so the scheduled
# Actions run uses the same list. Needs the GitHub CLI (gh), signed in.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path feeds.txt)) {
    Write-Error "feeds.txt not found. Copy feeds.example.txt to feeds.txt and fill it in."
}

# Send only the URLs: drop comments and blank lines.
$feeds = Get-Content feeds.txt |
    ForEach-Object { ($_ -split ' #')[0].Trim() } |
    Where-Object { $_ -and -not $_.StartsWith('#') }

if (-not $feeds) { Write-Error "feeds.txt has no feed URLs." }

($feeds -join "`n") | gh secret set RSS_FEEDS
Write-Host "RSS_FEEDS updated with $(@($feeds).Count) feeds."
