# 📱 Open Policy Platform - Mobile Applications

This directory contains the mobile applications for the Open Policy Platform, preserved for future development.

## 📱 **Mobile Applications**

### **open-policy-main/**
- **Type**: React Native (Expo)
- **Purpose**: Main mobile application
- **Status**: Preserved for future development
- **Technology**: React Native, Expo, TypeScript

### **open-policy-app/**
- **Type**: React Native Components
- **Purpose**: Reusable mobile components
- **Status**: Preserved for future development
- **Technology**: React Native, TypeScript

### **admin-open-policy/**
- **Type**: React Native Admin Interface
- **Purpose**: Mobile admin interface
- **Status**: Preserved for future development
- **Technology**: React Native, TypeScript

### **open-policy-web/**
- **Type**: React Web Application
- **Purpose**: Web interface (moved from apps/)
- **Status**: Integrated into main web application
- **Technology**: React, TypeScript, Vite

## 🚀 **Future Development**

### **Planned Features**
- **Cross-platform mobile app** for policy browsing
- **Offline capability** for policy data
- **Push notifications** for policy updates
- **Mobile-optimized** admin interface
- **Native features** integration

### **Development Timeline**
- **Phase 1**: Basic mobile app structure
- **Phase 2**: Policy browsing interface
- **Phase 3**: Offline functionality
- **Phase 4**: Advanced features

## 🔧 **Technology Stack**

### **React Native**
- **Framework**: React Native with Expo
- **Language**: TypeScript
- **Styling**: NativeWind (Tailwind CSS for React Native)
- **Navigation**: React Navigation
- **State Management**: React Context + Hooks

### **Development Tools**
- **Expo CLI**: Development and building
- **Metro**: JavaScript bundler
- **TypeScript**: Type safety
- **ESLint**: Code quality

## 📋 **Setup Instructions**

### **Prerequisites**
- Node.js 18+
- Expo CLI
- iOS Simulator (macOS) or Android Emulator

### **Installation**
```bash
# Install Expo CLI
npm install -g @expo/cli

# Navigate to mobile app
cd mobile/open-policy-main

# Install dependencies
npm install

# Start development server
npx expo start
```

### **Development**
```bash
# Start with iOS simulator
npx expo start --ios

# Start with Android emulator
npx expo start --android

# Start with web browser
npx expo start --web
```

## 📱 **App Structure**

### **open-policy-main/**
```
src/
├── components/          # Reusable components
├── screens/            # Screen components
├── navigation/         # Navigation configuration
├── services/           # API services
├── hooks/              # Custom hooks
├── utils/              # Utility functions
└── types/              # TypeScript types
```

### **open-policy-app/**
```
src/
├── components/         # Shared components
├── hooks/              # Custom hooks
├── utils/              # Utility functions
└── types/              # TypeScript types
```

## 🔗 **Integration**

### **API Integration**
- **Backend API**: Connects to unified backend
- **Authentication**: JWT-based authentication
- **Real-time updates**: WebSocket integration
- **Offline sync**: Local storage + sync

### **Web Integration**
- **Shared components** with web application
- **Consistent design** language
- **Unified API** access
- **Cross-platform** functionality

## 📊 **Features**

### **Current Features**
- **Basic structure** preserved
- **Component library** ready
- **Navigation setup** complete
- **TypeScript** configuration

### **Planned Features**
- **Policy browsing** interface
- **Search functionality** with filters
- **Favorites and bookmarks**
- **Offline reading** capability
- **Push notifications**
- **Admin interface** for mobile

## 🛠️ **Development Guidelines**

### **Code Standards**
- **TypeScript**: Strict type checking
- **ESLint**: Code quality enforcement
- **Prettier**: Code formatting
- **Testing**: Unit and integration tests

### **Component Guidelines**
- **Reusable components** in open-policy-app
- **Screen-specific components** in open-policy-main
- **Consistent styling** with NativeWind
- **Accessibility** compliance

## 📈 **Roadmap**

### **Q1 2024**
- [ ] Basic mobile app structure
- [ ] Policy browsing interface
- [ ] Authentication integration

### **Q2 2024**
- [ ] Offline functionality
- [ ] Search and filtering
- [ ] Push notifications

### **Q3 2024**
- [ ] Advanced features
- [ ] Performance optimization
- [ ] Production deployment

## 🔒 **Security**

### **Mobile Security**
- **Secure storage** for sensitive data
- **Certificate pinning** for API calls
- **Biometric authentication** support
- **Data encryption** for offline storage

## 📞 **Support**

For mobile development questions:
1. Check the [Development Guide](../docs/development/setup.md)
2. Review [API Documentation](../docs/api/overview.md)
3. Consult React Native and Expo documentation

---

**Last Updated**: August 8, 2024
**Version**: 1.0.0
**Status**: Preserved for Future Development
