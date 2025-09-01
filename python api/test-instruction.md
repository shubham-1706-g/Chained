# FlowForge Python API - Testing Instructions

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Test Environment Setup](#test-environment-setup)
4. [Running Tests](#running-tests)
5. [Test Configuration](#test-configuration)
6. [Test Categories](#test-categories)
7. [Performance Testing](#performance-testing)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Test Maintenance](#test-maintenance)

## 🎯 Overview

This comprehensive testing guide covers the FlowForge Python API's extensive test suite, which includes:

- **1,000+ Unit Tests**: Component-level testing
- **50+ Integration Tests**: API and database integration
- **30+ End-to-End Tests**: Complete workflow scenarios
- **15+ Performance Tests**: Load and scalability testing
- **80%+ Code Coverage**: Thorough test coverage

### Test Structure

```
tests/
├── unit/                    # Unit tests (1000+ tests)
│   ├── test_actions.py     # 22 action types
│   ├── test_triggers.py    # 6 trigger types
│   ├── test_core.py        # Engine, Executor, Context
│   └── test_api_routes.py  # FastAPI endpoints
├── integration/            # Integration tests
│   ├── __init__.py         # Shared fixtures & utilities
│   ├── test_database_integration.py
│   ├── test_external_services.py
│   └── test_auth_integration.py
├── e2e/                    # End-to-end tests
│   ├── __init__.py         # Test data & utilities
│   ├── conftest.py         # Pytest configuration
│   ├── test_ecommerce_workflow.py
│   ├── test_marketing_workflow.py
│   ├── test_customer_support_workflow.py
│   └── test_performance_workflow.py
└── conftest.py             # Global test configuration
```

## 📋 Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **PostgreSQL**: 14+ (for integration tests)
- **Redis**: 7+ (for integration tests)
- **Git**: For version control

### Python Dependencies

```bash
# Core testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-mock

# Performance testing
pip install psutil memory-profiler

# Code quality
pip install black flake8 mypy bandit safety

# Optional: Parallel testing
pip install pytest-xdist

# Optional: HTML reports
pip install pytest-html
```

### Database Setup (for Integration/E2E Tests)

```bash
# Create test database
createdb flowforge_test

# Create test user (optional)
createuser flowforge_test_user --createdb
psql -c "ALTER USER flowforge_test_user PASSWORD 'test_password';"

# Or use Docker
docker run --name postgres-test -e POSTGRES_DB=flowforge_test \
  -e POSTGRES_USER=test_user -e POSTGRES_PASSWORD=test_password \
  -p 5433:5432 -d postgres:14
```

### Redis Setup (for Integration/E2E Tests)

```bash
# Start Redis for testing
redis-server --port 6380 --daemonize yes

# Or use Docker
docker run --name redis-test -p 6380:6379 -d redis:7-alpine
```

## 🛠️ Test Environment Setup

### 1. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/flowforge/python-api.git
cd python-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If separate dev requirements
```

### 2. Environment Configuration

Create `.env.test` file:

```bash
# Test Environment Configuration
ENVIRONMENT=test
DEBUG=true
TEST_MODE=true

# Database (Test)
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5433/flowforge_test
TEST_DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5433/flowforge_test

# Redis (Test)
REDIS_URL=redis://localhost:6380/1
TEST_REDIS_URL=redis://localhost:6380/1

# API Configuration
API_KEY=test-api-key-12345
SECRET_KEY=test-secret-key-for-jwt

# External Services (Mocked for tests)
OPENAI_API_KEY=test-openai-key
SMTP_SERVER=smtp.mailtrap.io
SMTP_USERNAME=test-user
SMTP_PASSWORD=test-password

# Test-specific settings
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```

### 3. Database Migration (for Integration Tests)

```bash
# Run database migrations for test database
export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/flowforge_test"
alembic upgrade head

# Or if using Flask-Migrate
flask db upgrade
```

### 4. Verify Setup

```bash
# Test Python environment
python --version
python -c "import pytest; print('pytest version:', pytest.__version__)"

# Test database connection
python -c "
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect('postgresql://test_user:test_password@localhost:5433/flowforge_test')
    result = await conn.fetchval('SELECT 1')
    print('Database connection: OK' if result == 1 else 'FAILED')
    await conn.close()

asyncio.run(test_db())
"

# Test Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6380, decode_responses=True)
print('Redis connection:', 'OK' if r.ping() else 'FAILED')
"
```

## 🏃 Running Tests

### Quick Start Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_actions.py -v

# Run specific test
pytest tests/unit/test_actions.py::TestHTTPActions::test_http_action_success -v

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run tests with HTML report
pytest --html=report.html
```

### Running Different Test Categories

#### Unit Tests (Fast, Isolated)

```bash
# All unit tests
pytest tests/unit/ -v

# Specific component tests
pytest tests/unit/test_actions.py -v
pytest tests/unit/test_triggers.py -v
pytest tests/unit/test_core.py -v
pytest tests/unit/test_api_routes.py -v

# Run with coverage for unit tests only
pytest tests/unit/ --cov=app --cov-report=html
```

#### Integration Tests (Medium Speed, Database Required)

```bash
# All integration tests
pytest tests/integration/ -v

# Specific integration areas
pytest tests/integration/test_database_integration.py -v
pytest tests/integration/test_external_services.py -v
pytest tests/integration/test_auth_integration.py -v

# Run integration tests with database setup
pytest tests/integration/ -v --tb=short
```

#### End-to-End Tests (Slow, Full Environment Required)

```bash
# All E2E tests
pytest tests/e2e/ -v

# Specific E2E scenarios
pytest tests/e2e/test_ecommerce_workflow.py -v
pytest tests/e2e/test_marketing_workflow.py -v
pytest tests/e2e/test_customer_support_workflow.py -v

# Performance-focused E2E tests
pytest tests/e2e/test_performance_workflow.py -v
```

#### Custom E2E Test Runner

```bash
# Use custom E2E test runner for advanced features
python scripts/run_e2e_tests.py

# Run with performance monitoring
python scripts/run_e2e_tests.py --performance-monitoring

# Run parallel E2E tests
python scripts/run_e2e_tests.py --parallel

# Generate JSON report
python scripts/run_e2e_tests.py --report-format json --output-file e2e-results.json

# Run dedicated performance tests
python scripts/run_e2e_tests.py --performance-test --concurrency 20 --performance-duration 120
```

### Running Tests by Markers

```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only integration tests
pytest -m "integration" -v

# Run only E2E tests
pytest -m "e2e" -v

# Run performance tests
pytest -m "performance" -v

# Run load tests
pytest -m "load_test" -v
```

## ⚙️ Test Configuration

### Pytest Configuration

Create `pytest.ini` in project root:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    load_test: Load testing
    slow: Slow running tests
    database: Requires database
    external: Requires external services
asyncio_mode = auto
```

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    app/main.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

### Test Data Configuration

Configure test data in `tests/conftest.py`:

```python
@pytest.fixture
def sample_workflow_data():
    """Sample workflow for testing."""
    return {
        "name": "Test Workflow",
        "description": "Workflow for testing",
        "nodes": [
            {
                "id": "test-node",
                "type": "action",
                "action_type": "http",
                "config": {"method": "GET", "url": "https://httpbin.org/json"}
            }
        ],
        "connections": []
    }

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "permissions": ["read", "write"]
    }
```

## 📊 Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation
**Speed**: Fast (< 1 second per test)
**Dependencies**: Minimal (mocks/stubs)
**Coverage**: 80%+ of code

```bash
# Example unit test
def test_http_action_validation():
    """Test HTTP action configuration validation."""
    config = {"method": "GET", "url": "https://api.example.com"}
    action = HTTPAction(config)

    assert action.validate_config() is True

    invalid_config = {"method": "INVALID"}
    invalid_action = HTTPAction(invalid_config)
    assert invalid_action.validate_config() is False
```

### 2. Integration Tests

**Purpose**: Test component interactions and external integrations
**Speed**: Medium (1-10 seconds per test)
**Dependencies**: Database, Redis, external APIs
**Coverage**: API endpoints, database operations

```bash
# Example integration test
@pytest.mark.asyncio
async def test_workflow_creation_and_execution():
    """Test complete workflow creation and execution."""
    workflow_data = {
        "name": "Integration Test",
        "nodes": [...],
        "connections": [...]
    }

    # Create workflow
    response = await client.post("/api/v1/flows/create", json=workflow_data)
    assert response.status_code == 200

    # Execute workflow
    result = await client.post("/api/v1/flows/execute", json={
        "workflow_id": response.json()["workflow_id"],
        "input_data": {"test": "data"}
    })
    assert result.status_code == 200
```

### 3. End-to-End Tests

**Purpose**: Test complete user workflows and business scenarios
**Speed**: Slow (10-60 seconds per test)
**Dependencies**: Full application stack
**Coverage**: User journeys, complex workflows

```bash
# Example E2E test
@pytest.mark.asyncio
async def test_complete_ecommerce_order_fulfillment():
    """Test complete e-commerce order fulfillment workflow."""
    with mock_external_services():
        # Create order fulfillment workflow
        workflow = await create_ecommerce_workflow()

        # Simulate order data
        order_data = get_sample_order_data()

        # Execute workflow
        result = await execute_workflow(workflow["id"], order_data)

        # Verify complete fulfillment process
        final_status = await wait_for_completion(result["execution_id"])
        assert final_status["status"] == "completed"

        # Verify all steps completed
        assert_step_completed(final_status, "validate-order")
        assert_step_completed(final_status, "check-inventory")
        assert_step_completed(final_status, "process-payment")
        assert_step_completed(final_status, "create-shipping")
        assert_step_completed(final_status, "send-confirmation")
```

## ⚡ Performance Testing

### Running Performance Tests

```bash
# Run performance-focused tests
pytest tests/e2e/test_performance_workflow.py -v

# Run with custom performance runner
python scripts/run_e2e_tests.py --performance-test \
  --concurrency 50 \
  --performance-duration 300

# Run load tests
pytest -m "load_test" -v

# Profile specific tests
pytest tests/unit/test_actions.py --profile
```

### Performance Metrics

Monitor these key metrics during performance testing:

```python
def measure_performance(func):
    """Decorator to measure test performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            print(f"Performance: {end_time - start_time:.2f}s, "
                  f"Memory: {end_memory - start_memory:.1f}MB")

    return wrapper
```

### Performance Benchmarks

| Test Type | Expected Duration | Memory Usage | CPU Usage |
|-----------|------------------|--------------|-----------|
| Unit Test | < 0.1s | < 10MB | < 5% |
| Integration Test | < 5s | < 50MB | < 20% |
| E2E Test | < 30s | < 200MB | < 50% |
| Performance Test | 60-300s | < 500MB | < 80% |

### Load Testing Commands

```bash
# Simulate concurrent users
pytest tests/e2e/test_performance_workflow.py::TestWorkflowPerformance::test_concurrent_workflow_execution_performance -v

# Test database connection pool
pytest tests/integration/test_database_integration.py::TestDatabaseIntegration::test_database_connection_pool_performance -v

# Memory usage testing
pytest tests/e2e/test_performance_workflow.py::TestWorkflowPerformance::test_memory_usage_under_load -v
```

## 🔄 CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: flowforge_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6380:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        black --check app tests
        flake8 app tests

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=app --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5433/flowforge_test
        REDIS_URL: redis://localhost:6380/1

    - name: Run E2E tests
      run: |
        python scripts/run_e2e_tests.py --parallel

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                script {
                    sh '''
                        python -m venv venv
                        source venv/bin/activate
                        pip install -r requirements.txt
                        pip install -r requirements-dev.txt
                    '''
                }
            }
        }

        stage('Lint') {
            steps {
                script {
                    sh '''
                        source venv/bin/activate
                        black --check app tests
                        flake8 app tests
                        mypy app
                    '''
                }
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    sh '''
                        source venv/bin/activate
                        pytest tests/unit/ -v --cov=app --cov-report=xml
                    '''
                }
            }
        }

        stage('Integration Tests') {
            steps {
                script {
                    sh '''
                        source venv/bin/activate
                        pytest tests/integration/ -v --tb=short
                    '''
                }
            }
        }

        stage('E2E Tests') {
            steps {
                script {
                    sh '''
                        source venv/bin/activate
                        python scripts/run_e2e_tests.py --performance-monitoring
                    '''
                }
            }
        }
    }

    post {
        always {
            publishCoverage adapters: [coberturaAdapter('coverage.xml')]
            junit '**/test-results/*.xml'
        }
    }
}
```

## 🔧 Troubleshooting

### Common Test Issues

#### 1. Import Errors

```bash
# Fix import issues
pip install -e .

# Or check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if package is installed
pip list | grep flowforge
```

#### 2. Database Connection Issues

```bash
# Check database status
psql -h localhost -p 5433 -U test_user -d flowforge_test -c "SELECT 1;"

# Reset test database
psql -h localhost -p 5433 -U test_user -d postgres -c "DROP DATABASE IF EXISTS flowforge_test;"
createdb -h localhost -p 5433 -U test_user flowforge_test

# Run migrations
alembic upgrade head
```

#### 3. Redis Connection Issues

```bash
# Check Redis status
redis-cli -p 6380 ping

# Clear Redis data
redis-cli -p 6380 FLUSHDB

# Check Redis configuration
redis-cli -p 6380 CONFIG GET maxmemory
```

#### 4. Async Test Issues

```bash
# Ensure proper async test setup
pytest --asyncio-mode=auto

# Check for asyncio issues
python -c "
import asyncio
print('AsyncIO version:', asyncio.__version__)
"
```

#### 5. Coverage Issues

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage gaps
pytest --cov=app --cov-report=term-missing

# Exclude files from coverage
pytest --cov=app --cov-report=html --cov-config=.coveragerc
```

### Debug Commands

```bash
# Run tests with debug output
pytest -v -s --pdb

# Run specific failing test
pytest tests/unit/test_actions.py::TestHTTPActions::test_http_action_success -v -s

# Check test discovery
pytest --collect-only

# Run tests with different verbosity
pytest -v     # Verbose
pytest -vv    # Very verbose
pytest -q     # Quiet

# Run tests with timing
pytest --durations=10

# Run tests in random order (detect order dependencies)
pytest --random-order
```

### Performance Troubleshooting

```bash
# Profile slow tests
pytest --profile

# Check memory usage
pytest --memory-report

# Monitor system resources during tests
python -c "
import psutil
import time

for _ in range(10):
    print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')
    time.sleep(1)
"
```

## 📋 Best Practices

### Writing Tests

#### 1. Test Naming Conventions

```python
# Good test names
def test_http_action_success():
def test_workflow_execution_with_error():
def test_user_authentication_failure()

# Bad test names
def test_function():  # Too generic
def test_stuff():     # Not descriptive
```

#### 2. Test Organization

```python
class TestHTTPActions:
    """Test HTTP-related actions."""

    @pytest.fixture
    def http_action(self):
        """Provide HTTP action instance."""
        return HTTPAction({"method": "GET", "url": "https://api.example.com"})

    def test_successful_request(self, http_action):
        """Test successful HTTP request."""
        # Test implementation

    def test_error_handling(self, http_action):
        """Test error handling."""
        # Test implementation
```

#### 3. Mocking Best Practices

```python
# Good mocking
@patch('aiohttp.ClientSession.request')
async def test_with_mock(mock_request):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": "test"}
    mock_request.return_value = mock_response

    result = await make_http_request()
    assert result["status"] == 200

# Avoid over-mocking
# Don't mock everything - test real integrations where possible
```

#### 4. Test Data Management

```python
# Use factories for test data
def create_test_workflow(name="Test Workflow"):
    """Factory for test workflow data."""
    return {
        "name": name,
        "description": f"Test workflow: {name}",
        "nodes": [...],
        "connections": [...]
    }

# Use fixtures for shared data
@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "permissions": ["read", "write"]
    }
```

### Test Execution Best Practices

#### 1. Test Isolation

```python
# Use fixtures for setup/cleanup
@pytest.fixture
async def clean_database():
    """Ensure clean database state."""
    # Setup
    yield
    # Cleanup
    await cleanup_test_data()

# Run tests in isolation
@pytest.mark.isolated
async def test_database_operation(clean_database):
    # Test implementation
```

#### 2. Test Categories

```python
# Mark tests appropriately
@pytest.mark.unit
def test_component_logic():
    """Fast unit test."""

@pytest.mark.integration
@pytest.mark.database
async def test_database_integration():
    """Integration test requiring database."""

@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_workflow():
    """Slow E2E test."""

@pytest.mark.performance
async def test_system_performance():
    """Performance test."""
```

#### 3. Test Configuration

```python
# Environment-specific configuration
@pytest.mark.skipif(os.getenv("CI") != "true", reason="CI only")
def test_ci_specific():
    """Test that only runs in CI."""

@pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
def test_linux_specific():
    """Test specific to Linux."""
```

## 🔄 Test Maintenance

### Regular Maintenance Tasks

#### 1. Update Test Dependencies

```bash
# Update test dependencies monthly
pip install --upgrade pytest pytest-asyncio pytest-cov

# Check for outdated packages
pip list --outdated

# Update specific packages
pip install --upgrade pytest==7.4.0
```

#### 2. Review Test Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# Identify uncovered code
pytest --cov=app --cov-report=term-missing

# Set coverage goals
pytest --cov=app --cov-fail-under=80
```

#### 3. Update Test Data

```python
# Regularly update test data to reflect real scenarios
def get_current_api_response_schema():
    """Fetch current API response schema for testing."""
    # Implementation to get latest schema
    pass

def update_test_mocks():
    """Update mock responses to match current API."""
    # Implementation to update mocks
    pass
```

#### 4. Performance Baseline Updates

```python
# Update performance baselines
def update_performance_baseline():
    """Update expected performance metrics."""
    baseline = {
        "unit_test_time": 0.05,  # seconds
        "integration_test_time": 2.0,
        "e2e_test_time": 15.0,
        "memory_usage": 150,  # MB
        "cpu_usage": 30  # %
    }
    # Save to file or database
    pass
```

### Test Health Monitoring

#### 1. Test Flakiness Detection

```python
# Detect flaky tests
def detect_flaky_tests():
    """Run tests multiple times to detect flakiness."""
    flaky_tests = []

    for _ in range(5):  # Run 5 times
        result = subprocess.run(["pytest", "-v"], capture_output=True, text=True)

        # Parse failures
        if result.returncode != 0:
            # Extract failed test names
            failed_tests = parse_failed_tests(result.stdout)
            flaky_tests.extend(failed_tests)

    # Report flaky tests
    flaky_counts = {}
    for test in flaky_tests:
        flaky_counts[test] = flaky_counts.get(test, 0) + 1

    # Tests that failed at least once are potentially flaky
    potentially_flaky = [test for test, count in flaky_counts.items() if count < 5]
    return potentially_flaky
```

#### 2. Test Performance Tracking

```python
# Track test execution times
test_performance_history = {}

def track_test_performance(test_name: str, execution_time: float):
    """Track test performance over time."""
    if test_name not in test_performance_history:
        test_performance_history[test_name] = []

    test_performance_history[test_name].append({
        "timestamp": datetime.utcnow(),
        "execution_time": execution_time
    })

    # Keep only last 100 runs
    if len(test_performance_history[test_name]) > 100:
        test_performance_history[test_name].pop(0)

def analyze_performance_trends():
    """Analyze performance trends."""
    for test_name, history in test_performance_history.items():
        if len(history) >= 10:
            recent_times = [h["execution_time"] for h in history[-10:]]
            avg_time = statistics.mean(recent_times)
            std_dev = statistics.stdev(recent_times)

            print(f"{test_name}: {avg_time:.2f}s ± {std_dev:.2f}s")

            # Alert if performance degraded
            if avg_time > get_baseline_time(test_name) * 1.5:
                print(f"⚠️  Performance degradation detected for {test_name}")
```

### Automated Test Maintenance

#### 1. CI/CD Pipeline for Test Maintenance

```yaml
# Test maintenance workflow
name: Test Maintenance

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  maintenance:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Update dependencies
      run: |
        pip install --upgrade pytest pytest-asyncio pytest-cov
        pip install --upgrade -r requirements.txt

    - name: Run full test suite
      run: |
        pytest --cov=app --cov-report=xml

    - name: Check for flaky tests
      run: |
        python scripts/check_flaky_tests.py

    - name: Update performance baselines
      run: |
        python scripts/update_performance_baselines.py

    - name: Generate maintenance report
      run: |
        python scripts/generate_maintenance_report.py
```

## 📈 Advanced Testing Techniques

### Property-Based Testing

```python
# Use hypothesis for property-based testing
from hypothesis import given, strategies as st

@given(
    workflow_name=st.text(min_size=1, max_size=100),
    node_count=st.integers(min_value=1, max_value=20)
)
def test_workflow_creation_properties(workflow_name, node_count):
    """Test workflow creation with various inputs."""
    nodes = [
        {
            "id": f"node-{i}",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.example.com"}
        }
        for i in range(node_count)
    ]

    workflow_data = {
        "name": workflow_name,
        "nodes": nodes,
        "connections": []
    }

    # Test that workflow creation handles various inputs
    workflow = create_workflow(workflow_data)
    assert workflow["name"] == workflow_name
    assert len(workflow["nodes"]) == node_count
```

### Mutation Testing

```bash
# Use mutmut for mutation testing
pip install mutmut

# Run mutation tests
mutmut run --paths-to-mutate app/ --tests-dir tests/

# Check results
mutmut results

# Generate HTML report
mutmut html
```

### Fuzz Testing

```python
# Use atheris for fuzz testing
import atheris

def test_fuzz_workflow_creation(input_bytes):
    """Fuzz test for workflow creation."""
    fdp = atheris.FuzzedDataProvider(input_bytes)

    try:
        # Generate fuzzed workflow data
        workflow_data = {
            "name": fdp.ConsumeString(100),
            "description": fdp.ConsumeString(500),
            "nodes": []
        }

        # Add fuzzed nodes
        for _ in range(fdp.ConsumeIntInRange(0, 10)):
            node = {
                "id": fdp.ConsumeString(50),
                "type": fdp.ConsumeString(20),
                "config": {}
            }
            workflow_data["nodes"].append(node)

        # Test workflow creation
        create_workflow(workflow_data)

    except Exception:
        # Expected to handle invalid inputs gracefully
        pass

# Run fuzz test
atheris.Setup(sys.argv, test_fuzz_workflow_creation)
atheris.Fuzz()
```

## 🎯 Quick Reference

### Essential Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test type
pytest -m "unit"         # Unit tests
pytest -m "integration"  # Integration tests
pytest -m "e2e"          # E2E tests

# Run custom E2E runner
python scripts/run_e2e_tests.py --performance-monitoring

# Generate reports
pytest --html=report.html
pytest --cov-report=html
```

### Environment Variables

```bash
# Test configuration
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export TEST_DATABASE_URL=postgresql://test:test@localhost/test_db
export TEST_REDIS_URL=redis://localhost:6380/1

# Performance testing
export PERFORMANCE_TEST_DURATION=300
export PERFORMANCE_TEST_CONCURRENCY=20
```

### Test File Structure

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # API and database tests
├── e2e/              # Complete workflow tests
├── conftest.py       # Shared configuration
└── __init__.py       # Test package
```

---

## 🎉 Summary

This comprehensive testing guide ensures you can:

- ✅ **Run comprehensive test suites** across all test categories
- ✅ **Configure test environments** for different scenarios
- ✅ **Debug and troubleshoot** test failures effectively
- ✅ **Monitor test performance** and identify bottlenecks
- ✅ **Integrate testing** into CI/CD pipelines
- ✅ **Maintain test quality** over time

**Happy Testing! 🧪**

For more information, see the [API Documentation](../docs/api/API.md) and [Architecture Guide](../docs/guides/architecture.md).
