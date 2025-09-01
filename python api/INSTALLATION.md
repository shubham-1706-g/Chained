# FlowForge Python API - Installation Guide

## 🚀 Quick Start

### Option 1: Standard Installation (Recommended)

```bash
# Clone repository
git clone <your-repo-url>
cd flowforge-python-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 2: No-Rust Installation (If you encounter Rust compilation errors)

If you get errors about Rust during installation:

```bash
# Use the alternative requirements file
pip install -r requirements-no-rust.txt

# Then run the application
python main.py
```

## 🔧 Prerequisites

### Required Software
- **Python 3.8 or higher** (3.9+ recommended)
- **pip** package manager
- **Git** for cloning repositories

### Optional Software
- **Rust** (only needed for some package compilations)
- **Virtual Environment** (recommended for isolation)

## 🛠️ Detailed Installation Steps

### Step 1: Install Python

**Windows:**
1. Download from https://python.org
2. Run installer
3. Check "Add Python to PATH"
4. Verify: `python --version`

**Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
# Using Homebrew
brew install python

# Or download from python.org
```

### Step 2: Install Rust (Only if needed)

If you encounter compilation errors during pip install:

**Windows:**
1. Download from https://rustup.rs/
2. Run the installer
3. Verify: `rustc --version`

**Linux/macOS:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### Step 3: Clone and Setup Project

```bash
# Clone the repository
git clone <your-repo-url>
cd flowforge-python-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Try standard installation first
pip install -r requirements.txt

# If that fails with Rust errors, use:
pip install -r requirements-no-rust.txt
```

### Step 5: Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
# nano .env  # or use your preferred editor
```

### Step 6: Run the Application

```bash
# Development mode
python main.py

# Or with custom settings
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing Installation

### Check if everything works:

1. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **API Documentation:**
   Visit: http://localhost:8000/docs

3. **API Info:**
   ```bash
   curl http://localhost:8000/api/v1/info
   ```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "ModuleNotFoundError: No module named 'schedule'"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

#### 2. "Rust not found" or compilation errors
```bash
# Option 1: Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Option 2: Use no-rust requirements
pip install -r requirements-no-rust.txt
```

#### 3. "Permission denied" errors
```bash
# Windows: Run as Administrator or use virtual environment
# Linux/Mac: Use sudo or fix permissions
chmod +x venv/bin/activate
```

#### 4. Port already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Kill the process or change port
uvicorn main:app --port 8001
```

#### 5. Python version issues
```bash
# Check Python version
python --version

# Use Python 3 explicitly
python3 -m venv venv
python3 -m pip install -r requirements.txt
```

#### 6. Virtual environment issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Verifying Installation

Run these commands to verify everything is working:

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check virtual environment
which python  # Should point to venv
which pip     # Should point to venv

# Test basic import
python -c "import fastapi, uvicorn; print('✅ Basic imports work')"

# Test application startup
timeout 10 python main.py || echo "✅ App starts without errors"
```

## 🔄 Alternative Installation Methods

### Using pip-tools for locked dependencies
```bash
pip install pip-tools
pip-compile requirements.in  # Creates requirements.txt
pip-sync                    # Installs exact versions
```

### Using Poetry (alternative to pip)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Use Poetry instead of pip
poetry install
poetry run python main.py
```

### Using Docker
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t flowforge-api .
docker run -p 8000:8000 flowforge-api
```

## 📋 System Requirements

### Minimum Requirements
- **RAM**: 512MB
- **Disk**: 500MB free space
- **OS**: Windows 10+, Ubuntu 18.04+, macOS 10.14+

### Recommended Requirements
- **RAM**: 1GB+
- **Disk**: 1GB+ free space
- **CPU**: 1+ core
- **Python**: 3.9+

## 🚀 Post-Installation Steps

### 1. Configure API Keys
Add your API keys to `.env` file:
```env
OPENAI_API_KEY=your_key_here
NOTION_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
```

### 2. Test Integrations
```bash
# Test OpenAI integration
curl -X POST "http://localhost:8000/actions/test" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "openai", "config": {"api_key": "test"}}'
```

### 3. Check Logs
```bash
# View application logs
tail -f logs/flowforge.log
```

## 🆘 Getting Help

### Common Commands
```bash
# Check running processes
ps aux | grep python

# Check open ports
netstat -tlnp | grep 8000

# Check disk space
df -h

# Check memory usage
free -h
```

### Support Resources
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: Check `logs/` directory
- **Environment**: Run `env` to check variables

### If All Else Fails
1. Delete virtual environment: `rm -rf venv`
2. Reinstall Python if needed
3. Try the no-rust requirements: `pip install -r requirements-no-rust.txt`
4. Check the troubleshooting section above

---

**🎉 Successfully installed FlowForge Python API!**

Visit http://localhost:8000/docs for interactive API documentation.
