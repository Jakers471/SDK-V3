#!/usr/bin/env python3
"""
Demo script showing clean, readable logs for risk management system.
"""

import logging
import time

# Configure logging with timestamps - INFO level for clean readable logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)

def demo_clean_logs():
    """Demo the clean logging output."""
    print("="*70)
    print("🎯 CLEAN LOG DEMO - What You'll See With Risk Rules Active")
    print("="*70)

    # Simulate the clean logs you would see
    logger.info("🔗 Initializing TradingSuite for event listening...")
    time.sleep(0.1)

    logger.info("🔗 Registering risk rule event handlers...")
    logger.info("📡 Suite-level event handlers registered")
    logger.info("📡 Direct registration with MNQ PositionManager")
    logger.info("✅ Risk rules registered and monitoring live events")
    time.sleep(0.1)

    logger.info("✅ TradingSuite initialized and event handlers registered")
    logger.info("🛡️ Risk rules active: 1 rules loaded")
    logger.info("   📋 Rule loaded: {'rule_name': 'max_contracts', 'enabled': True, 'max_size': 2, 'severity': 'high', 'auto_flatten': False, 'breach_count': 0}")
    logger.info("🎧 Ready to receive real-time events from broker...")
    logger.info("🔗 WebSocket/SignalR: CONNECTED")
    time.sleep(0.1)

    # Simulate trade activity
    logger.info("📊 SESSION SUMMARY | Total Events: 1")
    logger.info("   Trade Types: Adjust:1")
    logger.info("   Position Changes: 0")
    logger.info("   P&L Updates: 0")
    logger.info("   Confirmed Position: FLAT")
    logger.info("🛡️ Risk monitoring active: 1 rules ready (waiting for events)")
    time.sleep(0.1)

    # Simulate a position opening
    logger.info("📈 TRADE_EXECUTED | 14:30:15.123")
    logger.info("   ID: 1643278084")
    logger.info("   Action: BUY (Market) - Open")
    logger.info("   Position: 0 → 5")
    logger.info("   Avg Price: $24738.75")
    logger.info("   Total Trades: 1")
    time.sleep(0.1)

    # Simulate risk rule evaluation
    logger.info("📏 Position size check: MNQ = 5 contracts")
    logger.info("⚖️ Risk rules evaluated: 1 rules checked, 1 breaches found")
    logger.info("🚨 RISK BREACHES DETECTED: 1 rules triggered")
    logger.info("   Rule: MaxContractsRule | Config: {'rule_name': 'max_contracts', 'enabled': True, 'max_size': 2, 'severity': 'high', 'auto_flatten': False, 'breach_count': 1}")
    time.sleep(0.1)

    # Simulate manual close
    logger.info("📉 MANUAL_POSITION_CLOSED | 14:30:20.456")
    logger.info("   Contract: MNQ")
    logger.info("   Final Size: 0 (confirmed flat)")
    logger.info("   Previous Position: LONG 5")
    logger.info("   Ignoring reopen events for 3.0s")
    time.sleep(0.1)

    # Simulate stale execution filtering
    logger.info("📜 STALE_EXECUTION_IGNORED | Order 1643278299 | 0.8s after manual close")
    logger.info("   This order fill is likely from before manual close - ignoring for position tracking")
    logger.info("   Confirmed position remains: FLAT")
    time.sleep(0.1)

    # Final summary
    logger.info("📊 SESSION SUMMARY | Total Events: 3")
    logger.info("   Trade Types: Open:1, Adjust:1")
    logger.info("   Position Changes: 1")
    logger.info("   Stale Executions Filtered: 1")
    logger.info("   Confirmed Position: FLAT")
    logger.info("   Risk Breaches: 1 rules triggered")

    print("\n" + "="*70)
    print("✅ LOGS ARE NOW CLEAN AND READABLE!")
    print("✅ No HTTP debug noise")
    print("✅ No SDK internal JSON logs")
    print("✅ Only important risk/trade events visible")
    print("✅ Manual closes clearly distinguished from stale executions")
    print("="*70)

if __name__ == "__main__":
    demo_clean_logs()
