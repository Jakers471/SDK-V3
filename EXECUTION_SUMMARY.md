# 🎯 Risk Rule Execution Summary

## Where Risk Rules "Go" - The Complete Path

| Step | Component | Method | What Happens |
|------|-----------|--------|--------------|
| 1 | **Event** | `POSITION_UPDATED` | Broker sends position update event |
| 2 | **Risk Rule** | `MaxContractsRule.check()` | Rule evaluates position size vs limit |
| 3 | **Decision** | `size > max_size` | Breach detected if size exceeds limit |
| 4 | **Handler** | `_handle_breach()` | Breach logging and action preparation |
| 5 | **Hook** | `on_breach` | Custom alert/notification hooks fire |
| 6 | **Auto-Close** | `_auto_flatten()` | Position closure initiated |
| 7 | **API Call** | `close_position_direct()` | Broker API executes position close |
| 8 | **Result** | API Response | Success/failure returned |
| 9 | **Completion** | `auto_flatten_complete` | Final status hook fires |

## Hook Execution Points

### `on_breach` - Breach Detection
```python
# Fires when: Risk rule detects violation
# Location: MaxContractsRule._handle_breach()
# Data: breach details, contract info, rule config
# Uses: Send alerts, log events, trigger notifications
```

### `auto_flatten_start` - Pre-Closure
```python
# Fires when: Auto-flatten begins
# Location: MaxContractsRule._auto_flatten()
# Data: contract_id, action details
# Uses: Pre-close validation, audit logging
```

### `auto_flatten_complete` - Post-Closure
```python
# Fires when: Auto-flatten finishes
# Location: MaxContractsRule._auto_flatten()
# Data: success/failure status, final state
# Uses: Success confirmations, error handling
```

## API Execution Sequence

```
Event → Rule Check → Breach → Hook → API Call → Result → Completion Hook
```

**Available API Methods:**
- `close_position_direct()` - Immediate market close
- `place_order()` - Submit orders
- `get_positions()` - Position queries
- `cancel_order()` - Order cancellation

## Performance for 32 Rules

- **Evaluation Time:** ~0.005s per rule
- **Total Flow:** ~0.200s for 32 rules
- **Hook Execution:** Concurrent (all hooks fire simultaneously)
- **API Calls:** 0.050-0.200s (network dependent)

## Key Files

- `execution_flow_tracer.py` - Complete execution tracing
- `EXECUTION_FLOW_TRACER_README.md` - Detailed documentation
- `RISK_RULE_EXECUTION_PATH.txt` - Visual execution path
- `run_execution_tracer.bat` - Windows launcher

## Run It

```cmd
run_execution_tracer.bat
```

See **exactly** where your risk rules go and how hooks execute! 🎯
