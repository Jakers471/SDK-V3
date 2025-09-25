# Quick test of diagnostic system

Write-Host "🧪 Testing Risk Diagnostic System" -ForegroundColor Cyan
Write-Host ""

# Test the diagnostic logger class
class TestDiagnosticLogger {
    [void]LogEvent([string]$eventType, [string]$enumName, [object]$payload) {
        Write-Host "🎯 EVENT FIRED:" -ForegroundColor Yellow -NoNewline
        Write-Host " $eventType ($enumName)" -ForegroundColor White
        Write-Host "   📦 PAYLOAD: $payload" -ForegroundColor Gray
        Write-Host ""
    }

    [void]LogHook([string]$hookName, [object]$data) {
        Write-Host "🪝 HOOK FIRED:" -ForegroundColor Magenta -NoNewline
        Write-Host " $hookName" -ForegroundColor White
        Write-Host "   📊 DATA: $data" -ForegroundColor Gray
        Write-Host ""
    }

    [void]LogApiCall([string]$methodName, [object]$parameters) {
        Write-Host "🔌 API CALL:" -ForegroundColor Green -NoNewline
        Write-Host " $methodName" -ForegroundColor White
        Write-Host "   ⚙️ PARAMETERS: $parameters" -ForegroundColor Gray
        Write-Host ""
    }
}

$testLogger = [TestDiagnosticLogger]::new()

# Simulate the diagnostic flow
Write-Host "🎭 Simulating diagnostic event flow..." -ForegroundColor Yellow
Write-Host ""

$positionData = @{
    contractId = "CON.F.US.MNQ.Z25"
    size = 5
    type = 1
    averagePrice = 24737.25
}
$testLogger.LogEvent("POSITION_UPDATED", "EventType.POSITION_UPDATED", $positionData)

$breachData = @{
    breach = @{rule_name = "max_contracts"; max_size = 2; current_size = 5}
    contract_id = "CON.F.US.MNQ.Z25"
}
$testLogger.LogHook("on_breach", $breachData)

$apiParams = @{
    contract_id = "CON.F.US.MNQ.Z25"
    account_id = "DEMO123"
}
$testLogger.LogApiCall("close_position_direct", $apiParams)

Write-Host "✅ Diagnostic test completed!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit test"
