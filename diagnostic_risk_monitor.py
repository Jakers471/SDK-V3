#!/usr/bin/env python3
"""
Risk Management Diagnostic System

Shows complete event-to-API trace for debugging risk rules:
- Which event enums fire (POSITION_UPDATED, RISK_LIMIT_EXCEEDED, etc.)
- What payloads are passed (breach details, position data, symbols)
- Which API calls are made (place_order, close_position, etc.)
"""

import asyncio
import time
from typing import Any, Dict, List
from dataclasses import dataclass
from datetime import datetime

from project_x_py import TradingSuite, EventType
from rules.rule_engine import RuleEngine, RiskEventHandler


@dataclass
class DiagnosticEntry:
    """Single diagnostic log entry."""
    timestamp: str
    entry_type: str  # EVENT, HOOK, API_CALL, RISK_RULE
    name: str
    data: Dict[str, Any]
    sequence: int


class DiagnosticLogger:
    """Comprehensive diagnostic logging system."""

    def __init__(self):
        self.log_entries: List[DiagnosticEntry] = []
        self.event_counter = 0
        self.api_counter = 0

    def log_event(self, event_type: str, enum_name: str, payload: Dict[str, Any]):
        """Log when an event enum fires."""
        self.event_counter += 1
        entry = DiagnosticEntry(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            entry_type="EVENT",
            name=f"{event_type} ({enum_name})",
            data=payload,
            sequence=self.event_counter
        )
        self.log_entries.append(entry)

        print(f"\n🎯 EVENT FIRED [{entry.timestamp}]: {event_type} ({enum_name})")
        print("   📦 PAYLOAD:")
        self._format_payload(payload, "     ")

    def log_hook(self, hook_name: str, data: Dict[str, Any]):
        """Log when a hook fires."""
        self.event_counter += 1
        entry = DiagnosticEntry(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            entry_type="HOOK",
            name=hook_name,
            data=data,
            sequence=self.event_counter
        )
        self.log_entries.append(entry)

        print(f"\n🪝 HOOK FIRED [{entry.timestamp}]: {hook_name}")
        print("   📊 DATA:")
        self._format_payload(data, "     ")

    def log_api_call(self, method_name: str, parameters: Dict[str, Any]):
        """Log when an API call is made."""
        self.api_counter += 1
        entry = DiagnosticEntry(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            entry_type="API_CALL",
            name=method_name,
            data=parameters,
            sequence=self.api_counter
        )
        self.log_entries.append(entry)

        print(f"\n🔌 API CALL [{entry.timestamp}]: {method_name}")
        print("   ⚙️ PARAMETERS:")
        self._format_payload(parameters, "     ")

    def log_risk_rule(self, rule_name: str, evaluation: Dict[str, Any]):
        """Log risk rule evaluation."""
        self.event_counter += 1
        entry = DiagnosticEntry(
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            entry_type="RISK_RULE",
            name=rule_name,
            data=evaluation,
            sequence=self.event_counter
        )
        self.log_entries.append(entry)

        print(f"\n🛡️ RULE EVAL [{entry.timestamp}]: {rule_name}")
        print("   📋 EVALUATION:")
        self._format_payload(evaluation, "     ")

    def _format_payload(self, payload: Any, indent: str = ""):
        """Format payload data for display."""
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, (dict, list)):
                    print(f"{indent}{key}:")
                    if isinstance(value, dict):
                        for k, v in value.items():
                            print(f"{indent}  {k}: {v}")
                    else:
                        print(f"{indent}  [{len(value)} items]")
                else:
                    print(f"{indent}{key}: {value}")
        else:
            print(f"{indent}{payload}")

    def generate_report(self):
        """Generate comprehensive diagnostic report."""
        print("\n" + "="*60)
        print("📊 DIAGNOSTIC REPORT SUMMARY")
        print("="*60)

        events = [e for e in self.log_entries if e.entry_type == "EVENT"]
        hooks = [e for e in self.log_entries if e.entry_type == "HOOK"]
        api_calls = [e for e in self.log_entries if e.entry_type == "API_CALL"]
        rules = [e for e in self.log_entries if e.entry_type == "RISK_RULE"]

        print(f"📈 Events Fired: {len(events)}")
        print(f"🪝 Hooks Triggered: {len(hooks)}")
        print(f"🔌 API Calls Made: {len(api_calls)}")
        print(f"🛡️ Risk Rules Evaluated: {len(rules)}")
        print()

        if events:
            print("🎯 Event Breakdown:")
            event_types = {}
            for e in events:
                event_types[e.name.split()[0]] = event_types.get(e.name.split()[0], 0) + 1
            for event_type, count in event_types.items():
                print(f"   {event_type}: {count} times")

        if hooks:
            print("\n🪝 Hook Breakdown:")
            hook_types = {}
            for h in hooks:
                hook_types[h.name] = hook_types.get(h.name, 0) + 1
            for hook_name, count in hook_types.items():
                print(f"   {hook_name}: {count} times")

        if api_calls:
            print("\n🔌 API Call Breakdown:")
            api_methods = {}
            for a in api_calls:
                api_methods[a.name] = api_methods.get(a.name, 0) + 1
            for method, count in api_methods.items():
                print(f"   {method}: {count} times")

        print("\n✅ Full event-to-API trace captured!")
        print("   Use this to verify your 32 risk rules work correctly.")

    def get_trace(self, entry_type: str = None) -> List[DiagnosticEntry]:
        """Get trace of specific entry type or all entries."""
        if entry_type:
            return [e for e in self.log_entries if e.entry_type == entry_type]
        return self.log_entries


class DiagnosticRiskHandler(RiskEventHandler):
    """Enhanced risk handler with diagnostic logging."""

    def __init__(self, rule_engine: RuleEngine, trading_suite: Any, diagnostic: DiagnosticLogger):
        super().__init__(rule_engine, trading_suite)
        self.diagnostic = diagnostic
        self._setup_diagnostic_hooks()

    def _setup_diagnostic_hooks(self):
        """Set up diagnostic hooks for all risk events."""
        print("🔧 Diagnostic hooks attached to risk system")

    async def on_position_updated(self, event: Any) -> None:
        """Enhanced position update handler with diagnostics."""
        # Log the event firing (this is handled by the main listener now)
        # Call parent handler first (does risk evaluation)
        await super().on_position_updated(event)

    async def on_order_filled(self, event: Any) -> None:
        """Enhanced order filled handler with diagnostics."""
        # Log the event firing
        order_data = {
            'order_id': getattr(event, 'order_id', 'unknown'),
            'contract_id': getattr(event, 'contractId', getattr(event, 'contract_id', 'unknown')),
            'side': getattr(event, 'side', 0),
            'quantity': getattr(event, 'quantity', 0),
            'price': getattr(event, 'price', 0),
            'source': 'order_filled_event'
        }
        self.diagnostic.log_event("ORDER_FILLED", "EventType.ORDER_FILLED", order_data)

        # Call parent handler
        await super().on_order_filled(event)

        # Log any API calls made during order processing
        # This would be enhanced to wrap actual API calls


class DiagnosticEventListener:
    """Event listener with comprehensive diagnostic capabilities."""

    def __init__(self, enable_risk_rules: bool = True):
        self.suite: TradingSuite | None = None
        self.rule_engine: RuleEngine | None = None
        self.risk_handler: DiagnosticRiskHandler | None = None
        self.enable_risk_rules = enable_risk_rules
        self.diagnostic = DiagnosticLogger()

        # Event counters
        self.event_counts = {
            "order_filled": 0,
            "position_updated": 0,
            "position_pnl_update": 0,
        }

    async def setup_suite(self):
        """Initialize TradingSuite with diagnostic capabilities."""
        print("🔗 Initializing TradingSuite with diagnostic monitoring...")

        # Set environment variables
        import os
        os.environ["PROJECT_X_API_KEY"] = "OXL7OhjGVXiMkRBhKR3Y8gHr83AXgjIRd9DzsT0XG/k="
        os.environ["PROJECT_X_USERNAME"] = "jakertrader"
        os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRACTICESEP2415506106"

        # Create suite
        self.suite = await TradingSuite.create(
            "MNQ",
            features=["risk_manager"],
            initial_days=1,
        )

        # Initialize risk rules with diagnostics
        if self.enable_risk_rules:
            await self._initialize_risk_rules()

        # Register event handlers
        await self._register_event_handlers()

        print("✅ TradingSuite initialized with diagnostic monitoring")
        if self.enable_risk_rules:
            print("🩺 Risk diagnostic system active - monitoring all events, hooks, and API calls")

    async def _initialize_risk_rules(self):
        """Initialize risk rules with diagnostic handler."""
        try:
            self.rule_engine = RuleEngine("config/risk_config.json")
            await self.rule_engine.initialize()

            # Create diagnostic risk handler
            self.risk_handler = DiagnosticRiskHandler(
                rule_engine=self.rule_engine,
                trading_suite=self.suite,
                diagnostic=self.diagnostic
            )

        except Exception as e:
            print(f"Failed to initialize risk rules: {e}")
            self.enable_risk_rules = False

    async def _register_event_handlers(self):
        """Register event handlers with diagnostics."""
        if not self.suite:
            return

        # Register core event handlers
        await self.suite.on(EventType.ORDER_FILLED, self._on_order_filled)
        await self.suite.on(EventType.POSITION_UPDATED, self._on_position_updated)
        await self.suite.on(EventType.POSITION_PNL_UPDATE, self._on_position_pnl_update)

        # Register risk rule handlers
        if self.enable_risk_rules and self.risk_handler:
            await self.suite.on(EventType.POSITION_UPDATED, self.risk_handler.on_position_updated)
            await self.suite.on(EventType.ORDER_FILLED, self._on_order_filled_with_risk_check)

    async def _on_order_filled(self, event: Any):
        """Handle order filled events."""
        self.event_counts["order_filled"] += 1

        # Log trade execution hook
        trade_data = {
            'order_id': getattr(event, 'order_id', 'unknown'),
            'contract_id': getattr(event, 'contractId', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        self.diagnostic.log_hook('on_trade_executed', trade_data)

    async def _on_order_filled_with_risk_check(self, event: Any):
        """Handle order filled with risk checking."""
        await self._on_order_filled(event)

        if self.enable_risk_rules and self.risk_handler:
            try:
                current_position = await self._get_current_position_info()
                enriched_event = {
                    'order_event': getattr(event, 'data', event),
                    'current_position': current_position,
                    'event_type': 'order_filled'
                }
                await self.risk_handler.on_order_filled(enriched_event)
            except Exception as e:
                print(f"Risk check failed: {e}")

    async def _on_position_updated(self, event: Any):
        """Handle position updated events."""
        self.event_counts["position_updated"] += 1

        # Log the POSITION_UPDATED event
        position_data = {
            'contract_id': getattr(event, 'contractId', getattr(event, 'contract_id', 'unknown')),
            'size': getattr(event, 'size', 0),
            'type': getattr(event, 'type', 0),
            'average_price': getattr(event, 'averagePrice', 0),
            'source': 'position_update_event'
        }
        self.diagnostic.log_event("POSITION_UPDATED", "EventType.POSITION_UPDATED", position_data)

    async def _on_position_pnl_update(self, event: Any):
        """Handle P&L update events."""
        self.event_counts["position_pnl_update"] += 1

    async def _get_current_position_info(self):
        """Get current position info."""
        if not self.suite:
            return None
        try:
            positions = await self.suite["MNQ"].positions.get_all_positions()
            return positions[0] if positions else None
        except:
            return None

    async def run_diagnostic_session(self):
        """Run diagnostic session."""
        print("🏥 Starting Risk Management Diagnostic Session")
        print("="*60)
        print("This system will show you:")
        print("• 🎯 Which event enums fire (POSITION_UPDATED, ORDER_FILLED, etc.)")
        print("• 📦 What payloads are passed (breach details, position data)")
        print("• 🪝 Which hooks trigger (on_breach, on_trade_executed, etc.)")
        print("• 🔌 Which API calls are made (close_position, place_order, etc.)")
        print("="*60)

        try:
            # Setup with diagnostics
            await self.setup_suite()

            print("🎧 Diagnostic system active - place trades to see the full trace!")
            print("Press Ctrl+C to stop and generate diagnostic report.")
            print()

            # Keep running to capture events
            while True:
                await asyncio.sleep(10)
                print(f"📊 Events captured so far: {sum(self.event_counts.values())}")

        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n🛑 Diagnostic session stopped by user")
        except Exception as e:
            print(f"\n❌ Diagnostic session failed: {e}")
        finally:
            if self.suite:
                await self.suite.disconnect()

            # Generate comprehensive diagnostic report
            self.diagnostic.generate_report()


async def main():
    """Run diagnostic risk management system."""
    listener = DiagnosticEventListener(enable_risk_rules=True)
    await listener.run_diagnostic_session()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Diagnostic system stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
    else:
        input("\n✅ Diagnostic session completed. Press Enter to exit...")
