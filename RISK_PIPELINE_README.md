# Risk Management Pipeline - Event Listener with Auto-Flatten

## Overview

This real-time event listener pipeline monitors live trading activity via WebSocket/SignalR connections and enforces risk management rules. When position sizes exceed configured limits, the system can automatically flatten breaching positions to prevent overexposure.

## Architecture

### Core Components

1. **Event Listener** (`event_listener.py`) - Real-time event processing
2. **Risk Rule Engine** (`rules/rule_engine.py`) - Rule evaluation and enforcement
3. **Max Contracts Rule** (`rules/max_contracts_rule.py`) - Position size enforcement
4. **Position Manager** - Executes position closure operations
5. **Trading Suite** - Orchestrates all trading operations

### Event Flow

```
Broker Events → Event Listener → Risk Rules → Auto-Flatten (if enabled) → Position Closure
     ↓              ↓              ↓              ↓              ↓
ORDER_FILLED   Logging      Breach Check    PositionManager   Market Order
POSITION_UPDATE Trade Analysis Rule Evaluation .close_position_direct()
POSITION_PNL_UPDATE Risk Alerts   Auto-Close Trigger
```

## Critical Bug Fix: Auto-Flatten API Calls

### The Error

**Date:** September 25, 2025

**Error Message:**
```
'ProjectX' object has no attribute 'close_contract'
'ProjectX' object has no attribute 'close_position_direct'
```

**Root Cause:**
The risk management system was attempting to call position closure methods directly on the ProjectX API client object, but these methods don't exist on the client. The correct methods exist on the PositionManager within the TradingSuite.

### The Fix

**Before (Broken):**
```python
# ❌ WRONG - Methods don't exist on API client
result = await api_client.close_contract(account_id, contract_id)
result = await api_client.close_position_direct(contract_id, account_id)
```

**After (Fixed):**
```python
# ✅ CORRECT - Use PositionManager methods via TradingSuite
result = await trading_suite["MNQ"].positions.close_position_direct(contract_id)
```

**Files Modified:**
- `event_listener.py` - Pass TradingSuite instead of API client to RiskEventHandler
- `rules/rule_engine.py` - Updated RiskEventHandler to use PositionManager methods
- `rules/max_contracts_rule.py` - Updated to use TradingSuite for position operations

## Enums Used (Start to Finish)

### Core Trading Enums

#### OrderSide (IntEnum)
```python
class OrderSide(IntEnum):
    BUY = 0      # Buy order/long position
    SELL = 1     # Sell order/short position
```

#### OrderType (IntEnum)
```python
class OrderType(IntEnum):
    LIMIT = 1           # Limit price order
    MARKET = 2          # Market price order
    STOP_LIMIT = 3      # Stop limit order
    STOP = 4           # Stop order
    TRAILING_STOP = 5   # Trailing stop order
    JOIN_BID = 6       # Join best bid
    JOIN_ASK = 7       # Join best ask
```

#### OrderStatus (IntEnum)
```python
class OrderStatus(IntEnum):
    NONE = 0       # Uninitialized
    OPEN = 1       # Active in market
    FILLED = 2     # Completely executed
    CANCELLED = 3  # Cancelled by user/broker
    EXPIRED = 4    # Expired
    REJECTED = 5   # Rejected by broker
    PENDING = 6    # Pending submission
```

#### PositionType (IntEnum)
```python
class PositionType(IntEnum):
    UNDEFINED = 0  # No position
    LONG = 1       # Long position (bought)
    SHORT = 2      # Short position (sold)
```

### Event System Enums

#### EventType (Enum)
```python
class EventType(Enum):
    ORDER_FILLED = "order_filled"           # Order execution event
    POSITION_UPDATED = "position_updated"   # Position change event
    POSITION_PNL_UPDATE = "position_pnl_update"  # P&L update event
    POSITION_CLOSED = "position_closed"     # Position closure event
```

## Risk Configuration

### Configuration File: `config/risk_config.json`

```json
{
  "rules": {
    "max_contracts": {
      "enabled": true,
      "max_size": 2,
      "severity": "high",
      "auto_flatten": true
    }
  },
  "global": {
    "log_level": "INFO",
    "dry_run": true
  }
}
```

### Configuration Parameters

#### Max Contracts Rule
- `enabled` (bool): Enable/disable the rule
- `max_size` (int): Maximum contracts allowed per position
- `severity` (str): "high" or "medium" - affects alert emojis
- `auto_flatten` (bool): Automatically close breaching positions

#### Global Settings
- `log_level` (str): Logging verbosity
- `dry_run` (bool): Test mode (doesn't execute real trades)

## Risk Rule Logic

### Breach Detection Flow

1. **Event Reception**: Event listener receives position/order events
2. **Data Extraction**: Parse contract_id, account_id, position size from event
3. **Rule Evaluation**: Check if `abs(position_size) > max_size`
4. **Breach Handling**:
   - Log breach with severity emoji 🚨/⚠️
   - If `auto_flatten=true`: Call PositionManager.close_position_direct()
   - Update breach statistics

### Auto-Flatten Process

```python
# When breach detected and auto_flatten enabled:
contract_id = position_data['contract_id']
result = await trading_suite["MNQ"].positions.close_position_direct(contract_id)

if result.get('success'):
    logger.info(f"✅ Auto-flattened breaching position: {contract_id}")
```

## Usage

### Running the Event Listener

**On Windows** (recommended to keep terminal open):
```cmd
# Use the batch file (keeps terminal open)
run_event_listener.bat

# Or use PowerShell script
powershell -ExecutionPolicy Bypass -File run_event_listener.ps1
```

**On Linux/Mac**:
```bash
# With risk rules enabled (default)
python event_listener.py

# Disable risk rules
python event_listener.py --no-risk
```

**Note**: The script now includes a pause at the end to keep the terminal open so you can read the output. Press Enter to exit when done.

### Manual Testing

```bash
# Run risk rule tests
python -c "from rules.rule_engine import RuleEngine; import asyncio; async def test(): r = RuleEngine('config/risk_config.json'); await r.initialize(); print('✅ RuleEngine ready'); asyncio.run(test())"
```

### Diagnostic Systems

#### **Execution Flow Tracer** (Shows WHERE risk rules go)
For understanding the exact execution path of your risk rules:

**Windows:**
```cmd
# See exactly where risk rules execute and how hooks fire
run_execution_tracer.bat

# Or run Python version directly
python execution_flow_tracer.py
```

**📖 Detailed Documentation:** See `EXECUTION_FLOW_TRACER_README.md` for complete usage guide.

**What it shows:**
```
🎯 Event fires (POSITION_UPDATED)
🛡️ Risk rule evaluates position size
🚨 Breach detected (size > limit)
🪝 Hook executes (on_breach)
🔌 API call made (close_position_direct)
✅ Flow completes with result
```

**Key Features:**
- **Complete execution path** from event to API
- **Hook execution timing** and data flow
- **API call tracing** with parameters and results
- **Performance monitoring** for 32+ rules
- **Error isolation** and recovery

#### **Live Diagnostic System** (Shows real-time event traces)
For debugging with actual trading:

**Windows:**
```cmd
# Run diagnostic system (shows full event trace)
run_diagnostic.bat

# Or run Python version directly
python diagnostic_risk_monitor.py
```

**What the diagnostic shows:**
- 🎯 **Events Fired**: Which event enums trigger (POSITION_UPDATED, ORDER_FILLED, etc.)
- 📦 **Payloads**: What data is passed with each event (breach details, position sizes, symbols)
- 🪝 **Hooks Triggered**: Which risk hooks fire (on_breach, on_trade_executed, etc.)
- 🔌 **API Calls**: Which broker API methods are called (close_position_direct, place_order, etc.)

**Example Output:**
```
🎯 EVENT FIRED [14:30:25.123]: POSITION_UPDATED (EventType.POSITION_UPDATED)
   📦 PAYLOAD:
     contract_id: CON.F.US.MNQ.Z25
     size: 5
     type: 1

🛡️ RULE EVAL [14:30:25.124]: MaxContractsRule
   📋 EVALUATION:
     rule: max_contracts
     breach_detected: true
     severity: high

🪝 HOOK FIRED [14:30:25.125]: on_breach
   📊 DATA:
     breach: {rule_name: max_contracts, current_size: 5, max_size: 2}
     contract_id: CON.F.US.MNQ.Z25

🔌 API CALL [14:30:25.126]: close_position_direct
   ⚙️ PARAMETERS:
     contract_id: CON.F.US.MNQ.Z25
     account_id: DEMO123
```

## Logging and Monitoring

### Log Levels
- **INFO**: Normal operations, trade executions, status updates
- **WARNING**: Risk breaches, connection issues
- **ERROR**: API failures, auto-flatten errors

### Key Log Messages

```
🔗 Initializing TradingSuite for event listening...
🛡️ Risk rules active: 1 rules loaded
🎧 Ready to receive real-time events from broker...
📈 TRADE_EXECUTED | 14:30:25.123
📏 Position size check: CON.F.US.MNQ.Z25 = 10 contracts
🚨 MAX_CONTRACTS_BREACH [Rule: 2 max] | Size: 10 > 2
🔄 AUTO-FLATTENING breach position: CON.F.US.MNQ.Z25
✅ Auto-flattened breaching position: CON.F.US.MNQ.Z25
```

### Event Summary
The system provides comprehensive session summaries:
- Total events processed
- Trade action breakdown (Open, Add, Reduce, Close, Flip)
- Position state tracking
- Risk breach counts
- Realized P&L tracking

## Error Handling

### Graceful Degradation
- If risk rules fail to initialize: continues with logging only
- If auto-flatten fails: logs error but doesn't crash the listener
- If position data extraction fails: skips risk checks for that event

### Connection Resilience
- Monitors WebSocket/SignalR connection status
- Automatic reconnection handling
- Stale execution filtering (ignores old fills after manual closes)

## Testing

### Unit Tests
- `MaxContractsRule.test_max_contracts_rule()` - Validates breach detection
- `RuleEngine.test_rule_engine()` - Tests full rule processing pipeline

### Integration Testing
- Manual trading with broker platform while listener runs
- Verify auto-flatten triggers on position limit breaches
- Confirm position closure executes market orders correctly

## Security Considerations

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Enable pre-commit hooks for security scanning
- Dry-run mode available for testing without real trades

## Future Enhancements

- Additional risk rules (daily P&L limits, drawdown limits, etc.)
- Configurable position sizing strategies
- Email/SMS alerts for critical breaches
- Historical breach analytics and reporting
- Multi-instrument position aggregation rules
