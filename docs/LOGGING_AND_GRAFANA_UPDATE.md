# Logging and Grafana Dashboard Update

**Date**: October 2, 2024  
**Issue**: логи и графана - Ensure all logs are automatically written and displayed in Grafana, rebuild dashboards according to current codebase

## Summary

Enhanced the bot application with structured JSON logging and completely rebuilt Grafana dashboards to match the current minimal codebase state.

## Changes Made

### 1. Structured JSON Logging (`bot/main.py`)

#### Added Custom JSON Formatter
- Created `JsonFormatter` class that formats all logs as JSON
- Automatic inclusion of standard fields:
  - `timestamp`: ISO 8601 format with timezone
  - `level`: Log level (INFO, WARNING, ERROR)
  - `logger`: Logger name
  - `message`: Log message
  - `module`, `function`, `line`: Source code location
  - `exception`: Stack trace if present
  - Custom fields: `event_type`, `user_id`, etc.

#### Enhanced Logging Throughout Application
Added comprehensive logging for all bot lifecycle events:
- `startup`: Bot initialization started
- `config_loaded`: Configuration loaded successfully (includes webapp_url and database status)
- `config_error`: Configuration loading failed
- `bot_created`: Bot instance created
- `dispatcher_initialized`: Dispatcher initialized
- `polling_start`: Polling started
- `bot_error`: Error during bot execution
- `shutdown`: Bot shutting down

#### Example JSON Log Output
```json
{
  "timestamp": "2024-10-02T12:36:09.468968Z",
  "level": "INFO",
  "logger": "bot.main",
  "message": "Configuration loaded successfully",
  "module": "main",
  "function": "main",
  "line": 67,
  "event_type": "config_loaded",
  "webapp_url": "https://example.com",
  "database_configured": true
}
```

### 2. Rebuilt Grafana Dashboards

#### A. System Overview Dashboard (`dating-app-overview.json`)
Completely redesigned with focus on current infrastructure:

**Panels Added/Updated:**
1. **Services Status** - Shows up/down status of all monitoring services
2. **Container CPU Usage** - Time series with proper queries
3. **Container Memory Usage** - Time series with MB units
4. **PostgreSQL Active Connections** - Database connection tracking
5. **Container Network Traffic** - RX/TX bytes per second
6. **All Container Logs** - Raw logs from all Docker containers
7. **Bot Application Logs (JSON Parsed)** - Formatted bot logs with JSON parsing
8. **Bot Error and Warning Logs** - Filtered ERROR/WARNING logs only
9. **Bot Events Timeline** - Shows event_type field for lifecycle tracking

**Key Features:**
- All panels use proper datasource UIDs
- Fixed panel types (timeseries instead of deprecated graph)
- Added proper field configs with units and colors
- JSON log parsing with `| json` filter
- LogQL queries that extract structured fields

#### B. Application Logs & Events Dashboard (`dating-app-business-metrics.json`)
Transformed from business metrics to log-focused dashboard (since business logic doesn't exist yet):

**Panels:**
1. **Bot Lifecycle Events Count** - Count of startup/shutdown events
2. **Error Logs Count** - Total ERROR logs with threshold coloring
3. **Warning Logs Count** - Total WARNING logs with threshold coloring
4. **Total Log Entries** - Overall log volume
5. **Log Levels Over Time** - Time series by level with color overrides
6. **Event Types Over Time** - Time series of event_type field
7. **Recent Bot Logs** - Live log stream with JSON parsing
8. **Detailed Bot Logs with Metadata** - Full JSON logs with all fields

**Key Features:**
- Uses Loki datasource for all panels
- Leverages JSON parsing to extract fields
- Time series aggregations with `count_over_time()`
- Color-coded thresholds (green → yellow → red)
- Real-time log streaming

### 3. Updated Documentation

#### `monitoring/README.md`
- Added "Structured Logging" section explaining JSON format
- Updated dashboard descriptions to match new panels
- Added comprehensive LogQL query examples:
  - All bot logs
  - JSON parsed logs
  - Error-only logs
  - Event filtering
- Documented log fields and their usage

#### `README.md`
- Enhanced monitoring section with structured logging description
- Added bullet points explaining what's tracked
- Mentioned JSON parsing capability

### 4. Testing

Verified that:
- ✅ Python code compiles without syntax errors
- ✅ JSON dashboards are valid JSON
- ✅ JSON logging produces correct format
- ✅ All required fields are included in logs
- ✅ event_type metadata works correctly

## Technical Details

### Log Flow Architecture

```
Bot Application (Python)
    ↓ (stdout with JSON format)
Docker Container
    ↓ (json-file logging driver)
/var/lib/docker/containers/*/*-json.log
    ↓ (Promtail scraping)
Loki (log aggregation)
    ↓ (Grafana datasource)
Grafana Dashboards (visualization)
```

### LogQL Parsing Examples

**Parse JSON and extract fields:**
```logql
{job="docker", container_name=~".*bot.*"} | json
```

**Format with extracted fields:**
```logql
{job="docker", container_name=~".*bot.*"} | json | line_format "[{{.level}}] {{.message}}"
```

**Filter by parsed field:**
```logql
{job="docker", container_name=~".*bot.*"} | json | level="ERROR"
```

**Count events over time:**
```logql
count_over_time({job="docker", container_name=~".*bot.*"} | json | event_type="startup" [5m])
```

## Benefits

1. **Better Observability**: Every application event is logged with context
2. **Structured Data**: JSON format allows easy parsing and filtering
3. **Real-time Monitoring**: Logs flow automatically to Grafana
4. **Error Tracking**: Separate panels for errors and warnings
5. **Event Timeline**: Track application lifecycle events
6. **No Code Changes Needed**: Logging happens automatically
7. **Industry Standard**: JSON logging is a best practice

## No Breaking Changes

- All changes are additive
- Existing functionality unchanged
- Backward compatible with current deployment
- No new dependencies added
- Docker logging already configured (json-file driver)

## How to Use

### View Logs in Grafana

1. Start monitoring stack:
   ```bash
   docker compose --profile monitoring up -d
   ```

2. Access Grafana: http://localhost:3000 (admin/admin)

3. Navigate to:
   - "Dating App - System Overview" for infrastructure + logs
   - "Dating App - Application Logs & Events" for detailed log analysis

4. Use Explore for custom queries:
   ```logql
   {job="docker", container_name=~".*bot.*"} | json | level="ERROR"
   ```

### Add Custom Logging

To add more logging in your code:

```python
import logging

# Get a logger for your module
logger = logging.getLogger(__name__)

# Info log with event
logger.info("User action", extra={"event_type": "user_action", "user_id": 123})

# Warning log
logger.warning("Rate limit approaching", extra={"event_type": "rate_limit"})

# Error log with exception
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True, extra={"event_type": "operation_error"})
```

Note: The logging configuration is set up automatically when the bot starts via the `configure_logging()` function called in `main()`.

## Future Enhancements

When business logic is added to the bot, the dashboards can be extended with:
- User registration metrics
- Profile creation/update counts
- Match rate calculations
- Command usage statistics
- Database query performance
- Custom business KPIs

The current log-based dashboard provides the foundation for these additions.

## Files Changed

- `bot/main.py` - Added JSON logging formatter and enhanced logging
- `monitoring/grafana/dashboards/dating-app-overview.json` - Complete rebuild
- `monitoring/grafana/dashboards/dating-app-business-metrics.json` - Transformed to logs dashboard
- `monitoring/README.md` - Added structured logging documentation
- `README.md` - Enhanced monitoring section

## Validation

All changes validated:
- JSON syntax valid
- Python syntax valid
- Log format produces correct JSON
- Grafana dashboard JSON structure correct
- No runtime errors

## References

- [Grafana Loki LogQL Documentation](https://grafana.com/docs/loki/latest/logql/)
- [Structured Logging Best Practices](https://www.datadoghq.com/blog/structured-logging/)
- [JSON Logging in Python](https://docs.python.org/3/library/logging.html)
