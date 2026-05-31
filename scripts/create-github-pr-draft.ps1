# Creates a draft Pull Request via GitHub REST API (no gh).
# Token: copy token to clipboard, run script, press Enter.
# If clipboard is empty: masked Read-Host prompt.

[CmdletBinding()]
param(
    [string] $Owner = 'alexklychnikov-ui',
    [string] $Repo  = 'DynamicsAX',
    [string] $Base   = 'main',
    [string] $Head   = 'final-branch',
    [string] $Title  = '',
    [string] $Body   = 'Draft PR (scripts/create-github-pr-draft.ps1).'
)

function Normalize-GitHubToken {
    param([string] $Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    $t = $Raw.Trim()
    # Strip UTF-8 BOM if present
    if ($t.Length -ge 1 -and [int][char]$t[0] -eq 0xFEFF) { $t = $t.Substring(1).Trim() }
    # Remove accidental surrounding quotes
    if (($t.StartsWith('"') -and $t.EndsWith('"')) -or ($t.StartsWith("'") -and $t.EndsWith("'"))) {
        $t = $t.Substring(1, $t.Length - 2).Trim()
    }
    # If multiple lines, prefer line that looks like a PAT
    if ($t -match "`n|`r") {
        foreach ($line in ($t -split "[\r\n]+")) {
            $line = $line.Trim()
            if ($line -match '^(ghp_|github_pat_|gho_|ghu_|ghs_)') { return $line }
        }
        $first = ($t -split "[\r\n]+" | Where-Object { $_.Trim() } | Select-Object -First 1)
        if ($first) { return $first.Trim() }
    }
    return $t
}

function Get-TokenFromClipboard {
    $raw = Get-Clipboard -Raw -ErrorAction SilentlyContinue
    return (Normalize-GitHubToken -Raw $raw)
}

function Get-TokenFromSecurePrompt {
    $sec = Read-Host 'Paste token (hidden input)' -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try {
        return (Normalize-GitHubToken -Raw ([Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)))
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        $sec.Dispose()
    }
}

function Get-ApiHeaders {
    param([string] $Token)
    return @{
        Authorization          = "Bearer $Token"
        Accept                 = 'application/vnd.github+json'
        'X-GitHub-Api-Version' = '2022-11-28'
    }
}

Write-Host 'Copy GitHub token to clipboard (ONLY the token string, no quotes or extra lines).'
Read-Host 'Press Enter when ready' | Out-Null

$token = Get-TokenFromClipboard
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host 'Clipboard empty or unreadable; use secure prompt.'
    $token = Get-TokenFromSecurePrompt
}

$token = Normalize-GitHubToken -Raw $token
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Error 'Token is empty.'
    exit 1
}

# Preflight: validate token (401 here means bad token or wrong scopes before PR call)
$userUri = 'https://api.github.com/user'
try {
    $null = Invoke-RestMethod -Uri $userUri -Method Get -Headers (Get-ApiHeaders -Token $token)
}
catch {
    Write-Host ''
    Write-Host '401 Unauthorized: GitHub rejected the token. Check:'
    Write-Host '  - Classic PAT: scope "repo" (full control of private repositories).'
    Write-Host '  - Fine-grained: Repository access for this repo + Pull requests: Read and write.'
    Write-Host '  - Token not expired; copy without spaces, quotes, or line breaks.'
    Write-Host '  - Regenerate token if unsure.'
    if ($_.ErrorDetails.Message) { Write-Host "  API: $($_.ErrorDetails.Message)" }
    exit 1
}

if (-not $Title) {
    $Title = "$Head -> $Base (draft)"
}

$uri = "https://api.github.com/repos/$Owner/$Repo/pulls"
$headers = Get-ApiHeaders -Token $token
$payload = @{
    title = $Title
    head  = $Head
    base  = $Base
    draft = $true
    body  = $Body
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $payload -ContentType 'application/json; charset=utf-8'
    Write-Host "OK: $($response.html_url)"
}
catch {
    $err = $_.ErrorDetails.Message
    # 422: PR already open for this head branch
    if ($err -and $err -match 'already exists') {
        $headParam = "${Owner}:${Head}"
        $listUri = "https://api.github.com/repos/$Owner/$Repo/pulls?head=$headParam&state=open"
        try {
            $prs = Invoke-RestMethod -Uri $listUri -Method Get -Headers $headers
            if ($prs -and $prs.Count -gt 0) {
                Write-Host "PR already exists (open): $($prs[0].html_url)"
                exit 0
            }
        }
        catch { }
        $listUriAll = "https://api.github.com/repos/$Owner/$Repo/pulls?head=$headParam&state=all"
        try {
            $prsAll = Invoke-RestMethod -Uri $listUriAll -Method Get -Headers $headers
            if ($prsAll -and $prsAll.Count -gt 0) {
                Write-Host "PR already exists: $($prsAll[0].html_url) (state=$($prsAll[0].state))"
                exit 0
            }
        }
        catch { }
        Write-Host 'PR already exists but could not list it. Open:'
        Write-Host "  https://github.com/$Owner/$Repo/pulls?q=head%3A$Head"
        exit 0
    }
    if ($err) { Write-Error $err }
    else { Write-Error $_ }
    exit 1
}
finally {
    $token = $null
    Remove-Variable token -ErrorAction SilentlyContinue
}
