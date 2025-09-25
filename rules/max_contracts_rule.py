"""
Max Contracts Risk Rule

Enforces maximum position size limits per instrument.
Can log breaches and optionally auto-flatten positions.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

from project_x_py.types.trading import OrderSide
from project_x_py.utils import ProjectXLogger

logger = ProjectXLogger.get_logger(__name__)


@dataclass
class MaxContractsConfig:
    """Configuration for Max Contracts rule."""
    enabled: bool = False
    max_size: int = 3
    severity: str = "high"
    auto_flatten: bool = False  # Set to True to automatically close breaching positions


class MaxContractsRule:
    """
    Risk rule that enforces maximum contract limits per instrument.

    Monitors position updates and alerts/logs when position sizes exceed
    configured limits. Can optionally auto-flatten breaching positions.
    """

    def __init__(self, config: MaxContractsConfig):
        """
        Initialize the Max Contracts rule.

        Args:
            config: Configuration object with limits and behavior settings
        """
        self.config = config
        self._breach_count = 0

    async def check(self, position_event: Any, trading_suite: Any) -> bool:
        """
        Check if a position update violates the max contracts rule.

        Args:
            position_event: Position update event object
            trading_suite: TradingSuite instance for position management operations

        Returns:
            bool: True if within limits, False if breach detected
        """
        if not self.config.enabled:
            logger.debug("MaxContractsRule: disabled, skipping check")
            return True

        logger.debug(f"MaxContractsRule: checking position against limit of {self.config.max_size}")

        try:
            # Extract position data safely
            position_data = self._extract_position_data(position_event)
            if not position_data:
                logger.warning("Could not extract position data from event")
                return True

            # Check size limit
            current_size = abs(position_data['size'])
            if current_size > self.config.max_size:
                await self._handle_breach(position_data, trading_suite)
                return False

            return True

        except Exception as e:
            logger.error(f"Error in MaxContractsRule.check: {e}")
            return True  # Fail-safe: allow trade on error

    def _extract_position_data(self, position_event: Any) -> Optional[Dict[str, Any]]:
        """Extract position data from event object safely."""
        try:
            # Handle enriched order_filled events with current_position
            if isinstance(position_event, dict) and 'current_position' in position_event:
                current_pos = position_event['current_position']
                if current_pos:
                    # Extract contract from order event or position data
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

            # Handle regular position update events
            if isinstance(position_event, dict):
                position = position_event.get('position') or position_event.get('new_position') or position_event
                contract_id = position_event.get('contractId') or position_event.get('contract_id', 'unknown')
                account_id = position_event.get('accountId') or position_event.get('account_id', 'unknown')
                size = position.get('size', 0) if isinstance(position, dict) else getattr(position, 'size', 0)
            else:
                # Object format
                position = getattr(position_event, 'position', None) or getattr(position_event, 'new_position', None) or position_event
                contract_id = getattr(position_event, 'contractId', None) or getattr(position_event, 'contract_id', 'unknown')
                account_id = getattr(position_event, 'accountId', None) or getattr(position_event, 'account_id', 'unknown')
                size = getattr(position, 'size', 0)

            return {
                'contract_id': contract_id,
                'account_id': account_id,
                'size': size,
                'event': position_event
            }

        except Exception as e:
            logger.error(f"Failed to extract position data: {e}")
            return None

    async def _handle_breach(self, position_data: Dict[str, Any], trading_suite: Any) -> None:
        """Handle a max contracts breach."""
        self._breach_count += 1

        # Log the breach
        self._log_breach(position_data)

        # Optional: auto-flatten if enabled
        if self.config.auto_flatten:
            await self._auto_flatten(position_data, trading_suite)

    def _log_breach(self, position_data: Dict[str, Any]) -> None:
        """Log a max contracts breach."""
        contract_id = position_data['contract_id']
        account_id = position_data['account_id']
        current_size = abs(position_data['size'])

        severity_emoji = "🚨" if self.config.severity == "high" else "⚠️"

        logger.warning(
            f"{severity_emoji} MAX_CONTRACTS_BREACH "
            f"[Rule: {self.config.max_size} max] | "
            f"Size: {current_size} > {self.config.max_size} | "
            f"Contract: {contract_id} | "
            f"Account: {account_id} | "
            f"Breach #{self._breach_count}"
        )

    async def _auto_flatten(self, position_data: Dict[str, Any], trading_suite: Any) -> None:
        """Automatically flatten a breaching position."""
        if not trading_suite:
            logger.warning("No TradingSuite provided for auto-flatten")
            return

        try:
            contract_id = position_data['contract_id']

            logger.info(f"🔄 AUTO-FLATTENING breach position: {contract_id}")

            # Use PositionManager's close_position_direct method
            result = await trading_suite["MNQ"].positions.close_position_direct(contract_id)

            if result and result.get('success'):
                logger.info(f"✅ Auto-flattened breaching position: {contract_id}")
            else:
                logger.error(f"❌ Failed to auto-flatten: {contract_id}")

        except Exception as e:
            logger.error(f"Error during auto-flatten: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rule statistics."""
        return {
            'rule_name': 'max_contracts',
            'enabled': self.config.enabled,
            'max_size': self.config.max_size,
            'severity': self.config.severity,
            'auto_flatten': self.config.auto_flatten,
            'breach_count': self._breach_count
        }

    async def reset(self) -> None:
        """Reset rule state (for testing or session reset)."""
        self._breach_count = 0
        logger.info("MaxContractsRule state reset")


# Example usage and testing
async def test_max_contracts_rule():
    """Test the Max Contracts rule with mock data."""
    config = MaxContractsConfig(
        enabled=True,
        max_size=3,
        severity="high",
        auto_flatten=False
    )

    rule = MaxContractsRule(config)

    # Mock position event
    mock_event = {
        'contractId': 'MNQ_TEST',
        'accountId': 'TEST123',
        'position': {'size': 5},  # Breach: 5 > 3
        'size': 5
    }

    # Test breach detection
    result = await rule.check(mock_event, None)  # None trading_suite for test
    assert result == False, "Should detect breach"

    # Test stats
    stats = rule.get_stats()
    assert stats['breach_count'] == 1, "Should count breach"

    logger.info("MaxContractsRule test passed!")
    return rule


if __name__ == "__main__":
    # Run test
    asyncio.run(test_max_contracts_rule())
