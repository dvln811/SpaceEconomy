Start-Process -FilePath "python" -ArgumentList "run_local.py" -WorkingDirectory $PSScriptRoot -WindowStyle Normal
Write-Host "Local server starting at http://127.0.0.1:8000 (240x speed)"
Write-Host "Open your browser to connect."
