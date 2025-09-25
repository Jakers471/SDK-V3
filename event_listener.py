#!/usr/bin/env python3
"""
Event Listener - Real-time Diagnostic Script

Listens to broker events via WebSocket/SignalR to validate SDK connectivity.
Logs order_filled, position_updated, and position_pnl_update events in real-time.

Usage: python event_listener.py
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from project_x_py import TradingSuite, EventType
from project_x_py.types.trading import OrderSide, OrderType, OrderStatus, PositionType
from rules.rule_engine import RuleEngine, RiskEventHandler

# Configure logging with timestamps - INFO level for clean readable logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

# Custom log filter to show only our important logs
class CleanLogFilter(logging.Filter):
    def filter(self, record):
        # Allow our event listener logs
        if record.name == '__main__':
            return True
        # Allow risk rule logs
        if record.name.startswith('rules'):
            return True
        # Allow critical connection status logs
        if 'WebSocket/SignalR' in str(record.getMessage()) or 'CONNECTED' in str(record.getMessage()):
            return True
        # Allow our custom emojis (trade executions, position updates, risk alerts)
        message = str(record.getMessage())
        if any(emoji in message for emoji in ['🔗', '🛡️', '🎧', '📈', '📉', '📊', '⚖️', '🚨', '👻', '📜', '✅', '❌']):
            return True
        # Block ALL other logs (SDK internal noise, HTTP requests, etc.)
        return False

# Apply filter to root logger
root_logger = logging.getLogger()
root_logger.addFilter(CleanLogFilter())

logger = logging.getLogger(__name__)


class EventListener:
    """Real-time event listener for diagnostic purposes with risk rules."""

    def __init__(self, enable_risk_rules: bool = True):
        self.suite: TradingSuite | None = None
        self.rule_engine: RuleEngine | None = None
        self.risk_handler: RiskEventHandler | None = None
        self.enable_risk_rules = enable_risk_rules

        self.event_counts = {
            "order_filled": 0,
            "position_updated": 0,
            "position_pnl_update": 0,
        }
        # Cache to reduce API calls
        self._position_cache: dict[str, Any] | None = None
        self._cache_timestamp: float = 0
        self._cache_ttl = 0.5  # 500ms cache

        # Track trade actions for better summary
        self._trade_actions = {
            "Open": 0,
            "Add": 0,
            "Reduce": 0,
            "Close": 0,
            "Reverse": 0,
            "Adjust": 0,
            "Unknown": 0
        }

        # Track position state to detect manual closes and ghost re-opens
        self._last_confirmed_position = None  # Last position confirmed by poll
        self._position_flat_timestamp = None  # When position last went to 0
        self._ignore_reopen_window = 3.0  # Seconds to ignore reopens after manual close
        self._stale_executions_filtered = 0  # Count of stale executions ignored

    async def setup_suite(self):
        """Initialize TradingSuite for event listening."""
        logger.info("🔗 Initializing TradingSuite for event listening...")

        # Set environment variables from user's input
        os.environ["PROJECT_X_API_KEY"] = "OXL7OhjGVXiMkRBhKR3Y8gHr83AXgjIRd9DzsT0XG/k="
        os.environ["PROJECT_X_USERNAME"] = "jakertrader"
        os.environ["PROJECT_X_ACCOUNT_NAME"] = "PRACTICESEP2415506106"

        # Create suite with minimal features for event listening
        self.suite = await TradingSuite.create(
            "MNQ",  # Micro futures for testing
            features=["risk_manager"],  # Enables position tracking
            initial_days=1,  # Minimal data for faster startup
        )

        # Initialize risk rules if enabled
        if self.enable_risk_rules:
            await self._initialize_risk_rules()

        # Register event handlers
        await self._register_event_handlers()

        logger.info("✅ TradingSuite initialized and event handlers registered")
        if self.enable_risk_rules and self.rule_engine:
            active_rules = len(self.rule_engine.rules)
            logger.info(f"🛡️ Risk rules active: {active_rules} rules loaded")
            # Log rule details
            for rule in self.rule_engine.rules:
                rule_stats = rule.get_stats()
                logger.info(f"   📋 Rule loaded: {rule_stats}")
        logger.info("🎧 Ready to receive real-time events from broker...")

    async def _register_event_handlers(self):
        """Register handlers for the three critical events."""
        if not self.suite:
            return

        # Order filled events
        await self.suite.on(EventType.ORDER_FILLED, self._on_order_filled)

        # Position updated events
        await self.suite.on(EventType.POSITION_UPDATED, self._on_position_updated)

        # Position P&L update events
        await self.suite.on(EventType.POSITION_PNL_UPDATE, self._on_position_pnl_update)

        # Register risk rule handlers if enabled
        if self.enable_risk_rules and self.risk_handler:
            logger.info("🔗 Registering risk rule event handlers...")

            # Register with suite-level events (should forward from components)
            await self.suite.on(EventType.POSITION_UPDATED, self.risk_handler.on_position_updated)
            await self.suite.on(EventType.ORDER_FILLED, self._on_order_filled_with_risk_check)
            logger.info("📡 Suite-level event handlers registered")

            # Also register directly with PositionManager to ensure we catch all events
            if hasattr(self.suite, '_instruments') and self.suite._instruments:
                # Multi-instrument mode
                for instrument_ctx in self.suite._instruments.values():
                    if hasattr(instrument_ctx, 'positions') and instrument_ctx.positions:
                        # Register for both event names that PositionManager uses
                        await instrument_ctx.positions.event_bus.on(EventType.POSITION_UPDATED, self.risk_handler.on_position_updated)
                        await instrument_ctx.positions.event_bus.on(EventType.POSITION_CLOSED, self.risk_handler.on_position_updated)
                        logger.info(f"📡 Direct registration with {instrument_ctx.symbol} PositionManager")
            elif hasattr(self.suite, '_positions'):
                # Single-instrument mode - register for PositionManager's callback system
                # This is the primary way PositionManager communicates events
                await self.suite._positions.add_callback('position_update', self.risk_handler.on_position_updated)
                await self.suite._positions.add_callback('position_closed', self.risk_handler.on_position_updated)
                logger.info("📞 Callback registration with PositionManager for position_update/position_closed")

                # Also register with event bus as backup
                await self.suite._positions.event_bus.on(EventType.POSITION_UPDATED, self.risk_handler.on_position_updated)
                await self.suite._positions.event_bus.on(EventType.POSITION_CLOSED, self.risk_handler.on_position_updated)
                logger.info("📡 Event bus registration with PositionManager")

            logger.info("✅ Risk rules registered and monitoring live events")

    async def _initialize_risk_rules(self) -> None:
        """Initialize the risk rule engine."""
        try:
            self.rule_engine = RuleEngine("config/risk_config.json")
            await self.rule_engine.initialize()

            # Create risk event handler with TradingSuite for manager access
            self.risk_handler = RiskEventHandler(
                rule_engine=self.rule_engine,
                trading_suite=self.suite
            )

        except Exception as e:
            logger.error(f"Failed to initialize risk rules: {e}")
            self.enable_risk_rules = False

    async def _on_order_filled(self, event: Any) -> None:
        """Handle order filled events with unified trade execution logging."""
        try:
            self.event_counts["order_filled"] += 1
            data = event.data

            order_id = self._safe_get(data, "order_id", "unknown")
            order_data = self._safe_get(data, "order_data", {})

            # Decode order details
            side_int = self._safe_get(order_data, "side", 0)
            side = "BUY" if side_int == OrderSide.BUY else "SELL"

            type_int = self._safe_get(order_data, "type", 2)
            order_type = self._decode_order_type(type_int)

            # Get position state before this fill (use cache when possible)
            prev_position = await self._get_current_position_info(force_refresh=False)

            # Wait for position update to propagate
            await asyncio.sleep(0.1)

            # Get position after fill (don't force refresh to reduce API calls)
            current_position = await self._get_current_position_info(force_refresh=False)

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Check if this is a stale execution after manual close
            now = asyncio.get_event_loop().time()
            is_stale_after_manual_close = (
                self._position_flat_timestamp and
                (now - self._position_flat_timestamp) < self._ignore_reopen_window and
                current_position and abs(current_position.get('size', 0)) > 0
            )

            if is_stale_after_manual_close:
                elapsed = now - self._position_flat_timestamp
                self._stale_executions_filtered += 1
                logger.warning(f"📜 STALE_EXECUTION_IGNORED | Order {order_id} | {elapsed:.1f}s after manual close")
                logger.warning(f"   This order fill is likely from before manual close - ignoring for position tracking")
                logger.warning(f"   Confirmed position remains: {self._last_confirmed_position or 'FLAT'}")
                return

            # Determine trade action type
            trade_action = self._classify_trade_action(prev_position, current_position, side)
            self._trade_actions[trade_action] += 1

            logger.info(f"\n📈 TRADE_EXECUTED | {timestamp}")
            logger.info(f"   ID: {order_id}")
            logger.info(f"   Action: {side} ({order_type}) - {trade_action}")

            # Show position transition with proper context
            if prev_position and current_position:
                prev_desc = f"{prev_position['direction']} {abs(prev_position['size'])}"
                current_desc = f"{current_position['direction']} {abs(current_position['size'])}"

                # Show position transition with proper context
                logger.info(f"   Position: {prev_desc} → {current_desc}")
                logger.info(f"   Avg Price: {current_position['avg_price']}")

                # For now, show unrealized P&L for remaining position
                if current_position.get('pnl') and abs(current_position['size']) > 0:
                    logger.info(f"   Unrealized PnL: {current_position['pnl']}")

                # Note: Realized PnL will be shown in session summary from position manager stats

            elif current_position:
                # Opening new position
                logger.info(f"   Position Opened: {current_position['direction']} {abs(current_position['size'])}")
                logger.info(f"   Avg Price: {current_position['avg_price']}")
            else:
                # Position fully closed
                if prev_position:
                    logger.info(f"   Position Closed: {prev_position['direction']} {abs(prev_position['size'])} → FLAT")
                    # Get final realized PnL for complete closure
                    realized_pnl = await self._get_incremental_realized_pnl(prev_position, None)
                    if realized_pnl is not None:
                        logger.info(f"   Realized PnL: ${realized_pnl:+.2f}")
                else:
                    logger.info(f"   Position: FLAT")

            logger.info(f"   Total Trades: {self.event_counts['order_filled']}")

        except Exception as e:
            logger.error(f"Error in event handler _on_order_filled: {e}")
            logger.error(f"Event data: {event.data}")

    async def _on_order_filled_with_risk_check(self, event: Any) -> None:
        """Handle order filled events with immediate risk checking."""
        # First, process the order filled event normally (for logging)
        await self._on_order_filled(event)

        # Then, immediately check risk rules with current position context
        if self.enable_risk_rules and self.risk_handler:
            try:
                # Get current position to provide context for risk checking
                current_position = await self._get_current_position_info(force_refresh=True)

                # Create enriched event data with position context
                enriched_event = {
                    'order_event': event.data if hasattr(event, 'data') else event,
                    'current_position': current_position,
                    'event_type': 'order_filled'
                }

                # Call risk handler immediately after trade execution
                await self.risk_handler.on_order_filled(enriched_event)

            except Exception as e:
                logger.error(f"Error in risk check after order fill: {e}")

    async def _on_position_updated(self, event: Any) -> None:
        """Handle position updated events - detect manual closes and filter ghost re-opens."""
        try:
            self.event_counts["position_updated"] += 1
            position = event.data

            # Handle both object and dict formats
            contract = self._safe_get(position, 'contractId', 'unknown')
            size = self._safe_get(position, 'size', 0)
            avg_price = self._safe_get(position, 'averagePrice', 0)
            pos_type = self._safe_get(position, 'type', 0)

            direction = self._decode_position_type(pos_type)
            now = asyncio.get_event_loop().time()

            # Detect manual position closures (size goes to 0)
            if size == 0 and self._last_confirmed_position and abs(self._last_confirmed_position.get('size', 0)) > 0:
                self._position_flat_timestamp = now
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                logger.info(f"\n📉 MANUAL_POSITION_CLOSED | {timestamp}")
                logger.info(f"   Contract: {contract}")
                logger.info(f"   Final Size: {size} (confirmed flat)")
                logger.info(f"   Previous Position: {self._last_confirmed_position.get('direction')} {abs(self._last_confirmed_position.get('size', 0))}")
                logger.info(f"   Ignoring reopen events for {self._ignore_reopen_window}s")

            # Check if this is a potential "ghost reopen" after a manual close
            elif (size != 0 and
                  self._position_flat_timestamp and
                  (now - self._position_flat_timestamp) < self._ignore_reopen_window):

                elapsed = now - self._position_flat_timestamp
                logger.warning(f"👻 GHOST_REOPEN_DETECTED | Contract: {contract} | Size: {size} | {elapsed:.1f}s after manual close")
                logger.warning("   This position change may be SDK catching up with manual order processing")
                logger.warning("   Ignoring for position state tracking - will be resolved by next poll")

                # Don't update last_confirmed_position for ghost reopens
                return

            # Update confirmed position state (skip ghost reopens)
            self._last_confirmed_position = {
                'contract': contract,
                'size': size,
                'direction': direction,
                'avg_price': f"${avg_price:.2f}" if avg_price else "unknown"
            }

            # When risk rules are active, let them handle detailed logging
            # Only log significant position changes (not ghost reopens)
            if size != 0 and not (self._position_flat_timestamp and (now - self._position_flat_timestamp) < self._ignore_reopen_window):
                if self.enable_risk_rules:
                    # Risk rules will handle their own logging
                    pass
                else:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    logger.info(f"\n📊 POSITION_UPDATED | {timestamp}")
                    logger.info(f"   Contract: {contract}")
                    logger.info(f"   Size: {size} ({direction})")
                    logger.info(f"   Avg Price: ${avg_price:.2f}")
                    logger.info(f"   Total Updates: {self.event_counts['position_updated']}")

        except Exception as e:
            logger.error(f"Error in event handler _on_position_updated: {e}")
            logger.error(f"Event data: {event.data}")

    async def _on_position_pnl_update(self, event: Any) -> None:
        """Handle position P&L update events - log periodically to avoid spam."""
        try:
            self.event_counts["position_pnl_update"] += 1
            pnl_data = event.data

            # Extract P&L details (handle both dict and object)
            contract = self._safe_get(pnl_data, "contractId", "unknown")
            unrealized_pnl = self._safe_get(pnl_data, "unrealizedPnl", 0)
            realized_pnl = self._safe_get(pnl_data, "realizedPnl", 0)

            # Only log P&L updates every 10th event to reduce spam
            if self.event_counts["position_pnl_update"] % 10 == 0:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                logger.info(f"\n💰 P&L_UPDATE | {timestamp}")
                logger.info(f"   Contract: {contract}")
                logger.info(f"   Unrealized PnL: ${unrealized_pnl:+.2f}")
                logger.info(f"   Realized PnL: ${realized_pnl:+.2f}")
                logger.info(f"   Total Updates: {self.event_counts['position_pnl_update']}")

        except Exception as e:
            logger.error(f"Error in event handler _on_position_pnl_update: {e}")
            logger.error(f"Event data: {event.data}")

    def _decode_order_type(self, type_int: int) -> str:
        """Decode order type integer to readable string."""
        try:
            order_type = OrderType(type_int)
            return order_type.name.replace('_', ' ').title()
        except ValueError:
            return f"UNKNOWN({type_int})"

    def _decode_order_status(self, status_int: int) -> str:
        """Decode order status integer to readable string."""
        try:
            status = OrderStatus(status_int)
            return status.name.replace('_', ' ').title()
        except ValueError:
            return f"UNKNOWN({status_int})"

    def _decode_position_type(self, type_int: int) -> str:
        """Decode position type integer to readable string."""
        try:
            pos_type = PositionType(type_int)
            return pos_type.name
        except ValueError:
            return f"UNKNOWN({type_int})"

    def _safe_get(self, obj: Any, key: str, default: Any = None) -> Any:
        """Safely get attribute from dict or object."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _classify_trade_action(self, prev_pos: dict[str, Any] | None, current_pos: dict[str, Any] | None, order_side: str) -> str:
        """Classify the type of trade action: Open, Add, Reduce, Close, Flip."""
        if not prev_pos and current_pos:
            # No previous position, now have one = OPEN
            return "Open"
        elif prev_pos and not current_pos:
            # Had position, now flat = CLOSE
            return "Close"
        elif prev_pos and current_pos:
            prev_size = prev_pos['size']
            current_size = current_pos['size']
            prev_direction = prev_pos['direction']
            current_direction = current_pos['direction']

            # Handle zero size cases
            if abs(prev_size) == 0 and abs(current_size) > 0:
                return "Open"
            elif abs(current_size) == 0 and abs(prev_size) > 0:
                return "Close"

            # Same direction changes
            if current_direction == prev_direction:
                if abs(current_size) > abs(prev_size):
                    return "Add"        # Scaling up
                elif abs(current_size) < abs(prev_size):
                    return "Reduce"     # Scaling down
                else:
                    return "Adjust"     # Same size, possibly price adjustment

            # Direction changed - this is a reversal (close old + open new)
            elif current_direction != prev_direction:
                return "Flip"

        # Unknown state
        return "Unknown"

    async def _get_realized_pnl(self, contract_id: str) -> float | None:
        """Get total realized PnL from position manager stats."""
        if not self.suite:
            return None

        try:
            # Use position manager reporting to get cumulative realized PnL
            report = await self.suite["MNQ"].positions.get_performance_report()
            return report.get("realized_pnl", 0.0)
        except Exception:
            return None

    def _get_incremental_realized_pnl(self, prev_pos: dict[str, Any], current_pos: dict[str, Any] | None) -> float | None:
        """Calculate realized PnL from a specific position change."""
        if not prev_pos:
            return None

        try:
            prev_size = abs(prev_pos['size'])
            prev_avg_price = prev_pos['avg_price']

            if not current_pos:
                # Complete closure - all remaining position is realized
                # This is an approximation since we don't have exact fill prices
                return 0.0  # We can't accurately calculate without fill-by-fill data

            current_size = abs(current_pos['size'])
            current_avg_price = current_pos['avg_price']

            if current_size < prev_size and prev_pos['direction'] == current_pos['direction']:
                # Position reduction in same direction
                # Calculate realized PnL from the portion that was closed
                closed_size = prev_size - current_size

                # Simple approximation: realized at current average price
                # In reality, this would need fill-by-fill P&L calculation
                realized_pnl = 0.0  # Placeholder - would need actual fill data

                return realized_pnl

            elif prev_pos['direction'] != current_pos['direction']:
                # Direction flip - entire previous position was closed
                # This would require tracking the closing price of the previous position
                return 0.0  # Placeholder

        except Exception:
            return None

        return None

    async def _get_current_position_info(self, force_refresh: bool = False) -> dict[str, Any] | None:
        """Get current position info from broker (ground truth) with caching."""
        if not self.suite:
            return None

        # Check cache first
        now = asyncio.get_event_loop().time()
        if not force_refresh and self._position_cache and (now - self._cache_timestamp) < self._cache_ttl:
            return self._position_cache

        try:
            # Use non-deprecated accessor
            positions = await self.suite["MNQ"].positions.get_all_positions()

            if not positions:
                self._position_cache = None
                self._cache_timestamp = now
                return None

            # For now, return info for the first position (MNQ)
            # In multi-instrument setups, you'd handle multiple
            position = positions[0] if positions else None
            if not position:
                self._position_cache = None
                self._cache_timestamp = now
                return None

            direction = self._decode_position_type(self._safe_get(position, 'type', 0))

            # Try to get P&L
            pnl_info = None
            try:
                current_price = await self.suite["MNQ"].data.get_current_price()
                if current_price:
                    pnl_data = await self.suite["MNQ"].positions.calculate_position_pnl(
                        position, float(current_price)
                    )
                    unrealized_pnl = pnl_data.get("unrealized_pnl", 0)
                    pnl_info = f"${unrealized_pnl:+.2f}"
            except Exception:
                pass

            result = {
                "contract": self._safe_get(position, 'contractId', 'unknown'),
                "size": self._safe_get(position, 'size', 0),
                "avg_price": f"${self._safe_get(position, 'averagePrice', 0):.2f}",
                "direction": direction,
                "pnl": pnl_info
            }

            # Cache result
            self._position_cache = result
            self._cache_timestamp = now

            return result

        except Exception as e:
            logger.warning(f"Could not fetch position info: {e}")
            return None

    async def log_connection_status(self):
        """Log current connection status."""
        if self.suite and self.suite.is_connected:
            logger.info("🔗 WebSocket/SignalR: CONNECTED")
        else:
            logger.warning("🔌 WebSocket/SignalR: DISCONNECTED")

    async def log_risk_status(self):
        """Log risk monitoring status."""
        if self.enable_risk_rules and self.rule_engine:
            stats = self.rule_engine.get_stats()
            events_processed = stats['engine_stats']['events_processed']
            rules_active = len(stats['rules'])

            if events_processed > 0:
                logger.info(f"🛡️ Risk monitoring active: {rules_active} rules processed {events_processed} events")
            else:
                logger.info(f"🛡️ Risk monitoring active: {rules_active} rules ready (waiting for events)")
        elif self.enable_risk_rules:
            logger.warning("🛡️ Risk rules enabled but not initialized")
        # If risk rules disabled, don't log anything

    async def log_event_summary(self):
        """Log summary of events received."""
        total_events = sum(self.event_counts.values())
        if total_events > 0:
            logger.info(f"\n📊 SESSION SUMMARY | Total Events: {total_events}")

            # Show trade action breakdown (filter out zero counts)
            actions_summary = []
            meaningful_actions = []
            for action, count in self._trade_actions.items():
                if count > 0:
                    actions_summary.append(f"{action}:{count}")
                    meaningful_actions.append(action)

            if actions_summary:
                logger.info(f"   Trade Types: {', '.join(actions_summary)}")

                # Show which actions realize PnL
                pnl_actions = [action for action in meaningful_actions if action in ["Reduce", "Close", "Flip"]]
                if pnl_actions:
                    logger.info(f"   PnL Realizing Actions: {', '.join(pnl_actions)}")

            logger.info(f"   Position Changes: {self.event_counts['position_updated']}")
            logger.info(f"   P&L Updates: {self.event_counts['position_pnl_update']}")
            if self._stale_executions_filtered > 0:
                logger.info(f"   Stale Executions Filtered: {self._stale_executions_filtered}")

            # Show confirmed position state (filtered for ghost reopens)
            if self._last_confirmed_position and self._last_confirmed_position.get('size', 0) != 0:
                pos = self._last_confirmed_position
                logger.info(f"   Confirmed Position: {pos['direction']} {pos['size']} @ {pos['avg_price']}")
            else:
                logger.info(f"   Confirmed Position: FLAT")

                # If we have a recent manual close, mention it
                if self._position_flat_timestamp:
                    elapsed = asyncio.get_event_loop().time() - self._position_flat_timestamp
                    if elapsed < 10:  # Only show recent closes
                        logger.info(f"   (Manually closed {elapsed:.1f}s ago)")

            # Show total realized PnL
            total_realized = await self._get_realized_pnl("any")
            if total_realized is not None:
                logger.info(f"   Total Realized PnL: ${total_realized:+.2f}")

            # Show risk rule stats if enabled
            if self.enable_risk_rules and self.rule_engine:
                rule_stats = self.rule_engine.get_stats()
                breaches = rule_stats['engine_stats']['breaches_detected']
                if breaches > 0:
                    logger.warning(f"   Risk Breaches: {breaches} rules triggered")

        else:
            logger.info("📊 SESSION SUMMARY | No events received yet")

    async def run_listener(self):
        """Run the event listener loop."""
        logger.info("🎯 Starting Event Listener - Real-time Diagnostic Mode")
        logger.info("=" * 70)
        logger.info("📋 INSTRUCTIONS:")
        logger.info("   1. Place trades manually in broker platform")
        logger.info("   2. Watch events appear here instantly")
        logger.info("   3. Press Ctrl+C to stop")
        logger.info("=" * 70)

        try:
            # Setup suite
            await self.setup_suite()

            # Initial status
            await self.log_connection_status()
            await self.log_event_summary()

            # Main listener loop
            logger.info("🎧 Listening for events... (Ctrl+C to stop)")

            while True:
                await asyncio.sleep(10)  # Check status every 10 seconds
                await self.log_connection_status()
                await self.log_event_summary()
                await self.log_risk_status()

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("\n🛑 Event listener stopped by user")

        except Exception as e:
            logger.error(f"❌ Event listener failed: {e}")
            raise

        finally:
            # Cleanup
            if self.suite:
                try:
                    logger.info(" Disconnecting...")
                    await self.suite.disconnect()
                except Exception as e:
                    logger.warning(f"Error during disconnect: {e}")

            # Final summary
            logger.info("\n🏁 FINAL EVENT SUMMARY")
            logger.info("=" * 50)
            logger.info(f"   Events Processed: {sum(self.event_counts.values())}")
            logger.info(f"   Trade Executions: {self.event_counts['order_filled']}")
            logger.info(f"   Position Changes: {self.event_counts['position_updated']}")
            logger.info(f"   P&L Updates: {self.event_counts['position_pnl_update']}")
            logger.info("✅ Event listener session complete")


async def main(enable_risk_rules: bool = True):
    """Run the event listener."""
    listener = EventListener(enable_risk_rules=enable_risk_rules)
    await listener.run_listener()


if __name__ == "__main__":
    import sys

    # Check for command line args
    enable_risk = "--no-risk" not in sys.argv

    if not enable_risk:
        logger.info("🛡️ Risk rules disabled via --no-risk flag")

    try:
        asyncio.run(main(enable_risk_rules=enable_risk))
    except KeyboardInterrupt:
        logger.info("\n👋 Event listener stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        # Keep terminal open on error
        input("\nPress Enter to exit...")
    else:
        # Keep terminal open after successful completion
        input("\n✅ Event listener completed. Press Enter to exit...")
