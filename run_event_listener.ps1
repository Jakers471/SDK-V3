# PowerShell script to run event listener and keep terminal open
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ProjectX Event Listener with Risk Rules" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Run the event listener
python event_listener.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Event listener session ended" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Read-Host "Press Enter to exit"
