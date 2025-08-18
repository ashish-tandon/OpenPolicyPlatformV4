# 🔧 Open Policy Platform - Scripts

This directory contains all the scripts needed to set up, start, and manage the Open Policy Platform.

## 📋 **Available Scripts**

### **Setup Scripts**
- **`setup-unified.sh`** - Complete platform setup (recommended)
- **`setup.sh`** - Legacy setup script

### **Startup Scripts**
- **`start-all.sh`** - Start all services (backend + web)
- **`start-backend.sh`** - Start backend API only
- **`start-web.sh`** - Start web application only
- **`start-mobile.sh`** - Start mobile app (future use)

### **Utility Scripts**
- **`verify-merge.sh`** - Verify merge integrity
- **`deploy.sh`** - Production deployment (coming soon)

## 🚀 **Quick Start**

### **1. Complete Setup**
```bash
# Run the unified setup script
./setup-unified.sh
```

### **2. Start All Services**
```bash
# Start backend and web application
./start-all.sh
```

### **3. Individual Services**
```bash
# Start backend only
./start-backend.sh

# Start web application only
./start-web.sh
```

## 📊 **Service Access Points**

After starting services, access them at:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:5173
- **Admin Interface**: http://localhost:5173/admin

## 🔧 **Script Details**

### **setup-unified.sh**
Complete platform setup including:
- Database setup and import
- Backend environment setup
- Web application setup
- Mobile apps preservation
- Environment configuration

### **start-all.sh**
Starts all services in the correct order:
1. Backend API (port 8000)
2. Web application (port 5173)
3. Provides access URLs and PIDs

### **start-backend.sh**
Starts the FastAPI backend:
- Activates Python virtual environment
- Starts uvicorn server
- Enables auto-reload for development

### **start-web.sh**
Starts the React web application:
- Installs dependencies if needed
- Starts Vite development server
- Enables hot reload

## 🛠️ **Troubleshooting**

### **Common Issues**
1. **Port conflicts**: Ensure ports 8000 and 5173 are available
2. **Database issues**: Check PostgreSQL is running
3. **Dependencies**: Run setup script if dependencies are missing

### **Logs**
- Backend logs: Check terminal where `start-backend.sh` is running
- Web logs: Check terminal where `start-web.sh` is running
- Database logs: Check PostgreSQL logs

## 📝 **Script Customization**

All scripts can be customized by editing:
- **Environment variables**: Modify `.env` files
- **Ports**: Change port numbers in scripts
- **Paths**: Update paths if folder structure changes

## 🔒 **Security Notes**

- Scripts should be run from the project root
- Ensure proper file permissions
- Review environment variables before production use
- Keep scripts updated with platform changes

---

**Last Updated**: August 8, 2024
**Version**: 1.0.0
