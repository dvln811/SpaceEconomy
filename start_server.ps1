## Start SpaceEconomy Server (no watchdog restarts)
## Usage: right-click > Run with PowerShell, or from terminal: .\start_server.ps1

Set-Location "C:\TrinityRepos\request_simulator\SpaceEconomy"

# Clean up debug log
Remove-Item debug_output.txt -ErrorAction SilentlyContinue

# Kill any existing python processes
taskkill /F /IM python.exe 2>$null

# Wait for processes to fully exit
Start-Sleep 3

# Start the server with reloader disabled (prevents random restarts)
# WERKZEUG_RUN_MAIN=true tricks Flask into thinking it's already the child process
$env:WERKZEUG_RUN_MAIN = "true"
Start-Process python -ArgumentList "-m","server.main" -WorkingDirectory "C:\TrinityRepos\request_simulator\SpaceEconomy"
