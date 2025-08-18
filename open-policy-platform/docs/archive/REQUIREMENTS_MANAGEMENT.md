# 📦 Requirements Management - OpenPolicy Merge

## 🎯 **CENTRALIZED REQUIREMENTS APPROACH**

This document outlines the **best practice approach** for managing dependencies in the OpenPolicy Merge platform, consolidating requirements from multiple merged repositories into a single, well-organized system.

---

## 📋 **REQUIREMENTS STRATEGY**

### **Why Centralized Requirements?**

✅ **Single Source of Truth**: One `requirements.txt` file for the entire project
✅ **Version Compatibility**: Ensures all components work together
✅ **Easy Installation**: Simple `pip install -r requirements.txt`
✅ **Development/Production Separation**: Optional dependencies for different environments
✅ **Best Practice Compliance**: Follows Python packaging standards

### **Before vs After**

**❌ Before (Multiple Files)**:
```
backend/requirements.txt
scrapers/requirements.txt
openparliament/requirements.txt
civic-scraper/requirements.txt
mobile/package.json
web/package.json
```

**✅ After (Centralized)**:
```
requirements.txt                    # Main Python dependencies
package.json                       # Node.js dependencies (if needed)
REQUIREMENTS_MANAGEMENT.md         # This documentation
```

---

## 🏗️ **REQUIREMENTS STRUCTURE**

### **Main Requirements File**: `requirements.txt`

The centralized `requirements.txt` is organized into logical sections:

```python
# =============================================================================
# CORE FRAMEWORK DEPENDENCIES
# =============================================================================
fastapi>=0.104.0
sqlalchemy>=2.0.0
# ... core dependencies

# =============================================================================
# SCRAPING & DATA COLLECTION
# =============================================================================
requests>=2.31.0
pupa>=2.4.0
# ... scraping dependencies

# =============================================================================
# MONITORING & BACKGROUND TASKS
# =============================================================================
celery>=5.3.0
psutil>=5.9.0
# ... monitoring dependencies

# =============================================================================
# DEVELOPMENT & TESTING
# =============================================================================
pytest>=7.4.0
black>=23.11.0
# ... development dependencies

# =============================================================================
# OPTIONAL DEPENDENCIES
# =============================================================================
[dev]
jupyter>=1.0.0
# ... development-only dependencies

[prod]
gunicorn>=21.2.0
# ... production-only dependencies
```

---

## 🚀 **INSTALLATION METHODS**

### **1. Basic Installation**
```bash
# Install all core dependencies
pip install -r requirements.txt
```

### **2. Development Installation**
```bash
# Install core + development dependencies
pip install -r requirements.txt[dev]
```

### **3. Production Installation**
```bash
# Install core + production dependencies
pip install -r requirements.txt[prod]
```

### **4. Virtual Environment Setup**
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📊 **DEPENDENCY CATEGORIES**

### **Core Framework Dependencies**
- **FastAPI**: Modern web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### **Scraping & Data Collection**
- **Requests**: HTTP client
- **BeautifulSoup4**: HTML parsing
- **Pupa**: OpenCivicData framework
- **Pandas**: Data processing

### **Monitoring & Background Tasks**
- **Celery**: Task queue
- **Redis**: Message broker
- **Psutil**: System monitoring
- **Schedule**: Task scheduling

### **Authentication & Security**
- **Python-Jose**: JWT tokens
- **Passlib**: Password hashing
- **Cryptography**: Encryption

### **Development & Testing**
- **Pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking

---

## 🔧 **MANAGEMENT WORKFLOW**

### **Adding New Dependencies**

1. **Identify Category**: Determine which section the dependency belongs to
2. **Add to requirements.txt**: Add with appropriate version constraint
3. **Update Documentation**: Document the addition here
4. **Test Installation**: Verify it works in all environments

### **Updating Dependencies**

1. **Check Compatibility**: Ensure new versions work together
2. **Update Version Constraints**: Modify version numbers in requirements.txt
3. **Test Thoroughly**: Run tests to ensure nothing breaks
4. **Update Documentation**: Reflect changes in this document

### **Removing Dependencies**

1. **Check Usage**: Ensure the dependency is not used anywhere
2. **Remove from requirements.txt**: Delete the line
3. **Clean Up**: Remove any related configuration
4. **Test**: Verify the system still works

---

## 📁 **LEGACY REPOSITORY INTEGRATION**

### **Merged Repository Dependencies**

The centralized requirements file includes dependencies from all merged repositories:

| Repository | Dependencies | Status |
|------------|--------------|--------|
| **OpenPolicyAshBack** | FastAPI, SQLAlchemy, Celery | ✅ Integrated |
| **openparliament** | Django, DRF | ✅ Integrated |
| **scrapers-ca** | Pupa, OpenCivicData | ✅ Integrated |
| **civic-scraper** | Scrapy, BeautifulSoup | ✅ Integrated |
| **admin-open-policy** | React, TypeScript | 📦 Separate (Node.js) |

### **Node.js Dependencies**

For frontend components, maintain separate `package.json` files:

```bash
# Web frontend
cd web/
npm install

# Mobile app
cd mobile/open-policy-app/
npm install

# Admin interface
cd mobile/admin-open-policy/
npm install
```

---

## 🛠️ **ENVIRONMENT-SPECIFIC REQUIREMENTS**

### **Development Environment**
```bash
# Install development dependencies
pip install -r requirements.txt[dev]

# Additional development tools
pip install ipython jupyter debugpy
```

### **Production Environment**
```bash
# Install production dependencies
pip install -r requirements.txt[prod]

# Additional production tools
pip install gunicorn supervisor
```

### **Testing Environment**
```bash
# Install testing dependencies (included in [dev])
pip install -r requirements.txt[dev]

# Run tests
pytest tests/
```

---

## 🔍 **DEPENDENCY ANALYSIS**

### **Dependency Graph**
```
OpenPolicy Merge Platform
├── Core Framework
│   ├── FastAPI (Web API)
│   ├── SQLAlchemy (Database)
│   └── Pydantic (Validation)
├── Scraping System
│   ├── Pupa (OpenCivicData)
│   ├── Requests (HTTP)
│   └── BeautifulSoup (Parsing)
├── Monitoring
│   ├── Celery (Tasks)
│   ├── Redis (Broker)
│   └── Psutil (System)
└── Development
    ├── Pytest (Testing)
    ├── Black (Formatting)
    └── Flake8 (Linting)
```

### **Version Compatibility Matrix**

| Component | Version | Compatible With |
|-----------|---------|-----------------|
| FastAPI | >=0.104.0 | Python 3.8+ |
| SQLAlchemy | >=2.0.0 | PostgreSQL 12+ |
| Pupa | >=2.4.0 | OpenCivicData 3.0+ |
| Celery | >=5.3.0 | Redis 6.0+ |

---

## 📋 **MAINTENANCE CHECKLIST**

### **Monthly Maintenance**
- [ ] Check for security updates
- [ ] Review dependency usage
- [ ] Update version constraints
- [ ] Test compatibility

### **Quarterly Review**
- [ ] Audit unused dependencies
- [ ] Update major versions
- [ ] Review performance impact
- [ ] Update documentation

### **Before Releases**
- [ ] Lock dependency versions
- [ ] Test all environments
- [ ] Update changelog
- [ ] Verify installation

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues**

**1. Version Conflicts**
```bash
# Check for conflicts
pip check

# Resolve conflicts
pip install --upgrade package-name
```

**2. Missing Dependencies**
```bash
# Install missing packages
pip install -r requirements.txt --force-reinstall
```

**3. Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Getting Help**

- **Documentation**: Check this file first
- **Issues**: Review GitHub issues
- **Community**: Check project discussions
- **Logs**: Review installation logs

---

## 📚 **BEST PRACTICES**

### **Version Management**
- ✅ Use `>=` for minimum versions
- ✅ Pin critical dependencies with `==`
- ✅ Use `~=` for patch-level updates
- ✅ Document version constraints

### **Security**
- ✅ Regular security updates
- ✅ Vulnerability scanning
- ✅ Dependency auditing
- ✅ Secure installation methods

### **Performance**
- ✅ Minimal dependencies
- ✅ Efficient package selection
- ✅ Regular cleanup
- ✅ Performance monitoring

---

## 🎯 **SUCCESS METRICS**

### **Management Goals**
- ✅ **Single requirements file** for entire project
- ✅ **Zero dependency conflicts** across components
- ✅ **Fast installation** (<5 minutes)
- ✅ **Comprehensive coverage** of all features
- ✅ **Easy maintenance** and updates

### **Quality Indicators**
- ✅ **100% test coverage** with installed dependencies
- ✅ **Zero security vulnerabilities** in dependencies
- ✅ **Consistent behavior** across environments
- ✅ **Clear documentation** for all dependencies

---

## 🚀 **NEXT STEPS**

### **Immediate Actions**
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Test Installation**: Run basic functionality tests
3. **Verify Compatibility**: Ensure all components work together
4. **Document Issues**: Report any problems

### **Ongoing Maintenance**
1. **Regular Updates**: Monthly dependency reviews
2. **Security Audits**: Quarterly security checks
3. **Performance Monitoring**: Track dependency impact
4. **Documentation Updates**: Keep this guide current

---

## 📞 **SUPPORT**

For questions about requirements management:
- **Documentation**: This file
- **Issues**: GitHub project issues
- **Discussions**: Project discussions
- **Maintainers**: Project maintainers

**Remember**: The goal is to have a **single, well-organized, maintainable** requirements system that serves the entire OpenPolicy Merge platform! 🎯
