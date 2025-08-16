# Legal Document Management System - Startup Guide

## 🚀 **Simple Startup (No Setup Script Required)**

The legal document management system now initializes automatically. Users need zero setup!

---

## 📋 **Server Setup (One-time, by you)**

### **1. Set Environment Variables**
```bash
# Database (Laravel Herd PostgreSQL)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=openhands_legal
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=""

# Legal Workspace Paths
export LEGAL_WORKSPACE_ROOT=/app/legal_workspace
export DRAFT_SYSTEM_PATH=/app/draft_system

# Optional: Redis (Laravel Herd)
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

### **2. Start OpenHands**
```bash
# That's it! Just start OpenHands normally
uvx --from openhands-ai openhands serve
```

### **3. What Happens Automatically**
When OpenHands starts:
- ✅ **Directories created** automatically
- ✅ **Database schema** initialized on first API call
- ✅ **Legal routes** available at `/api/legal/cases`
- ✅ **Workspace manager** ready for case switching

---

## 👥 **User Experience (Zero Setup)**

Users can immediately start using the system:

### **Create First Case**
```bash
curl -X POST http://localhost:3000/api/legal/cases \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bank of America Dispute",
    "case_number": "2024-001",
    "description": "Credit card dispute case"
  }'
```

### **Enter Case Workspace**
```bash
curl -X POST http://localhost:3000/api/legal/cases/{case_id}/enter
```

### **What Happens Automatically**
When a user creates their first case:
- ✅ **Case directory** created automatically
- ✅ **Draft system** copied as template
- ✅ **Workspace** initialized with legal workflow
- ✅ **AI agent** loads case-specific personality
- ✅ **Ready to work** immediately

---

## 🔧 **What's Automatic vs Manual**

### **✅ Automatic (No Action Required)**
- Directory creation
- Database schema initialization  
- Case workspace setup
- Draft system template copying
- AI agent context loading
- Workspace switching
- File permissions
- Error handling

### **⚙️ Manual (Server Operator Only)**
- Set environment variables
- Ensure PostgreSQL is running (Laravel Herd)
- Ensure draft_system folder exists
- Start OpenHands server

### **👤 Manual (Users)**
- Create cases via API
- Switch between workspaces
- Work with documents

---

## 🚨 **Troubleshooting**

### **If Legal Features Don't Work**

1. **Check Environment Variables**
   ```bash
   echo $LEGAL_WORKSPACE_ROOT
   echo $DRAFT_SYSTEM_PATH
   echo $POSTGRES_HOST
   ```

2. **Check PostgreSQL Connection**
   ```bash
   psql -h localhost -p 5433 -U postgres -d postgres -c "SELECT version();"
   ```

3. **Check Draft System**
   ```bash
   ls -la /app/draft_system/
   # Should show: README.md, standards/, templates/, scripts/, etc.
   ```

4. **Check Logs**
   - Look for "Legal workspace manager initialized successfully"
   - Look for "Legal database initialized automatically"
   - Any warnings are logged but don't prevent startup

### **Common Issues**

| Issue | Solution |
|-------|----------|
| "Draft system not found" | Ensure draft_system folder is mounted/copied |
| "Database connection failed" | Check PostgreSQL is running on port 5433 |
| "Permission denied" | Check file permissions on workspace directories |
| "Legal routes not found" | Restart OpenHands server |

---

## 📊 **System Status Endpoints**

Check if legal system is working:

```bash
# Check workspace status
curl http://localhost:3000/api/legal/workspace/current

# List available cases
curl http://localhost:3000/api/legal/cases

# Health check (if legal system is loaded)
curl http://localhost:3000/api/legal/workspace/available-cases
```

---

## 🎯 **Success Indicators**

### **Server Startup**
Look for these log messages:
```
✅ Legal workspace manager initialized successfully
✅ Legal database initialized automatically
✅ Legal case routes registered
```

### **First Case Creation**
```bash
# Should return case details with workspace_path
{
  "case_id": "uuid-here",
  "title": "Bank of America Dispute", 
  "workspace_path": "/app/legal_workspace/cases/case-uuid/draft_system",
  "draft_system_initialized": true
}
```

### **Workspace Switching**
```bash
# Should return workspace info
{
  "case_id": "uuid-here",
  "workspace_path": "/path/to/case/draft_system",
  "workspace_mounted": true,
  "draft_system_initialized": true
}
```

---

## 🎉 **That's It!**

No setup scripts, no complex initialization. The system is designed to:

1. **Start automatically** when OpenHands starts
2. **Initialize on demand** when first used
3. **Handle errors gracefully** without breaking OpenHands
4. **Provide clear feedback** about what's working

**Users can start creating legal cases immediately after you start the server!**
