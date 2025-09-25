#!/usr/bin/env python3
"""Quick test of risk rules initialization."""
import asyncio
from rules.rule_engine import RuleEngine

async def test():
    try:
        engine = RuleEngine("config/risk_config.json")
        await engine.initialize()
        print("✅ RuleEngine initialized successfully")
        stats = engine.get_stats()
        print(f"   Rules loaded: {stats['config_summary']['rules_enabled']}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RuleEngine: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
