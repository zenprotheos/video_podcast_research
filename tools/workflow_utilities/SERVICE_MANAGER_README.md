---
title: "SERVICE MANAGER README"
created: "2025-09-23T04:36:49.601Z"
type: "guide"
purpose: "Essential project documentation providing comprehensive information about system capabilities, setup instructions, usage guidelines, and important considerations for effective implementation and operation of the VoiceScribeAI application."
status: "Active"
tags: ["voicescribeai"]
---




# VoiceScribeAI Service Manager

A comprehensive service management system for individual control of frontend and backend services with automatic conflict detection.

## 🎯 Problem Solved

This system addresses the challenge of running services individually through Cursor IDE while preventing port conflicts with the `@start-app.bat` script.

## 🚀 Available Commands

### PowerShell Commands (for Agent/IDE use)
```powershell
# Start services individually
.\tools\workflow_utilities\service_manager.ps1 -Action start-frontend
.\tools\workflow_utilities\service_manager.ps1 -Action start-backend

# Stop services individually
.\tools\workflow_utilities\service_manager.ps1 -Action stop-frontend
.\tools\workflow_utilities\service_manager.ps1 -Action stop-backend

# Check service status
.\tools\workflow_utilities\service_manager.ps1 -Action status

# Stop all services
.\tools\workflow_utilities\service_manager.ps1 -Action stop-all

# Force restart (kills existing processes)
.\tools\workflow_utilities\service_manager.ps1 -Action start-frontend -Force
```

### Batch Files (for convenience)
- `start-frontend.bat` - Start Next.js frontend on port 3000
- `start-backend.bat` - Start Flask backend on port 5000
- `service-status.bat` - Check status of all services
- `stop-services.bat` - Stop all running services

## 🔍 Conflict Detection

The system automatically:
- ✅ Checks if ports 3000 (frontend) or 5000 (backend) are in use
- ✅ Identifies which process is using the port
- ✅ Warns about conflicts and suggests solutions
- ✅ Provides `-Force` option to kill existing processes
- ✅ Tracks PowerShell jobs for clean shutdown

## 📊 Service Status Output

```
VoiceScribeAI Service Status
=================================
Frontend (Port 3000):
  [OK] Job running (ID: 5)
  [IN USE] Port used by: node.exe (PID: 12345)

Backend (Port 5000):
  [STOPPED] No active job
  [FREE] Port available
```

## 🛡️ Safety Features

- **Port Monitoring**: Continuous checking of service ports
- **Process Management**: Clean shutdown of jobs and processes
- **Error Handling**: Comprehensive error reporting
- **Force Options**: Override conflicts when necessary
- **Status Tracking**: Real-time service state monitoring

## 🔄 Integration with Development Workflow

### For Agent/Cursor IDE Use:
```bash
# Terminal commands for individual service control
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\workflow_utilities\service_manager.ps1" -Action start-frontend
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools\workflow_utilities\service_manager.ps1" -Action start-backend
```

### For Manual Use:
```bash
# Use the convenience batch files
start-frontend.bat
start-backend.bat
service-status.bat
stop-services.bat
```

## ⚡ Workflow Recommendations

1. **Agent Development**: Use PowerShell commands directly for precise control
2. **Manual Development**: Use batch files for convenience
3. **Conflict Resolution**: Use `-Force` flag when switching between systems
4. **Status Monitoring**: Always check status before starting services
5. **Clean Shutdown**: Use `stop-all` before switching workflows

## 🔧 Technical Details

- **Ports**: Frontend (3000), Backend (5000)
- **Job Names**: VoiceScribeAI-Frontend, VoiceScribeAI-Backend
- **Working Directories**: Automatic navigation to correct directories
- **Process Tracking**: Both PowerShell jobs and system processes
- **Error Codes**: 0 for success, 1 for conflicts/errors

## 📝 SOP Integration

This system is integrated into the project SOP_AGENT.md and should be used by agents instead of `@start-app.bat` for better IDE integration and conflict prevention.
