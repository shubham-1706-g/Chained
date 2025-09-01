# Troubleshooting Guide for FlowForge Python API

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the FlowForge Python API. Whether you're facing installation problems, runtime errors, or performance issues, this guide provides step-by-step solutions.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Installation Issues](#installation-issues)
3. [Startup Problems](#startup-problems)
4. [API Errors](#api-errors)
5. [Workflow Execution Issues](#workflow-execution-issues)
6. [Performance Problems](#performance-problems)
7. [Integration Issues](#integration-issues)
8. [Security & Authentication](#security--authentication)
9. [Monitoring & Debugging](#monitoring--debugging)
10. [Database Issues](#database-issues)
11. [External Service Problems](#external-service-problems)
12. [Frequently Asked Questions](#frequently-asked-questions)

## Quick Diagnosis

### System Health Check

Run these commands to quickly assess system health:

```bash
# Check if FlowForge is running
curl -f http://localhost:8000/health || echo "FlowForge is not responding"

# Check detailed health status
curl -s http://localhost:8000/health/detailed | jq .

# Check system resources
echo "=== CPU Usage ==="
top -bn1 | head -10

echo "=== Memory Usage ==="
free -h

echo "=== Disk Usage ==="
df -h

echo "=== Network Connections ==="
netstat -tlnp | grep :8000
```

### Log Analysis

Check recent logs for errors:

```bash
# View recent application logs
tail -f /var/log/flowforge/api.log

# Search for specific errors
grep -i error /var/log/flowforge/api.log | tail -20

# Check systemd service status
sudo systemctl status flowforge-api

# View systemd logs
sudo journalctl -u flowforge-api -f
```

### Configuration Validation

Validate your configuration:

```bash
# Check environment variables
env | grep -E "(FLOWFORGE|DATABASE|REDIS)"

# Validate configuration file
python -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
print('Configuration loaded successfully')
print(f'API Key configured: {bool(config.get(\"api_key\"))}')
print(f'Database URL configured: {bool(config.get(\"database\", {}).get(\"url\"))}')
"
```

## Installation Issues

### Python Version Compatibility

**Problem**: `ModuleNotFoundError` or import errors

**Solutions**:

```bash
# Check Python version
python --version
python3 --version

# Ensure Python 3.8+
python3 -c "import sys; print(f'Python version: {sys.version}'); assert sys.version_info >= (3, 8)"

# Install with compatible pip
python3 -m pip install --upgrade pip

# Check virtual environment
which python
which pip

# Recreate virtual environment if needed
deactivate 2>/dev/null || true
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependency Installation Failures

**Problem**: Pip install fails with compilation errors

**Solutions**:

```bash
# For Rust compilation issues (Windows)
pip install -r requirements-no-rust.txt

# For general compilation issues
export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"
pip install --no-cache-dir -r requirements.txt

# Install system dependencies
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential python3-dev libssl-dev libffi-dev

# macOS
brew install openssl
export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install -y python3-devel openssl-devel libffi-devel
```

### Virtual Environment Issues

**Problem**: Virtual environment not working properly

**Solutions**:

```bash
# Check if virtual environment is activated
echo $VIRTUAL_ENV
echo $PATH

# Proper activation
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Check Python path
which python
python -c "import sys; print(sys.path)"

# Reinstall packages in virtual environment
pip install --force-reinstall -r requirements.txt

# Check for conflicting packages
pip list | grep -E "(fastapi|uvicorn|pydantic)"
```

## Startup Problems

### Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Solutions**:

```bash
# Find process using port 8000
lsof -i :8000
netstat -tlnp | grep :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --host 0.0.0.0 --port 8001

# Check for multiple instances
ps aux | grep uvicorn
```

### Database Connection Failures

**Problem**: Database connection errors on startup

**Solutions**:

```bash
# Test database connection
python -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://user:pass@localhost/flowforge')
        await conn.close()
        print('Database connection successful')
    except Exception as e:
        print(f'Database connection failed: {e}')

asyncio.run(test_db())
"

# Check database service status
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Check connection string format
# Correct: postgresql://user:password@host:port/database
# Wrong: postgresql://user:password@host/database  # Missing port

# Test with database CLI
psql -h localhost -U flowforge_user -d flowforge -c "SELECT 1;"
```

### Redis Connection Issues

**Problem**: Redis connection errors

**Solutions**:

```bash
# Test Redis connection
redis-cli ping

# Check Redis service status
sudo systemctl status redis-server
sudo systemctl restart redis-server

# Check Redis configuration
redis-cli config get maxmemory
redis-cli config get maxmemory-policy

# Test Python Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print('Redis ping:', r.ping())
"
```

### Configuration File Errors

**Problem**: Invalid configuration causing startup failure

**Solutions**:

```python
# Validate JSON configuration
python -c "
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    print('Configuration is valid JSON')
    print('Required fields present:')
    print(f'  - api_key: {bool(config.get(\"api_key\"))}')
    print(f'  - database: {bool(config.get(\"database\"))}')
except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}')
except FileNotFoundError:
    print('Configuration file not found')
"

# Check for environment variable conflicts
env | grep -i flowforge

# Validate with schema
python -c "
from pydantic import BaseModel, ValidationError
import json

class ConfigSchema(BaseModel):
    api_key: str
    database: dict
    redis: dict = {}

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    validated = ConfigSchema(**config)
    print('Configuration schema is valid')
except ValidationError as e:
    print(f'Configuration validation error: {e}')
"
```

## API Errors

### 401 Unauthorized

**Problem**: Authentication failures

**Solutions**:

```bash
# Check API key format
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/health

# Verify API key in configuration
grep "api_key" config.json

# Check for extra spaces or characters
echo "YOUR_API_KEY" | od -c

# Test with different API key
curl -H "Authorization: Bearer test-key-123" http://localhost:8000/health
```

### 422 Unprocessable Entity

**Problem**: Invalid request data

**Solutions**:

```python
# Validate request payload
import json
from pydantic import BaseModel, ValidationError

class ActionRequest(BaseModel):
    action_type: str
    config: dict
    input_data: dict = {}

# Test validation
test_payload = {
    "action_type": "http",
    "config": {"method": "GET", "url": "https://api.example.com"},
    "input_data": {"param": "value"}
}

try:
    validated = ActionRequest(**test_payload)
    print("Request payload is valid")
except ValidationError as e:
    print(f"Validation error: {e}")

# Check for malformed JSON
echo '{"test": "data"}' | python -m json.tool
```

### 429 Too Many Requests

**Problem**: Rate limit exceeded

**Solutions**:

```bash
# Check current rate limit status
curl -v http://localhost:8000/api/v1/actions/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"action_type": "http", "config": {"method": "GET", "url": "https://httpbin.org/get"}}' \
  2>&1 | grep -i "x-rate"

# Wait for rate limit reset
sleep 60

# Check rate limit headers
curl -I http://localhost:8000/health
```

### 500 Internal Server Error

**Problem**: Server-side errors

**Solutions**:

```bash
# Check application logs
tail -f /var/log/flowforge/api.log

# Enable debug logging temporarily
export LOG_LEVEL=DEBUG
python main.py

# Check system resources
top -b -n1 | head -20

# Test individual components
python -c "
from app.core.engine import WorkflowEngine
engine = WorkflowEngine()
print('Workflow engine initialized successfully')
"

# Check database connectivity
python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    result = await conn.fetchval('SELECT 1')
    print(f'Database test: {result}')
    await conn.close()

asyncio.run(test())
"
```

## Workflow Execution Issues

### Workflow Validation Errors

**Problem**: Invalid workflow definition

**Solutions**:

```python
# Validate workflow structure
python -c "
import json
from typing import List, Dict, Any

def validate_workflow(workflow: dict) -> List[str]:
    errors = []
    
    # Check required fields
    if 'nodes' not in workflow:
        errors.append('Missing required field: nodes')
    if 'connections' not in workflow:
        errors.append('Missing required field: connections')
    
    # Validate nodes
    for i, node in enumerate(workflow.get('nodes', [])):
        if 'id' not in node:
            errors.append(f'Node {i}: Missing required field: id')
        if 'type' not in node:
            errors.append(f'Node {i}: Missing required field: type')
        if node.get('type') not in ['trigger', 'action', 'operation']:
            errors.append(f'Node {i}: Invalid type: {node.get(\"type\")}')
    
    # Validate connections
    nodes_ids = {node['id'] for node in workflow.get('nodes', [])}
    for i, conn in enumerate(workflow.get('connections', [])):
        if conn.get('from') not in nodes_ids:
            errors.append(f'Connection {i}: Source node not found: {conn.get(\"from\")}')
        if conn.get('to') not in nodes_ids:
            errors.append(f'Connection {i}: Target node not found: {conn.get(\"to\")}')
    
    return errors

# Test validation
with open('workflow.json', 'r') as f:
    workflow = json.load(f)

errors = validate_workflow(workflow)
if errors:
    print('Validation errors:')
    for error in errors:
        print(f'  - {error}')
else:
    print('Workflow is valid')
"
```

### Action Execution Failures

**Problem**: Actions failing to execute

**Solutions**:

```python
# Test action in isolation
from app.actions.http.request import HTTPAction
import asyncio

async def test_action():
    config = {
        "method": "GET",
        "url": "https://httpbin.org/json",
        "timeout": 30
    }
    
    action = HTTPAction(config)
    
    # Test configuration validation
    is_valid = action.validate_config()
    print(f'Configuration valid: {is_valid}')
    
    if is_valid:
        # Test action execution
        result = await action.execute({}, None)
        print(f'Action result: {result}')

asyncio.run(test_action())

# Test with mock data
import unittest.mock as mock

async def test_action_with_mock():
    with mock.patch('aiohttp.ClientSession') as mock_session:
        # Mock successful response
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {'success': True}
        
        mock_session.return_value.__aenter__.return_value.request.return_value = mock_response
        
        config = {"method": "GET", "url": "https://api.example.com"}
        action = HTTPAction(config)
        result = await action.execute({}, None)
        
        print(f'Mock test result: {result}')

asyncio.run(test_action_with_mock())
```

### Trigger Activation Issues

**Problem**: Triggers not firing

**Solutions**:

```python
# Test webhook trigger
curl -X POST http://localhost:8000/webhooks/test-webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"key": "value"}}'

# Check webhook logs
grep webhook /var/log/flowforge/api.log

# Test schedule trigger
python -c "
from app.triggers.schedule import ScheduleTrigger
import asyncio

async def test_schedule():
    config = {
        'schedule_type': 'cron',
        'cron_expression': '*/5 * * * *',  # Every 5 minutes
        'timezone': 'UTC'
    }
    
    trigger = ScheduleTrigger(config)
    await trigger.setup()
    
    # Check next execution time
    next_time = trigger._get_next_execution_time()
    print(f'Next execution: {next_time}')

asyncio.run(test_schedule())
"

# Test file watch trigger
python -c "
from app.triggers.file_watch import FileWatchTrigger
import tempfile
import os

config = {
    'watch_path': '/tmp',
    'file_pattern': '*.txt',
    'watch_events': ['created']
}

trigger = FileWatchTrigger(config)
is_valid = trigger._validate_config()
print(f'File watch config valid: {is_valid}')
"
```

## Performance Problems

### High Memory Usage

**Problem**: Application consuming too much memory

**Solutions**:

```bash
# Monitor memory usage
ps aux --sort=-%mem | head -10

# Check for memory leaks
python -c "
import tracemalloc
tracemalloc.start()

# Your code here
import gc
gc.collect()

current, peak = tracemalloc.get_traced_memory()
print(f'Current memory usage: {current / 1024 / 1024:.2f} MB')
print(f'Peak memory usage: {peak / 1024 / 1024:.2f} MB')
"

# Check connection pool sizes
python -c "
import asyncpg
import asyncio

async def check_pools():
    # Check PostgreSQL connection pool
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    result = await conn.fetchval('SELECT count(*) FROM pg_stat_activity')
    print(f'Active PostgreSQL connections: {result}')
    await conn.close()

asyncio.run(check_pools())
"

# Optimize Gunicorn configuration
# gunicorn.conf.py
workers = 2  # Reduce from default
worker_connections = 100  # Reduce from default
max_requests = 1000  # Restart worker after 1000 requests
max_requests_jitter = 50
```

### Slow Response Times

**Problem**: API responses are slow

**Solutions**:

```bash
# Profile application performance
python -c "
import cProfile
import main

cProfile.run('main.app', 'profile_output.prof')
"

# Analyze profile data
python -c "
import pstats
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative').print_stats(20)
"

# Check database query performance
python -c "
import asyncpg
import asyncio
import time

async def benchmark_query():
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    
    start_time = time.time()
    result = await conn.fetch('SELECT * FROM executions LIMIT 1000')
    end_time = time.time()
    
    print(f'Query took: {end_time - start_time:.3f} seconds')
    print(f'Results: {len(result)}')
    
    await conn.close()

asyncio.run(benchmark_query())
"

# Add database indexes
# SQL commands to add indexes
CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_created_at ON executions(created_at);
```

### High CPU Usage

**Problem**: Application consuming too much CPU

**Solutions**:

```bash
# Profile CPU usage
python -c "
import cProfile
import main

# Run with profiling
cProfile.run('main.app', 'cpu_profile.prof')

# Analyze results
import pstats
p = pstats.Stats('cpu_profile.prof')
p.sort_stats('time').print_stats(20)
"

# Check for infinite loops or recursive calls
# Add timeout to long-running operations
import asyncio

async def timeout_example():
    try:
        result = await asyncio.wait_for(
            long_running_operation(),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        print("Operation timed out")
        return None
```

## Integration Issues

### External API Timeouts

**Problem**: External API calls timing out

**Solutions**:

```python
# Test external API connectivity
curl -w "@curl-format.txt" -o /dev/null -s "https://api.external.com/endpoint"

# curl-format.txt
     time_namelookup:  %{time_namelookup}\\n
        time_connect:  %{time_connect}\\n
     time_appconnect:  %{time_appconnect}\\n
    time_pretransfer:  %{time_pretransfer}\\n
       time_redirect:  %{time_redirect}\\n
  time_starttransfer:  %{time_starttransfer}\\n
                     ----------\\n
          time_total:  %{time_total}\\n

# Implement retry logic with exponential backoff
import asyncio
import random

async def call_with_retry(url, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            # Make API call
            response = await make_api_call(url)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s")
            await asyncio.sleep(delay)

# Configure appropriate timeouts
action_config = {
    "method": "GET",
    "url": "https://api.external.com/data",
    "timeout": 30,  # Increase timeout
    "retry_count": 3,
    "retry_delay": 2
}
```

### Webhook Delivery Issues

**Problem**: Webhooks not being delivered or processed

**Solutions**:

```bash
# Test webhook endpoint manually
curl -X POST http://localhost:8000/webhooks/your-webhook-id \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=your-signature" \
  -d '{"event": "test", "data": {"key": "value"}}'

# Check webhook signature verification
python -c "
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(f'sha256={expected}', signature)

payload = '{\"event\": \"test\"}'
signature = 'sha256=abc123...'
secret = 'your-webhook-secret'

is_valid = verify_signature(payload, signature, secret)
print(f'Signature valid: {is_valid}')
"

# Check webhook logs
grep webhook /var/log/flowforge/api.log | tail -20

# Test webhook retry mechanism
# Configure webhook with retry settings
webhook_config = {
    "webhook_id": "test-webhook",
    "secret": "webhook-secret",
    "retry_count": 3,
    "retry_delay": 5,
    "timeout": 30
}
```

### Database Connection Pool Issues

**Problem**: Database connection pool exhausted

**Solutions**:

```python
# Monitor connection pool status
python -c "
import asyncpg
import asyncio

async def check_pool_status():
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    
    # Check active connections
    result = await conn.fetch('''
        SELECT count(*) as active_connections
        FROM pg_stat_activity 
        WHERE datname = 'flowforge'
    ''')
    
    print(f'Active connections: {result[0][\"active_connections\"]}')
    
    # Check connection pool settings
    pool_result = await conn.fetch('''
        SELECT name, setting
        FROM pg_settings 
        WHERE name LIKE '%connection%'
    ''')
    
    for row in pool_result:
        print(f'{row[\"name\"]}: {row[\"setting\"]}')
    
    await conn.close()

asyncio.run(check_pool_status())
"

# Optimize connection pool settings
# config.py
DATABASE_CONFIG = {
    'min_size': 5,
    'max_size': 20,
    'max_queries': 50000,
    'max_inactive_connection_lifetime': 300.0,
    'command_timeout': 60.0
}

# Monitor slow queries
# PostgreSQL configuration
# postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = 'all'
pg_stat_statements.max = 10000

# Query slow queries
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## Security & Authentication

### API Key Issues

**Problem**: API key authentication failing

**Solutions**:

```bash
# Test API key authentication
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/health

# Check API key format and length
echo "YOUR_API_KEY" | wc -c

# Verify API key in database/logs
# Check if API key exists and is active
python -c "
import os
api_key = os.getenv('FLOWFORGE_API_KEY')
print(f'API key configured: {bool(api_key)}')
print(f'API key length: {len(api_key) if api_key else 0}')
"

# Rotate API key if compromised
python -c "
import secrets
new_api_key = secrets.token_urlsafe(32)
print(f'New API key: {new_api_key}')
# Update configuration and restart service
"
```

### SSL/TLS Certificate Issues

**Problem**: SSL certificate validation errors

**Solutions**:

```bash
# Test SSL certificate
openssl s_client -connect api.flowforge.com:443 -servername api.flowforge.com

# Check certificate expiration
echo | openssl s_client -connect api.flowforge.com:443 2>/dev/null | openssl x509 -noout -dates

# Disable SSL verification for testing (NOT for production)
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Update certificate store
sudo update-ca-certificates
```

## Monitoring & Debugging

### Enable Debug Logging

```python
# Enable debug logging temporarily
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG

# Check current log level
python -c "import logging; print(logging.getLogger().level)"

# Log to file with rotation
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'debug.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
handler.setLevel(logging.DEBUG)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

### Trace Request Flow

```python
# Add request tracing middleware
from fastapi import Request, Response
import time
import uuid

@app.middleware("http")
async def trace_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    
    # Add request ID to logger context
    logger = logging.getLogger()
    logger.request_id = request_id
    
    start_time = time.time()
    
    logger.info(f"Request started: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Request completed: {response.status_code} in {process_time:.3f}s")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed after {process_time:.3f}s: {e}")
        raise
```

### Memory Profiling

```python
# Profile memory usage
import tracemalloc
import gc

def profile_memory():
    tracemalloc.start()
    
    # Your code here
    # ...
    
    # Get memory statistics
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
    
    # Get top memory consumers
    stats = tracemalloc.take_snapshot().statistics('lineno')
    for stat in stats[:10]:
        print(f"{stat.size / 1024 / 1024:.2f} MB - {stat.traceback.format()[-1]}")

# Force garbage collection
gc.collect()

# Profile specific function
@profile
def my_function():
    # Function code here
    pass
```

### Performance Profiling

```python
# Profile function performance
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            return func(*args, **kwargs)
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(20)
    
    return wrapper

# Use decorator
@profile_function
def slow_function():
    # Function that might be slow
    pass

# Or profile entire application
if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.prof')
    
    # Analyze results
    stats = pstats.Stats('profile_output.prof')
    stats.sort_stats('cumulative').print_stats(20)
```

## Database Issues

### Connection Pool Exhaustion

```sql
-- Check active connections
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'flowforge';

-- Check connection pool settings
SHOW max_connections;
SHOW shared_preload_libraries;

-- Monitor connection states
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;
```

### Slow Queries

```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check query execution plan
EXPLAIN ANALYZE
SELECT * FROM executions
WHERE workflow_id = 'some-workflow-id'
ORDER BY created_at DESC
LIMIT 100;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX CONCURRENTLY idx_executions_status ON executions(status);
CREATE INDEX CONCURRENTLY idx_executions_created_at ON executions(created_at);
```

### Database Migration Issues

```bash
# Check migration status
alembic current

# Check pending migrations
alembic heads

# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Downgrade if needed
alembic downgrade -1
```

## External Service Problems

### API Rate Limiting

**Problem**: External API rate limits being exceeded

**Solutions**:

```python
# Implement rate limiting for external APIs
import time
from collections import defaultdict

class APIRateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def can_make_request(self, api_name):
        now = time.time()
        # Remove old requests
        self.requests[api_name] = [
            req_time for req_time in self.requests[api_name]
            if now - req_time < 60
        ]
        
        if len(self.requests[api_name]) < self.requests_per_minute:
            self.requests[api_name].append(now)
            return True
        return False

# Usage
rate_limiter = APIRateLimiter(requests_per_minute=30)

async def call_external_api(api_name, url):
    if not rate_limiter.can_make_request(api_name):
        raise Exception(f"Rate limit exceeded for {api_name}")
    
    # Make API call
    response = await make_http_request(url)
    return response
```

### Service Unavailability

**Problem**: External services are down or unreachable

**Solutions**:

```python
# Implement circuit breaker pattern
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'half-open':
                self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
    
    def _reset(self):
        self.failure_count = 0
        self.state = 'closed'

# Usage
circuit_breaker = CircuitBreaker()

async def call_external_service():
    async def make_request():
        return await aiohttp.ClientSession().get('https://api.external.com')
    
    return await circuit_breaker.call(make_request)
```

## Frequently Asked Questions

### General Questions

**Q: What's the difference between actions and triggers?**

A: Actions perform operations (like sending emails or calling APIs), while triggers start workflow execution based on events (like webhooks or schedules).

**Q: How do I handle errors in workflows?**

A: Use error handling nodes, implement retry logic in actions, and set up proper monitoring and alerting.

**Q: Can I run workflows in parallel?**

A: Yes, independent nodes can execute in parallel. Configure `max_parallel_nodes` in your workflow settings.

**Q: How do I monitor workflow performance?**

A: Use the `/health/detailed` endpoint, check logs, and monitor metrics like execution time and success rate.

### Technical Questions

**Q: Why is my workflow slow?**

A: Check database queries, external API calls, and resource usage. Consider adding indexes and optimizing connection pools.

**Q: How do I debug workflow execution?**

A: Enable debug logging, check execution status, and use the monitoring endpoints to trace execution flow.

**Q: Can I modify workflows while they're running?**

A: No, running workflows use the definition that was active when they started. Changes only affect new executions.

**Q: How do I handle large data in workflows?**

A: Use data transformation actions to filter and aggregate data. Consider pagination for large datasets.

### Integration Questions

**Q: How do I integrate with my existing systems?**

A: Use HTTP actions for REST APIs, webhooks for event-driven integration, and data transformation for format conversion.

**Q: Can I use custom actions?**

A: Yes, implement the `BaseAction` interface and register your custom action with the plugin system.

**Q: How do I handle authentication for external APIs?**

A: Store API keys securely in environment variables or configuration files. Use the appropriate authentication headers in HTTP actions.

### Performance Questions

**Q: What's the maximum workflow size?**

A: Limited by available memory and database constraints. Typically 100-500 nodes depending on complexity.

**Q: How many concurrent workflows can I run?**

A: Depends on system resources and workflow complexity. Monitor CPU, memory, and database connections.

**Q: Can I prioritize certain workflows?**

A: Use queue priorities and resource allocation to ensure critical workflows get resources first.

### Security Questions

**Q: How are API keys stored?**

A: API keys should be stored as environment variables or in secure configuration files, never in code.

**Q: Can I restrict workflow access?**

A: Yes, implement role-based access control and validate permissions in your API endpoints.

**Q: How do I secure webhook endpoints?**

A: Use webhook signatures for verification, implement rate limiting, and validate IP addresses if possible.

---

This troubleshooting guide covers the most common issues you'll encounter with FlowForge Python API. For additional support:

- Check the [API Documentation](../api/API.md) for detailed endpoint information
- Review the [Getting Started Guide](../guides/getting-started.md) for basic setup
- Visit the [Examples Directory](../examples/) for sample implementations
- Join our [GitHub Discussions](https://github.com/flowforge/python-api/discussions) for community support

If you can't find a solution to your problem, please [open an issue](https://github.com/flowforge/python-api/issues) on GitHub with detailed information about your setup and the error you're encountering.
