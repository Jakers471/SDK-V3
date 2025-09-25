#!/usr/bin/env python3
"""
Execution Flow Tracer - Shows EXACTLY where risk rules go and how hooks execute

This traces the complete execution path:
Event → Risk Rule Evaluation → Hook Execution → API Call → Result
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
import traceback


class ExecutionFlowTracer:
    """Traces the complete execution flow of risk management system."""

    def __init__(self):
        self.flow_steps = []
        self.current_flow_id = 0
        self.active_flows = {}

    def start_flow(self, flow_type: str, trigger_event: Any) -> int:
        """Start a new execution flow."""
        self.current_flow_id += 1
        flow_id = self.current_flow_id

        flow = {
            'id': flow_id,
            'type': flow_type,
            'start_time': time.time(),
            'trigger': self._extract_trigger_info(trigger_event),
            'steps': []
        }

        self.active_flows[flow_id] = flow

        self._log_step(flow_id, "FLOW_START", f"🚀 Starting {flow_type} flow", {
            'trigger_event': trigger_event,
            'flow_id': flow_id
        })

        return flow_id

    def _extract_trigger_info(self, event: Any) -> Dict[str, Any]:
        """Extract key info from trigger event."""
        if hasattr(event, 'contractId'):
            return {
                'contract_id': event.contractId,
                'size': getattr(event, 'size', 0),
                'type': getattr(event, 'type', 'unknown')
            }
        elif isinstance(event, dict):
            return {
                'contract_id': event.get('contractId', event.get('contract_id', 'unknown')),
                'size': event.get('size', 0),
                'type': event.get('type', 'unknown')
            }
        return {'type': 'unknown_event'}

    def trace_risk_evaluation(self, flow_id: int, rule_name: str, event_data: Any, rule_result: bool):
        """Trace risk rule evaluation."""
        self._log_step(flow_id, "RISK_EVAL", f"🛡️ {rule_name} evaluating", {
            'rule_name': rule_name,
            'event_data': event_data,
            'result': rule_result,
            'breach_detected': not rule_result  # False means breach detected
        })

    def trace_hook_execution(self, flow_id: int, hook_name: str, hook_data: Any):
        """Trace hook execution."""
        self._log_step(flow_id, "HOOK_EXEC", f"🪝 {hook_name} executing", {
            'hook_name': hook_name,
            'data': hook_data
        })

    def trace_api_call(self, flow_id: int, method_name: str, parameters: Any, result: Any = None):
        """Trace API call execution."""
        self._log_step(flow_id, "API_CALL", f"🔌 {method_name} calling", {
            'method': method_name,
            'parameters': parameters,
            'result': result
        })

    def trace_flow_completion(self, flow_id: int, final_result: Any = None):
        """Complete a flow and show final result."""
        if flow_id in self.active_flows:
            flow = self.active_flows[flow_id]
            duration = time.time() - flow['start_time']

            self._log_step(flow_id, "FLOW_END", f"✅ Flow completed in {duration:.3f}s", {
                'duration': duration,
                'final_result': final_result,
                'total_steps': len(flow['steps'])
            })

            # Move to completed flows
            self.flow_steps.append(flow)
            del self.active_flows[flow_id]

    def _log_step(self, flow_id: int, step_type: str, message: str, data: Any):
        """Log a single execution step."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        step = {
            'flow_id': flow_id,
            'timestamp': timestamp,
            'type': step_type,
            'message': message,
            'data': data
        }

        # Add to active flow
        if flow_id in self.active_flows:
            self.active_flows[flow_id]['steps'].append(step)

        # Print immediate output with flow tracing
        flow_prefix = f"[Flow-{flow_id}]"
        print(f"{flow_prefix} {timestamp} | {step_type} | {message}")

        # Show key data
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['contract_id', 'size', 'result', 'breach_detected', 'method', 'final_result']:
                    print(f"{flow_prefix}   └─ {key}: {value}")

    def show_flow_diagram(self, flow_id: int = None):
        """Show ASCII diagram of execution flow."""
        print("\n" + "="*80)
        print("EXECUTION FLOW DIAGRAM")
        print("="*80)

        flows_to_show = [self.active_flows[flow_id]] if flow_id and flow_id in self.active_flows else list(self.active_flows.values())

        for flow in flows_to_show[-5:]:  # Show last 5 flows
            print(f"\n🔄 Flow-{flow['id']} ({flow['type']})")
            print(f"   Trigger: {flow['trigger']}")

            for i, step in enumerate(flow['steps']):
                connector = "├──" if i < len(flow['steps']) - 1 else "└──"
                print(f"   {connector} {step['timestamp']} {step['type']}: {step['message']}")

                # Show key results
                if step['type'] == 'RISK_EVAL' and 'breach_detected' in step['data']:
                    status = "🚨 BREACH!" if step['data']['breach_detected'] else "✅ OK"
                    print(f"      └─ Status: {status}")

                elif step['type'] == 'API_CALL' and 'result' in step['data']:
                    result = step['data']['result']
                    status = "✅ SUCCESS" if result and result.get('success') else "❌ FAILED"
                    print(f"      └─ Result: {status}")

        print("="*80)


# Global tracer instance
execution_tracer = ExecutionFlowTracer()


class TracedMaxContractsRule:
    """Max contracts rule with execution tracing."""

    def __init__(self, config):
        self.config = config
        self._breach_count = 0

    async def check(self, position_event: Any, trading_suite: Any) -> bool:
        """Check rule with full execution tracing."""
        # Start execution flow
        flow_id = execution_tracer.start_flow("RISK_RULE_EVALUATION", position_event)

        try:
            execution_tracer.trace_risk_evaluation(
                flow_id, "MaxContractsRule",
                position_event, False  # Will be updated with real result
            )

            # Extract position data safely
            position_data = self._extract_position_data(position_event)
            if not position_data:
                execution_tracer.trace_flow_completion(flow_id, "EXTRACTION_FAILED")
                return True

            current_size = abs(position_data['size'])

            # Log evaluation details
            eval_data = {
                'current_size': current_size,
                'max_allowed': self.config.max_size,
                'will_breach': current_size > self.config.max_size
            }
            execution_tracer._log_step(flow_id, "EVAL_DETAIL", f"📊 Size check: {current_size} > {self.config.max_size}", eval_data)

            if current_size > self.config.max_size:
                # Breach detected - handle it
                await self._handle_breach(position_data, trading_suite, flow_id)
                execution_tracer.trace_flow_completion(flow_id, "BREACH_HANDLED")
                return False

            execution_tracer.trace_flow_completion(flow_id, "NO_BREACH")
            return True

        except Exception as e:
            execution_tracer._log_step(flow_id, "ERROR", f"❌ Rule evaluation failed: {e}", {'error': str(e)})
            execution_tracer.trace_flow_completion(flow_id, "ERROR")
            return True

    def _extract_position_data(self, position_event: Any):
        """Extract position data with tracing."""
        try:
            if isinstance(position_event, dict) and 'current_position' in position_event:
                current_pos = position_event['current_position']
                if current_pos:
                    order_event = position_event.get('order_event', {})
                    contract_id = (order_event.get('contractId') or
                                 order_event.get('contract_id') or
                                 (current_pos['contractId'] if hasattr(current_pos, '__getitem__') else getattr(current_pos, 'contractId', 'unknown')) or
                                 'unknown')
                    account_id = (order_event.get('accountId') or
                                order_event.get('account_id') or
                                'unknown')
                    size = abs(current_pos['size'] if hasattr(current_pos, '__getitem__') else getattr(current_pos, 'size', 0))

                    return {
                        'contract_id': contract_id,
                        'account_id': account_id,
                        'size': size,
                        'event': position_event
                    }
            return None
        except Exception as e:
            print(f"Position extraction error: {e}")
            return None

    async def _handle_breach(self, position_data: Dict[str, Any], trading_suite: Any, flow_id: int):
        """Handle breach with tracing."""
        self._breach_count += 1

        # Log breach
        breach_data = {
            'rule': 'max_contracts',
            'contract_id': position_data['contract_id'],
            'breach_size': position_data['size'],
            'limit': self.config.max_size,
            'breach_count': self._breach_count
        }
        execution_tracer.trace_hook_execution(flow_id, "on_breach_internal", breach_data)

        # Auto-flatten if enabled
        if self.config.auto_flatten and trading_suite:
            await self._auto_flatten(position_data, trading_suite, flow_id)

    async def _auto_flatten(self, position_data: Dict[str, Any], trading_suite: Any, flow_id: int):
        """Auto-flatten position with tracing."""
        contract_id = position_data['contract_id']

        execution_tracer.trace_hook_execution(flow_id, "auto_flatten_start", {
            'contract_id': contract_id,
            'action': 'closing_position'
        })

        try:
            # Simulate API call (in real code this would be actual API)
            execution_tracer.trace_api_call(flow_id, "close_position_direct", {
                'contract_id': contract_id,
                'account_id': 'simulated'
            }, {'success': True, 'contract_id': contract_id})

            execution_tracer.trace_hook_execution(flow_id, "auto_flatten_complete", {
                'contract_id': contract_id,
                'status': 'success'
            })

        except Exception as e:
            execution_tracer.trace_hook_execution(flow_id, "auto_flatten_failed", {
                'contract_id': contract_id,
                'error': str(e)
            })


async def demo_execution_flow():
    """Demonstrate the complete execution flow."""
    print("🎯 EXECUTION FLOW TRACER DEMO")
    print("="*60)
    print("This shows EXACTLY where risk rules go and how hooks execute")
    print("="*60)

    # Create traced rule
    from rules.max_contracts_rule import MaxContractsConfig
    config = MaxContractsConfig(enabled=True, max_size=2, auto_flatten=True)
    traced_rule = TracedMaxContractsRule(config)

    # Simulate position update that triggers breach
    breach_event = {
        'current_position': type('MockPos', (), {
            'contractId': 'CON.F.US.MNQ.Z25',
            'size': 5,  # This exceeds limit of 2
            '__getitem__': lambda self, key: getattr(self, key)
        })(),
        'order_event': {'contractId': 'CON.F.US.MNQ.Z25', 'accountId': 'DEMO123'}
    }

    print("\n🚨 Simulating position update that triggers risk rule breach...")
    print("Position size: 5 contracts (limit: 2)")
    print()

    # Execute the rule - this will create the full trace
    result = await traced_rule.check(breach_event, None)

    print(f"\n📋 Rule check result: {result} (False = breach detected, action taken)")

    # Show flow diagram
    execution_tracer.show_flow_diagram()

    print("\n" + "="*60)
    print("🎯 EXECUTION FLOW SUMMARY")
    print("="*60)
    print("1. 🎯 Event fires (POSITION_UPDATED)")
    print("2. 🛡️ Risk rule evaluates position size")
    print("3. 🚨 Breach detected (size > limit)")
    print("4. 🪝 Hook executes (on_breach)")
    print("5. 🔌 API call made (close_position_direct)")
    print("6. ✅ Flow completes with result")
    print()
    print("This is the EXACT path your 32 risk rules will follow!")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(demo_execution_flow())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        traceback.print_exc()
    finally:
        input("\n✅ Demo complete. Press Enter to exit...")
