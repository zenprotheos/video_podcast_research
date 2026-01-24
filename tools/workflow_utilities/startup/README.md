---
title: "README"
created: "2025-09-23T04:36:49.603Z"
type: "guide"
purpose: "Essential project documentation providing comprehensive information about system capabilities, setup instructions, usage guidelines, and important considerations for effective implementation and operation of the VoiceScribeAI application."
status: "Active"
tags: ["voicescribeai"]
---




# VoiceScribeAI Startup Scripts

## 📁 Organization
This directory contains organized startup and service management scripts for VoiceScribeAI.

## 🚀 Scripts

### Primary Scripts
- **`start-backend.bat`** - Start only the Flask backend service (port 5000)
- **`start-frontend.bat`** - Start only the Next.js frontend service (port 3000)
- **`stop-services.bat`** - Stop all running services

### Usage
```bash
# Start individual services
start-backend.bat
start-frontend.bat

# Stop all services
stop-services.bat
```

### Integration
These scripts integrate with:
- `tools/workflow_utilities/service_manager.ps1` - Core service management
- Port conflict detection and resolution
- Automatic service verification

## 🎯 Primary Command
For the most convenient startup experience, use the root-level script:
```bash
start-smart-simple.bat
```
This provides one-click startup with automatic checks, service starting, and browser launch.

## 📊 Status Checking
```bash
# Quick status
start-smart-simple.bat status

# Full detailed status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools/workflow_utilities/service_manager.ps1" -Action status
```
