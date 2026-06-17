param([int]$Port = 8000)

$ErrorActionPreference = 'SilentlyContinue'
$proj = 'H:\Projects\space_hauler'
$python = 'C:\miniconda\python.exe'

# Kill any existing space_hauler server
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    try { $_.CommandLine -like '*server.main*' } catch { $false }
} | Stop-Process -Force
Start-Sleep -Milliseconds 500

$result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
    -Arguments @{
        CommandLine = "`"$python`" -m server.main"
        CurrentDirectory = $proj
    }

if ($result.ReturnValue -ne 0) {
    Write-Host "Spawn failed, return code $($result.ReturnValue)"
    exit 1
}

# Poll health endpoint
$deadline = (Get-Date).AddSeconds(10)
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Port/health" -TimeoutSec 1 -UseBasicParsing
        if ($r.StatusCode -eq 200) {
            Write-Host "Server ready (PID $($result.ProcessId)) at http://127.0.0.1:$Port"
            exit 0
        }
    } catch {}
    Start-Sleep -Milliseconds 400
}
Write-Host "Server did not respond within 10s (PID $($result.ProcessId))."
exit 1
