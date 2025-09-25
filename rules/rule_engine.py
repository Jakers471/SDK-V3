"""
Rule Engine for Risk Management

Loads and executes risk rules based on configuration.
Integrates with the event-driven system.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from project_x_py.utils import ProjectXLogger

from .max_contracts_rule import MaxContractsConfig, MaxContractsRule

logger = ProjectXLogger.get_logger(__name__)


class RuleEngine:
    """
    Engine for loading and executing risk management rules.

    Loads configuration and instantiates rule objects.
    Processes events through all active rules.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the rule engine.

        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path or "config/risk_config.json"
        self.config = {}
        self.rules = []
        self.stats = {
            'events_processed': 0,
            'rules_checked': 0,
            'breaches_detected': 0
        }

    async def initialize(self) -> None:
        """Load configuration and initialize rules."""
        await self._load_config()
        await self._initialize_rules()
        logger.info(f"RuleEngine initialized with {len(self.rules)} rules")

    async def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self.config = {"rules": {}, "global": {"dry_run": True}}
                return

            with open(config_file, 'r') as f:
                self.config = json.load(f)

            logger.info(f"Loaded risk config from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {"rules": {}, "global": {"dry_run": True}}

    async def _initialize_rules(self) -> None:
        """Initialize rule objects from configuration."""
        rules_config = self.config.get("rules", {})

        # Max Contracts Rule
        if rules_config.get("max_contracts", {}).get("enabled", False):
            max_contracts_config = MaxContractsConfig(
                enabled=rules_config["max_contracts"]["enabled"],
                max_size=rules_config["max_contracts"]["max_size"],
                severity=rules_config["max_contracts"]["severity"],
                auto_flatten=rules_config["max_contracts"].get("auto_flatten", False)
            )
            rule = MaxContractsRule(max_contracts_config)
            self.rules.append(rule)
            logger.info(f"Enabled MaxContractsRule: max_size={max_contracts_config.max_size}")

    async def process_event(self, event_type: str, event_data: Any, api_client: Any = None) -> Dict[str, Any]:
        """
        Process an event through all active rules.

        Args:
            event_type: Type of event (e.g., 'position_updated')
            event_data: Event data object
            api_client: API client for rule enforcement

        Returns:
            Dict with processing results
        """
        self.stats['events_processed'] += 1
        logger.info(f"🏗️ RuleEngine processing {event_type} event through {len(self.rules)} active rules")

        results = {
            'event_type': event_type,
            'rules_checked': 0,
            'breaches': [],
            'actions_taken': []
        }

        # Process both position update and order filled events
        if event_type not in ['position_updated', 'order_filled']:
            return results

        # Check all rules
        for rule in self.rules:
            self.stats['rules_checked'] += 1
            results['rules_checked'] += 1

            try:
                # Run rule check - pass trading_suite for auto-flatten functionality
                rule_passed = await rule.check(event_data, self.trading_suite if hasattr(self, 'trading_suite') else api_client)

                if not rule_passed:
                    self.stats['breaches_detected'] += 1
                    breach_info = {
                        'rule': rule.__class__.__name__,
                        'rule_config': rule.get_stats()
                    }
                    results['breaches'].append(breach_info)

                    # Track actions (auto-flatten would be logged here)
                    if hasattr(rule, 'config') and rule.config.auto_flatten:
                        results['actions_taken'].append({
                            'rule': rule.__class__.__name__,
                            'action': 'auto_flatten_attempted'
                        })

            except Exception as e:
                logger.error(f"Error processing rule {rule.__class__.__name__}: {e}")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'engine_stats': self.stats,
            'rules': [rule.get_stats() for rule in self.rules],
            'config_summary': {
                'rules_enabled': len(self.rules),
                'config_file': self.config_path
            }
        }

    async def reload_config(self) -> None:
        """Reload configuration and reinitialize rules."""
        logger.info("Reloading risk configuration...")
        await self._load_config()
        await self._initialize_rules()

    async def reset_stats(self) -> None:
        """Reset engine statistics."""
        self.stats = {
            'events_processed': 0,
            'rules_checked': 0,
            'breaches_detected': 0
        }
        logger.info("RuleEngine stats reset")


# Integration helper for event listeners
class RiskEventHandler:
    """
    Event handler that integrates RuleEngine with event streams.

    Can be registered with TradingSuite event listeners.
    """

    def __init__(self, rule_engine: RuleEngine, trading_suite: Any = None):
        self.rule_engine = rule_engine
        self.trading_suite = trading_suite
        self.api_client = trading_suite.client if trading_suite else None  # Keep for backward compatibility

    async def on_position_updated(self, event: Any) -> None:
        """Handle position update events and run risk rules."""
        logger.info("🔍 RiskEventHandler received position_updated event")

        # Add detailed logging of the event data
        logger.debug(f"📊 Event data type: {type(event)}")
        if hasattr(event, 'data'):
            logger.debug(f"📊 Event.data: {event.data}")
        else:
            logger.debug(f"📊 Event object: {event}")

        # Extract position size for immediate visibility
        try:
            if isinstance(event, dict) and 'size' in event:
                size = event.get('size', 0)
                contract = event.get('contractId', 'unknown')
                logger.info(f"📏 Position size check: {contract} = {size} contracts")
            elif hasattr(event, 'data') and isinstance(event.data, dict):
                size = event.data.get('size', 0)
                contract = event.data.get('contractId', 'unknown')
                logger.info(f"📏 Position size check: {contract} = {size} contracts")
            elif hasattr(event, 'size'):
                size = getattr(event, 'size', 0)
                contract = getattr(event, 'contractId', 'unknown')
                logger.info(f"📏 Position size check: {contract} = {size} contracts")
            else:
                logger.warning("📏 Could not extract position size from event")
        except Exception as e:
            logger.error(f"📏 Error extracting position size: {e}")

        results = await self.rule_engine.process_event('position_updated', event, self.api_client)

        # Log that rules were checked (even if no breaches)
        logger.info(f"⚖️ Risk rules evaluated: {results['rules_checked']} rules checked, {len(results['breaches'])} breaches found")

        # Log summary if breaches detected
        if results['breaches']:
            logger.warning(
                f"🚨 RISK BREACHES DETECTED: {len(results['breaches'])} rules triggered"
            )

            for breach in results['breaches']:
                rule_name = breach.get('rule', 'UnknownRule')
                rule_config = breach.get('rule_config', {})

                logger.warning(
                    f"   Rule: {rule_name} | "
                    f"Config: {rule_config}"
                )

                # Check if auto-flatten is enabled and attempt to close position
                if rule_config.get('auto_flatten', False):
                    logger.warning(f"💥 AUTO-FLATTEN ENABLED: Attempting to close position for {rule_name}")
                    # Auto-flatten logic would go here
                    try:
                        # Extract account and contract IDs for closing
                        account_id = None
                        contract_id = None

                        if isinstance(event, dict):
                            account_id = event.get('accountId')
                            contract_id = event.get('contractId')
                        elif hasattr(event, 'data') and isinstance(event.data, dict):
                            account_id = event.data.get('accountId')
                            contract_id = event.data.get('contractId')
                        elif hasattr(event, 'accountId') and hasattr(event, 'contractId'):
                            account_id = event.accountId
                            contract_id = event.contractId

                        if contract_id and self.trading_suite:
                            logger.info(f"📞 Calling PositionManager to close position: {contract_id}")
                            # Use PositionManager's close_position_direct method
                            result = await self.trading_suite["MNQ"].positions.close_position_direct(contract_id)
                            logger.info(f"✅ Close position result: {result}")
                        else:
                            logger.error(f"❌ Missing contract_id or trading_suite for auto-flatten: contract={contract_id}, suite={self.trading_suite is not None}")

                    except Exception as e:
                        logger.error(f"❌ Auto-flatten failed: {e}")
        else:
            logger.info("✅ No breaches detected - position within limits")

    async def on_order_filled(self, event: Any) -> None:
        """Handle order filled events and check risk rules immediately after execution."""
        logger.info("🔍 RiskEventHandler received order_filled event")

        # Add detailed logging of the event data
        logger.debug(f"📊 Order event data type: {type(event)}")
        if hasattr(event, 'data'):
            logger.debug(f"📊 Order event.data: {event.data}")
        else:
            logger.debug(f"📊 Order event object: {event}")

        # Process risk rules immediately after order execution
        results = await self.rule_engine.process_event('order_filled', event, self.api_client)

        # Log that rules were checked (even if no breaches)
        logger.info(f"⚖️ Risk rules evaluated: {results['rules_checked']} rules checked, {len(results['breaches'])} breaches found")

        # Log summary if breaches detected
        if results['breaches']:
            logger.warning(
                f"🚨 RISK BREACHES DETECTED: {len(results['breaches'])} rules triggered"
            )

            for breach in results['breaches']:
                rule_name = breach.get('rule', 'UnknownRule')
                rule_config = breach.get('rule_config', {})

                logger.warning(
                    f"   Rule: {rule_name} | "
                    f"Config: {rule_config}"
                )

                # Check if auto-flatten is enabled and attempt to close position
                if rule_config.get('auto_flatten', False):
                    logger.warning(f"💥 AUTO-FLATTEN ENABLED: Attempting to close position for {rule_name}")
                    # Auto-flatten logic would go here
                    try:
                        # Extract position data from enriched event for order_filled
                        current_position = None
                        if isinstance(event, dict) and 'current_position' in event:
                            current_position = event['current_position']

                        if current_position and self.trading_suite:
                            position_size = current_position.get('size', 0)
                            contract_id = current_position.get('contract', 'unknown')

                            if position_size != 0:
                                logger.info(f"📞 Calling PositionManager close_position_direct for {contract_id} (position size: {position_size})")
                                try:
                                    # Use PositionManager's close_position_direct method
                                    result = await self.trading_suite["MNQ"].positions.close_position_direct(contract_id)
                                    logger.info(f"✅ Auto-flatten PositionManager result: {result}")
                                except Exception as e:
                                    logger.error(f"❌ PositionManager call failed: {e}")
                            else:
                                logger.warning("⚠️ Position size is 0, no flattening needed")
                        else:
                            logger.error(f"❌ No position data available for auto-flatten: position={current_position}")

                    except Exception as e:
                        logger.error(f"❌ Auto-flatten failed: {e}")
        else:
            logger.info("✅ No breaches detected - trade within limits")


# Example usage
async def test_rule_engine():
    """Test the rule engine with sample data."""
    engine = RuleEngine("config/risk_config.json")
    await engine.initialize()

    # Create mock API client
    class MockAPIClient:
        async def close_contract(self, account_id, contract_id):
            return {'success': True}

    api_client = MockAPIClient()

    # Test with breaching position
    mock_position_event = {
        'contractId': 'MNQ_TEST',
        'accountId': 'TEST123',
        'position': {'size': 5},  # Breach: 5 > 3 limit
        'size': 5
    }

    results = await engine.process_event('position_updated', mock_position_event, api_client)

    assert len(results['breaches']) == 1, "Should detect breach"
    assert results['breaches'][0]['rule'] == 'MaxContractsRule', "Should identify correct rule"

    # Check stats
    stats = engine.get_stats()
    assert stats['engine_stats']['breaches_detected'] == 1, "Should count breaches"

    logger.info("RuleEngine test passed!")
    return engine


if __name__ == "__main__":
    asyncio.run(test_rule_engine())
