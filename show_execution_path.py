#!/usr/bin/env python3
"""
Quick Execution Path Display - Shows where risk rules go
"""

print("🎯 RISK RULE EXECUTION PATH")
print("="*50)
print()
print("Where risk rules 'go' and how hooks execute:")
print()

steps = [
    ("🎯 EVENT FIRES", "POSITION_UPDATED event from broker"),
    ("🛡️ RULE EVALUATES", "MaxContractsRule.check() runs"),
    ("📊 SIZE CHECK", "Compares position size vs limit"),
    ("🚨 BREACH DETECTED", "Size > max_size = VIOLATION"),
    ("🪝 HOOK EXECUTES", "on_breach hook fires"),
    ("🔄 AUTO-FLATTEN", "_auto_flatten() called"),
    ("🔌 API CALL", "close_position_direct() executes"),
    ("✅ RESULT", "Position closed successfully"),
    ("🏁 COMPLETION", "auto_flatten_complete hook fires")
]

for i, (icon, description) in enumerate(steps, 1):
    print(f"{i}. {icon} → {description}")

print()
print("🎯 EXECUTION FLOW:")
print("   Event → Rule → Check → Breach → Hook → API → Result")
print()
print("Your 32 risk rules follow this EXACT same path!")
print()
print("📖 Run 'run_execution_tracer.bat' for detailed tracing")
print("📖 See 'EXECUTION_FLOW_TRACER_README.md' for full docs")
print()
input("Press Enter to exit...")
