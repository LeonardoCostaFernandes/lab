# Windows port of bin/local_model_bench.py (PowerShell 5.1, no Python needed).
# Loopback only. Receipt holds hashes and timings, never raw text.
param(
  [string]$Endpoint = 'http://127.0.0.1:8080',
  [string]$Model = 'qwen2.5-3b-instruct-q4_k_m',
  [string]$Prompts = "$PSScriptRoot\..\fixtures\synthetic-prompts.txt",
  [string]$Machine = 'NO_DATA(machine_not_declared)',
  [Parameter(Mandatory)] [string]$Out,
  [int]$MaxTokens = 128,
  [int]$Seed = 42
)
$ErrorActionPreference = 'Stop'
if ($Endpoint -notmatch '^http://(127\.0\.0\.1|\[::1\]):[0-9]+$') { throw 'endpoint must be http://127.0.0.1:<port> or http://[::1]:<port>' }
$list = Get-Content $Prompts -Encoding UTF8 | Where-Object { $_.Trim() }
function Sha([string]$s) { $b=[Text.Encoding]::UTF8.GetBytes($s); ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($b)) -replace '-','').ToLower() }
$runs = @()
foreach ($p in $list) {
  $p = $p.Trim()
  $body = @{ model=$Model; messages=@(@{role='user';content=$p}); temperature=0; seed=$Seed; max_tokens=$MaxTokens; stream=$false } | ConvertTo-Json -Depth 5
  $e = [ordered]@{ prompt_sha256=(Sha $p); output_sha256=$null; output_chars=$null; latency_ms=$null; prompt_tokens=$null; completion_tokens=$null; tokens_per_s=$null; error=$null }
  try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod -Uri "$Endpoint/v1/chat/completions" -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120
    $sw.Stop()
    $t = [string]$r.choices[0].message.content
    $ms = [math]::Round($sw.Elapsed.TotalMilliseconds,1)
    $ct = [int]$r.usage.completion_tokens
    $e.output_sha256=(Sha $t); $e.output_chars=$t.Length; $e.latency_ms=$ms
    $e.prompt_tokens=[int]$r.usage.prompt_tokens; $e.completion_tokens=$ct
    if ($ct -gt 0) { $e.tokens_per_s=[math]::Round($ct/($ms/1000),2) }
  } catch { $e.error = $_.Exception.GetType().Name }
  $runs += [pscustomobject]$e
}
$ok = @($runs | Where-Object { -not $_.error }).Count
$rec = [ordered]@{ schema='lab.receipt/1'; status=$(if($ok){'DEVICE_TESTED'}else{'NO_DATA(endpoint_unreachable_or_invalid_response)'});
  date_utc=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); machine=$Machine; endpoint=$Endpoint; model=$Model;
  command='bin/local_model_bench.ps1'; params=[ordered]@{temperature=0;seed=$Seed;max_tokens=$MaxTokens;n_prompts=$list.Count}; runs=$runs }
$rec | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $Out
Write-Output $rec.status
