# 🚀 Squad API - Complete Multi-Terminal Activator System

## 📋 Overview

This comprehensive activator system enables your Squad API project to be easily integrated with other projects through a sophisticated multi-terminal management system. The system provides automated startup, monitoring, and shutdown of all Squad API components across multiple terminal windows.

## 🎯 Key Features

✅ **Multi-Terminal Management**: Automatically opens and manages 3 terminal windows
✅ **Dual Script Support**: Both Batch (.bat) and PowerShell (.ps1) versions
✅ **Process Monitoring**: Comprehensive status checking and health verification
✅ **Clean Shutdown**: Graceful termination of all services and terminals
✅ **Integration Ready**: Designed for seamless integration with other projects
✅ **Redis-Only Setup**: Optimized for Redis without Docker dependencies

## 📁 Complete File Structure

```
📦 Squad API Multi-Terminal Activator System
├── 🔥 ACTIVATION SCRIPTS
│   ├── activate_squad_complete.bat          # Main Batch activator
│   ├── activate_squad_complete.ps1          # PowerShell activator
│   └── activate_squad.bat                   # Original activator
│
├── 📊 STATUS & MONITORING
│   ├── squad_status_complete.bat            # Comprehensive status checker
│   └── squad_status.sh                      # Unix status checker
│
├── 🛑 SHUTDOWN SCRIPTS
│   ├── squad_stop_complete.bat              # Complete shutdown script
│   ├── squad_stop_complete.ps1              # PowerShell shutdown
│   └── squad_stop.bat                       # Original shutdown
│
├── 🐳 DOCKER CONFIGURATION (Optional)
│   └── docker-compose.yaml                  # Full stack with monitoring
│
└── 📚 INTEGRATION FILES
    ├── squad_client_enhanced.py             # Enhanced client for other projects
    └── SQUAD_ACTIVATOR_GUIDE.md             # This guide
```

## 🚀 Quick Start Guide

### 1. Simple Activation (Recommended)

**Windows Batch:**
```cmd
# From the Squad API directory
activate_squad_complete.bat
```

**PowerShell:**
```powershell
# From the Squad API directory
.\activate_squad_complete.ps1
```

### 2. What Happens During Activation

**Terminal 1 - API Server + Monitoring**
- Starts the Squad API server on port 8000
- Displays real-time logs and monitoring information
- Provides health check endpoints

**Terminal 2 - Client Interface**
- Opens interactive client interface
- Allows testing different agents (dev, analyst, architect, etc.)
- Perfect for development and debugging

**Terminal 3 - Log Monitor & Status**
- Shows live system status
- Displays Docker service health
- Provides real-time log monitoring

### 3. System Verification

**Quick Health Check:**
```cmd
curl http://localhost:8000/health
```

**Complete Status Report:**
```cmd
squad_status_complete.bat
```

### 4. Graceful Shutdown

**Standard Shutdown:**
```cmd
squad_stop_complete.bat
```

**PowerShell Shutdown:**
```powershell
.\squad_stop_complete.ps1
```

## 🔧 Integration with Other Projects

### Method 1: Direct API Integration

1. **Copy the client file to your project:**
```bash
cp /path/to/squad-api/squad_client_enhanced.py /your-project/
```

2. **Use in your project:**
```python
from squad_client_enhanced import SquadClient

# Initialize the client
squad = SquadClient(base_url='http://localhost:8000')

# Use different agents
response = squad.ask('dev', 'Create a Flask REST API for user management')
print(response)

response = squad.ask('analyst', 'Analyze this dataset and provide insights')
print(response)
```

### Method 2: REST API Integration

```python
import requests

# Direct API calls
api_url = 'http://localhost:8000'
headers = {'Content-Type': 'application/json'}

# Test agent response
data = {
    'prompt': 'Write a Python function to calculate fibonacci numbers',
    'agent': 'dev',
    'max_tokens': 200
}

response = requests.post(f'{api_url}/agents/dev/query', json=data, headers=headers)
if response.status_code == 200:
    result = response.json()
    print(result['response'])
```

### Method 3: Environment Variable Integration

Add to your project's `.env`:
```bash
SQUAD_API_URL=http://localhost:8000
SQUAD_API_KEY=your_api_key_if_needed
```

## 🎯 Available Agents

| Agent | Purpose | Use Case |
|-------|---------|----------|
| `dev` | Code generation & debugging | Generate code, debug issues, refactoring |
| `analyst` | Research & data analysis | Data analysis, research, report generation |
| `architect` | System design & architecture | System design, architecture planning |
| `reviewer` | Code review & quality assurance | Code reviews, quality checks |
| `qa` | Test design & validation | Test creation, validation strategies |
| `pm` | Planning & project management | Project planning, task management |

## 📊 Monitoring & Health Checks

### Core Endpoints

- **Health Check**: `http://localhost:8000/health`
- **API Documentation**: `http://localhost:8000/docs`
- **Provider Status**: `http://localhost:8000/providers`
- **Cost Statistics**: `http://localhost:8000/cost/stats`

### System Status Commands

```cmd
# Quick health check
curl http://localhost:8000/health

# Full system status
squad_status_complete.bat

# Docker services status
docker-compose ps

# Process monitoring
tasklist | findstr python
```

## 🔧 Advanced Configuration

### Custom Port Setup

**PowerShell version supports custom ports:**
```powershell
.\activate_squad_complete.ps1 -CustomPort 8080
```

### Skip Components

**Start without client interface:**
```powershell
.\activate_squad_complete.ps1 -NoClientTest
```

**Skip log terminal:**
```powershell
.\activate_squad_complete.ps1 -SkipLogTerminal
```

### Force Operations

**PowerShell shutdown with force:**
```powershell
.\squad_stop_complete.ps1 -Force
```

## 🐛 Troubleshooting

### Common Issues

**1. API Not Responding**
- Check if port 8000 is available: `netstat -ano | findstr :8000`
- Verify Python processes: `tasklist | findstr python`
- Restart with: `activate_squad_complete.bat`

**2. Docker Services Issues**
- Ensure Docker Desktop is running
- Check Docker status: `docker --version`
- Manual start: `docker-compose up -d`

**3. Permission Issues**
- Run Command Prompt as Administrator
- PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**4. Port Conflicts**
- Check port usage: `netstat -ano -p tcp | findstr :8000`
- Kill conflicting processes if needed
- Use custom ports with PowerShell scripts

### System Requirements

- **Python**: 3.11 or higher
- **Docker Desktop**: For full monitoring stack
- **Windows**: 10/11 or Windows Server 2019+
- **PowerShell**: 5.1 or higher (for PowerShell scripts)

## 📈 Performance Optimization

### For Development
```cmd
# Quick start without full monitoring stack
activate_squad.bat
```

### For Production
```cmd
# Full stack with monitoring
activate_squad_complete.bat
```

### For Testing
```powershell
# PowerShell with custom configuration
.\activate_squad_complete.ps1 -FullStack -NoClientTest
```

## 🎉 Success Indicators

When the system is working correctly, you should see:

✅ **Terminal 1**: API server running with log output
✅ **Terminal 2**: Client interface ready for interaction
✅ **Terminal 3**: Live monitoring and status updates
✅ **Health Check**: `{"status":"healthy","service":"squad-api"}`
✅ **API Docs**: Available at `http://localhost:8000/docs`

## 📝 Summary

This multi-terminal activator system provides:

🎯 **Complete Solution**: Start, monitor, and stop your Squad API with ease
🔧 **Flexible Configuration**: Multiple scripts for different use cases
📊 **Comprehensive Monitoring**: Real-time status and health checking
🚀 **Easy Integration**: Simple methods to use Squad API in other projects
🛠️ **Production Ready**: Robust error handling and graceful shutdown

Your Squad API is now ready for seamless integration with any development project!

---

**Status**: ✅ **COMPLETE AND READY**
**Last Updated**: 2025-11-14
**Version**: 1.0.0 Multi-Terminal Activator System
