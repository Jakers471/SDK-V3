#!/usr/bin/env python3
"""
Demo of Risk Management Diagnostic System

Shows what the diagnostic output looks like without requiring live trading.
"""

import time
from datetime import datetime
from typing import Any, Dict


class DemoDiagnosticLogger:
    """Demo diagnostic logging system."""

    def __init__(self):
        self.event_counter = 0
        self.api_counter = 0

    def log_event(self, event_type: str, enum_name: str, payload: Dict[str, Any]):
        """Log when an event enum fires."""
        self.event_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(f"\n🎯 EVENT FIRED [{timestamp}]: {event_type} ({enum_name})")
        print("   📦 PAYLOAD:")
        self._format_payload(payload, "     ")

    def log_hook(self, hook_name: str, data: Dict[str, Any]):
        """Log when a hook fires."""
        self.event_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(f"\n🪝 HOOK FIRED [{timestamp}]: {hook_name}")
        print("   📊 DATA:")
        self._format_payload(data, "     ")

    def log_api_call(self, method_name: str, parameters: Dict[str, Any]):
        """Log when an API call is made."""
        self.api_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(f"\n🔌 API CALL [{timestamp}]: {method_name}")
        print("   ⚙️ PARAMETERS:")
        self._format_payload(parameters, "     ")

    def log_risk_rule(self, rule_name: str, evaluation: Dict[str, Any]):
        """Log risk rule evaluation."""
        self.event_counter += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(f"\n🛡️ RULE EVAL [{timestamp}]: {rule_name}")
        print("   📋 EVALUATION:")
        self._format_payload(evaluation, "     ")

    def _format_payload(self, payload: Any, indent: str = ""):
        """Format payload data for display."""
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, dict):
                    print(f"{indent}{key}:")
                    for k, v in value.items():
                        print(f"{indent}  {k}: {v}")
                else:
                    print(f"{indent}{key}: {value}")
        else:
            print(f"{indent}{payload}")

    def generate_report(self):
        """Generate diagnostic report."""
        print(f"\n📊 Demo Complete - Captured {self.event_counter} events, {self.api_counter} API calls")


def simulate_risk_scenario():
    """Simulate a complete risk management scenario."""
    print("🩺 RISK MANAGEMENT DIAGNOSTIC DEMO")
    print("="*60)
    print("This shows the complete event-to-API trace you'll see")
    print("when your 32 risk rules are running!")
    print("="*60)

    diagnostic = DemoDiagnosticLogger()

    print("\n🎭 Simulating trading activity that triggers risk rules...")

    # 1. Position Update Event Fires
    position_data = {
        'contract_id': 'CON.F.US.MNQ.Z25',
        'size': 5,  # This exceeds our max of 2
        'type': 1,  # LONG position
        'average_price': 24737.25,
        'account_id': 'DEMO123'
    }
    diagnostic.log_event("POSITION_UPDATED", "EventType.POSITION_UPDATED", position_data)

    # 2. Risk Rule Evaluates the Position
    rule_evaluation = {
        'rule': 'max_contracts',
        'current_size': 5,
        'max_allowed': 2,
        'breach_detected': True,
        'severity': 'high',
        'auto_flatten': True,
        'contract_id': 'CON.F.US.MNQ.Z25'
    }
    diagnostic.log_risk_rule("MaxContractsRule", rule_evaluation)

    # 3. Breach Hook Fires
    breach_data = {
        'breach': {
            'rule_name': 'max_contracts',
            'max_size': 2,
            'current_size': 5,
            'severity': 'high',
            'auto_flatten': True
        },
        'contract_id': 'CON.F.US.MNQ.Z25',
        'account_id': 'DEMO123',
        'timestamp': datetime.now().isoformat(),
        'trigger_reason': 'position_size_exceeded_limit'
    }
    diagnostic.log_hook("on_breach", breach_data)

    # 4. API Call Made to Close Position
    api_params = {
        'contract_id': 'CON.F.US.MNQ.Z25',
        'account_id': 'DEMO123',
        'reason': 'risk_breach_auto_flatten',
        'market_order': True
    }
    diagnostic.log_api_call("close_position_direct", api_params)

    # 5. Position Closure Hook Fires
    closure_data = {
        'contract_id': 'CON.F.US.MNQ.Z25',
        'success': True,
        'final_size': 0,
        'pnl_realized': -25.50,
        'closure_reason': 'auto_flatten_risk_breach'
    }
    diagnostic.log_hook("on_position_closed", closure_data)

    # 6. Generate Report
    diagnostic.generate_report()

    print("\n" + "="*60)
    print("🎉 DIAGNOSTIC DEMO COMPLETE!")
    print("="*60)
    print("This is exactly what you'll see when testing your risk rules!")
    print("\nKey Benefits:")
    print("• 🎯 See which events actually fire")
    print("• 📦 Verify payloads contain correct data")
    print("• 🪝 Confirm hooks trigger as expected")
    print("• 🔌 Validate API calls are made correctly")
    print("• 🛡️ Debug 32+ risk rules easily")


if __name__ == "__main__":
    try:
        simulate_risk_scenario()
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        input("\n✅ Demo complete. Press Enter to exit...")
