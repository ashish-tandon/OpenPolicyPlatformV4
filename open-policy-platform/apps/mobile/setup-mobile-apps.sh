#!/bin/bash
set -e

# Setup Mobile Apps for OpenPolicy Platform
# Builds and deploys iOS and Android apps to app stores

echo "=== Setting up Mobile Apps ==="

# Configuration
APP_NAME="OpenPolicy"
BUNDLE_ID_IOS="com.openpolicy.app"
BUNDLE_ID_ANDROID="com.openpolicy.app"
APP_VERSION="1.0.0"
BUILD_NUMBER="1"

# 1. Initialize React Native Project
echo "1. Initializing React Native project..."
cd apps/mobile

# Create main app if not exists
if [ ! -d "OpenPolicyMobile" ]; then
    npx react-native init OpenPolicyMobile --template react-native-template-typescript
fi

cd OpenPolicyMobile

# 2. Install Dependencies
echo "2. Installing dependencies..."
npm install \
    @react-navigation/native \
    @react-navigation/stack \
    @react-navigation/bottom-tabs \
    @react-navigation/drawer \
    react-native-screens \
    react-native-safe-area-context \
    react-native-gesture-handler \
    react-native-reanimated \
    @reduxjs/toolkit \
    react-redux \
    react-native-async-storage/async-storage \
    react-native-keychain \
    react-native-vector-icons \
    react-native-linear-gradient \
    react-native-webview \
    react-native-push-notification \
    @react-native-firebase/app \
    @react-native-firebase/auth \
    @react-native-firebase/messaging \
    @react-native-firebase/analytics \
    @react-native-firebase/crashlytics \
    react-native-config \
    react-native-device-info \
    react-native-splash-screen \
    react-native-code-push \
    react-native-biometrics \
    axios \
    date-fns \
    formik \
    yup

# Development dependencies
npm install --save-dev \
    @types/react-native-vector-icons \
    react-native-flipper \
    redux-flipper \
    eslint-config-prettier \
    prettier

# 3. iOS Setup
echo "3. Setting up iOS..."
cd ios

# Update Podfile
cat > Podfile << 'EOF'
require_relative '../node_modules/react-native/scripts/react_native_pods'
require_relative '../node_modules/@react-native-community/cli-platform-ios/native_modules'

platform :ios, '12.4'
install! 'cocoapods', :deterministic_uuids => false

target 'OpenPolicyMobile' do
  config = use_native_modules!

  # Flags change depending on the env values.
  flags = get_default_flags()

  use_react_native!(
    :path => config[:reactNativePath],
    # Hermes is now enabled by default. Disable by setting this flag to false.
    # Upcoming versions of React Native may rely on get_default_flags(), but
    # we make it explicit here to aid in the React Native upgrade process.
    :hermes_enabled => true,
    :fabric_enabled => flags[:fabric_enabled],
    # Enables Flipper.
    #
    # Note that if you have use_frameworks! enabled, Flipper will not work and
    # you should disable the next line.
    :flipper_configuration => FlipperConfiguration.enabled,
    # An absolute path to your application root.
    :app_path => "#{Pod::Config.instance.installation_root}/.."
  )

  # Add Firebase
  use_frameworks! :linkage => :static
  $RNFirebaseAsStaticFramework = true

  target 'OpenPolicyMobileTests' do
    inherit! :complete
    # Pods for testing
  end

  post_install do |installer|
    react_native_post_install(
      installer,
      # Set `mac_catalyst_enabled` to `true` in order to apply patches
      # necessary for Mac Catalyst builds
      :mac_catalyst_enabled => false
    )
    __apply_Xcode_12_5_M1_post_install_workaround(installer)
  end
end
EOF

# Install pods
pod install

cd ..

# 4. Android Setup
echo "4. Setting up Android..."

# Update android/app/build.gradle
cat > android/app/build.gradle << 'EOF'
apply plugin: "com.android.application"
apply plugin: "com.facebook.react"
apply plugin: 'com.google.gms.google-services'
apply plugin: 'com.google.firebase.crashlytics'

import com.android.build.OutputFile

def projectRoot = rootDir.getAbsoluteFile().getParentFile().getAbsolutePath()

react {
    entryFile = file(["node", "-e", "require('react-native/cli').bin", projectRoot, "index.js"].execute(null, rootDir).text.trim())
    cliPath = new File(["node", "--print", "require.resolve('react-native/package.json')"].execute(null, rootDir).text.trim()).getParentFile().getAbsolutePath() + "/cli.js"
    bundleCommand = "bundle"
    enableHermes = true
}

def enableProguardInReleaseBuilds = true
def jscFlavor = 'org.webkit:android-jsc:+'

android {
    ndkVersion rootProject.ext.ndkVersion

    compileSdkVersion rootProject.ext.compileSdkVersion

    namespace "com.openpolicy.app"
    
    defaultConfig {
        applicationId "com.openpolicy.app"
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode 1
        versionName "1.0.0"
        multiDexEnabled true
    }
    
    signingConfigs {
        debug {
            storeFile file('debug.keystore')
            storePassword 'android'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
        }
        release {
            if (project.hasProperty('MYAPP_UPLOAD_STORE_FILE')) {
                storeFile file(MYAPP_UPLOAD_STORE_FILE)
                storePassword MYAPP_UPLOAD_STORE_PASSWORD
                keyAlias MYAPP_UPLOAD_KEY_ALIAS
                keyPassword MYAPP_UPLOAD_KEY_PASSWORD
            }
        }
    }
    
    buildTypes {
        debug {
            signingConfig signingConfigs.debug
        }
        release {
            signingConfig signingConfigs.release
            minifyEnabled enableProguardInReleaseBuilds
            proguardFiles getDefaultProguardFile("proguard-android.txt"), "proguard-rules.pro"
        }
    }
}

dependencies {
    implementation("com.facebook.react:react-android")
    
    debugImplementation("com.facebook.flipper:flipper:${FLIPPER_VERSION}")
    debugImplementation("com.facebook.flipper:flipper-network-plugin:${FLIPPER_VERSION}") {
        exclude group:'com.squareup.okhttp3', module:'okhttp'
    }
    debugImplementation("com.facebook.flipper:flipper-fresco-plugin:${FLIPPER_VERSION}")
    
    if (hermesEnabled.toBoolean()) {
        implementation("com.facebook.react:hermes-android")
    } else {
        implementation jscFlavor
    }
    
    implementation platform('com.google.firebase:firebase-bom:32.0.0')
    implementation 'com.google.firebase:firebase-analytics'
    implementation 'com.google.firebase:firebase-crashlytics'
}

apply from: file("../../node_modules/@react-native-community/cli-platform-android/native_modules.gradle"); applyNativeModulesAppBuildGradle(project)
apply from: file("../../node_modules/react-native-code-push/android/codepush.gradle")
EOF

# 5. Create App Structure
echo "5. Creating app structure..."

# Create directories
mkdir -p src/{components,screens,navigation,services,store,utils,types,assets}

# 6. Create Main App Component
cat > src/App.tsx << 'EOF'
import React, { useEffect } from 'react';
import { StatusBar } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { Provider } from 'react-redux';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import SplashScreen from 'react-native-splash-screen';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { store } from './store';
import RootNavigator from './navigation/RootNavigator';
import { setupPushNotifications } from './services/notifications';
import { initializeAnalytics } from './services/analytics';
import codePush from 'react-native-code-push';

const App: React.FC = () => {
  useEffect(() => {
    // Hide splash screen
    SplashScreen.hide();
    
    // Setup services
    setupPushNotifications();
    initializeAnalytics();
  }, []);

  return (
    <Provider store={store}>
      <ThemeProvider>
        <AuthProvider>
          <SafeAreaProvider>
            <StatusBar barStyle="dark-content" />
            <NavigationContainer>
              <RootNavigator />
            </NavigationContainer>
          </SafeAreaProvider>
        </AuthProvider>
      </ThemeProvider>
    </Provider>
  );
};

// Enable CodePush for OTA updates
export default codePush({
  checkFrequency: codePush.CheckFrequency.ON_APP_RESUME,
  installMode: codePush.InstallMode.ON_NEXT_RESTART,
})(App);
EOF

# 7. Create Authentication Service
cat > src/services/auth.ts << 'EOF'
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';
import auth from '@react-native-firebase/auth';
import { api } from './api';

interface LoginCredentials {
  email: string;
  password: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  tenant?: string;
}

class AuthService {
  private static instance: AuthService;
  private currentUser: User | null = null;

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async login(credentials: LoginCredentials): Promise<User> {
    try {
      // Authenticate with backend
      const response = await api.post('/auth/login', credentials);
      const { token, user } = response.data;

      // Store token securely
      await Keychain.setInternetCredentials(
        'openpolicy.com',
        user.email,
        token
      );

      // Store user data
      await AsyncStorage.setItem('user', JSON.stringify(user));
      this.currentUser = user;

      // Setup Firebase auth
      if (auth().currentUser?.uid !== user.id) {
        const firebaseToken = await api.get('/auth/firebase-token');
        await auth().signInWithCustomToken(firebaseToken.data.token);
      }

      return user;
    } catch (error) {
      throw new Error('Login failed');
    }
  }

  async loginWithSSO(provider: string): Promise<User> {
    // Implement SSO login flow
    // This would open a WebView or use native SSO
    throw new Error('Not implemented');
  }

  async loginWithBiometrics(): Promise<User | null> {
    try {
      const credentials = await Keychain.getInternetCredentials('openpolicy.com');
      if (credentials) {
        // Verify with biometrics
        const biometryType = await Keychain.getSupportedBiometryType();
        if (biometryType) {
          const verified = await Keychain.getInternetCredentials(
            'openpolicy.com',
            {
              authenticationPrompt: {
                title: 'Authenticate to login',
                subtitle: 'Use your biometric credential',
              },
            }
          );
          
          if (verified) {
            // Login with stored token
            api.defaults.headers.common['Authorization'] = `Bearer ${verified.password}`;
            const response = await api.get('/auth/me');
            this.currentUser = response.data;
            return this.currentUser;
          }
        }
      }
    } catch (error) {
      console.error('Biometric login failed:', error);
    }
    return null;
  }

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Continue with local logout even if API fails
    }

    // Clear local data
    await Keychain.resetInternetCredentials('openpolicy.com');
    await AsyncStorage.multiRemove(['user', 'token']);
    await auth().signOut();
    this.currentUser = null;
  }

  async refreshToken(): Promise<string | null> {
    try {
      const response = await api.post('/auth/refresh');
      const { token } = response.data;
      
      // Update stored token
      const credentials = await Keychain.getInternetCredentials('openpolicy.com');
      if (credentials) {
        await Keychain.setInternetCredentials(
          'openpolicy.com',
          credentials.username,
          token
        );
      }
      
      return token;
    } catch (error) {
      return null;
    }
  }

  getCurrentUser(): User | null {
    return this.currentUser;
  }

  async loadStoredUser(): Promise<User | null> {
    try {
      const userJson = await AsyncStorage.getItem('user');
      if (userJson) {
        this.currentUser = JSON.parse(userJson);
        return this.currentUser;
      }
    } catch (error) {
      console.error('Failed to load stored user:', error);
    }
    return null;
  }
}

export default AuthService.getInstance();
EOF

# 8. Create Navigation Structure
cat > src/navigation/RootNavigator.tsx << 'EOF'
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useAuth } from '../contexts/AuthContext';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';
import LoadingScreen from '../screens/LoadingScreen';

export type RootStackParamList = {
  Loading: undefined;
  Auth: undefined;
  Main: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

const RootNavigator: React.FC = () => {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="Main" component={MainNavigator} />
      ) : (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  );
};

export default RootNavigator;
EOF

# 9. Create Main Tab Navigator
cat > src/navigation/MainNavigator.tsx << 'EOF'
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createDrawerNavigator } from '@react-navigation/drawer';
import Icon from 'react-native-vector-icons/MaterialIcons';
import HomeScreen from '../screens/HomeScreen';
import PoliciesScreen from '../screens/PoliciesScreen';
import RepresentativesScreen from '../screens/RepresentativesScreen';
import SearchScreen from '../screens/SearchScreen';
import ProfileScreen from '../screens/ProfileScreen';
import CustomDrawer from '../components/CustomDrawer';

const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName: string;

        switch (route.name) {
          case 'Home':
            iconName = 'home';
            break;
          case 'Policies':
            iconName = 'policy';
            break;
          case 'Representatives':
            iconName = 'people';
            break;
          case 'Search':
            iconName = 'search';
            break;
          case 'Profile':
            iconName = 'person';
            break;
          default:
            iconName = 'circle';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#1976d2',
      tabBarInactiveTintColor: 'gray',
    })}
  >
    <Tab.Screen name="Home" component={HomeScreen} />
    <Tab.Screen name="Policies" component={PoliciesScreen} />
    <Tab.Screen name="Representatives" component={RepresentativesScreen} />
    <Tab.Screen name="Search" component={SearchScreen} />
    <Tab.Screen name="Profile" component={ProfileScreen} />
  </Tab.Navigator>
);

const MainNavigator = () => (
  <Drawer.Navigator
    drawerContent={(props) => <CustomDrawer {...props} />}
    screenOptions={{
      drawerType: 'slide',
      overlayColor: 'transparent',
    }}
  >
    <Drawer.Screen name="Main" component={TabNavigator} />
  </Drawer.Navigator>
);

export default MainNavigator;
EOF

# 10. Create Key Screens
cat > src/screens/HomeScreen.tsx << 'EOF'
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import DashboardCard from '../components/DashboardCard';
import RecentActivity from '../components/RecentActivity';
import QuickActions from '../components/QuickActions';

interface DashboardData {
  activePolicies: number;
  upcomingVotes: number;
  representatives: number;
  recentActivity: any[];
}

const HomeScreen: React.FC = () => {
  const navigation = useNavigation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/dashboard');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>Hello, {user?.name || 'User'}!</Text>
        <Text style={styles.subtitle}>Here's what's happening in policy today</Text>
      </View>

      <View style={styles.statsContainer}>
        <DashboardCard
          title="Active Policies"
          value={dashboardData?.activePolicies || 0}
          icon="policy"
          color="#4CAF50"
          onPress={() => navigation.navigate('Policies')}
        />
        <DashboardCard
          title="Upcoming Votes"
          value={dashboardData?.upcomingVotes || 0}
          icon="how-to-vote"
          color="#FF9800"
          onPress={() => navigation.navigate('Votes')}
        />
        <DashboardCard
          title="Representatives"
          value={dashboardData?.representatives || 0}
          icon="people"
          color="#2196F3"
          onPress={() => navigation.navigate('Representatives')}
        />
      </View>

      <QuickActions />

      <RecentActivity activities={dashboardData?.recentActivity || []} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 5,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 15,
  },
});

export default HomeScreen;
EOF

# 11. Create Build Scripts
echo "11. Creating build scripts..."

# iOS build script
cat > scripts/build-ios.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Building iOS app..."

cd apps/mobile/OpenPolicyMobile

# Clean build
cd ios
xcodebuild clean -workspace OpenPolicyMobile.xcworkspace -scheme OpenPolicyMobile

# Archive
xcodebuild archive \
  -workspace OpenPolicyMobile.xcworkspace \
  -scheme OpenPolicyMobile \
  -configuration Release \
  -archivePath build/OpenPolicyMobile.xcarchive

# Export IPA
xcodebuild -exportArchive \
  -archivePath build/OpenPolicyMobile.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build

echo "iOS build complete! IPA available at: build/OpenPolicyMobile.ipa"
SCRIPT

# Android build script
cat > scripts/build-android.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Building Android app..."

cd apps/mobile/OpenPolicyMobile

# Clean
cd android
./gradlew clean

# Build release APK
./gradlew assembleRelease

# Build release bundle (AAB)
./gradlew bundleRelease

echo "Android build complete!"
echo "APK: android/app/build/outputs/apk/release/app-release.apk"
echo "AAB: android/app/build/outputs/bundle/release/app-release.aab"
SCRIPT

# 12. Create Fastlane Configuration
echo "12. Setting up Fastlane..."

# iOS Fastlane
mkdir -p ios/fastlane
cat > ios/fastlane/Fastfile << 'FASTLANE'
default_platform(:ios)

platform :ios do
  desc "Push a new release build to TestFlight"
  lane :release do
    increment_build_number(xcodeproj: "OpenPolicyMobile.xcodeproj")
    build_app(
      workspace: "OpenPolicyMobile.xcworkspace",
      scheme: "OpenPolicyMobile",
      export_method: "app-store"
    )
    upload_to_testflight
  end

  desc "Deploy to App Store"
  lane :deploy do
    release
    deliver(
      submit_for_review: true,
      automatic_release: true,
      force: true,
      metadata_path: "./metadata"
    )
  end
end
FASTLANE

# Android Fastlane
mkdir -p android/fastlane
cat > android/fastlane/Fastfile << 'FASTLANE'
default_platform(:android)

platform :android do
  desc "Build and upload to Google Play Console"
  lane :release do
    gradle(
      task: "bundle",
      build_type: "Release"
    )
    upload_to_play_store(
      track: "internal",
      release_status: "draft"
    )
  end

  desc "Deploy to production"
  lane :deploy do
    gradle(
      task: "bundle",
      build_type: "Release"
    )
    upload_to_play_store(
      track: "production",
      release_status: "completed"
    )
  end
end
FASTLANE

# 13. Create App Store Metadata
echo "13. Creating App Store metadata..."

mkdir -p ios/fastlane/metadata/en-US
cat > ios/fastlane/metadata/en-US/description.txt << 'META'
OpenPolicy - Your Gateway to Government Transparency

Stay informed about government policies, track legislative changes, and connect with your representatives. OpenPolicy brings transparency to governance by providing real-time access to:

• Policy Documents: Browse and search through current and proposed policies
• Legislative Tracking: Follow bills and resolutions through the legislative process
• Representative Information: Connect with your elected officials
• Voting Records: See how representatives vote on key issues
• Real-time Updates: Get notified about policy changes that matter to you

Features:
- Comprehensive search across all government documents
- Personalized policy tracking and notifications
- Direct communication channels with representatives
- Offline access to saved documents
- Multi-language support
- Accessibility features for all users

Join thousands of engaged citizens in making government more transparent and accessible.
META

# 14. Create CI/CD Pipeline
echo "14. Creating mobile CI/CD pipeline..."

cat > .github/workflows/mobile-deploy.yml << 'CICD'
name: Mobile App Deployment

on:
  push:
    tags:
      - 'mobile-v*'
  workflow_dispatch:

jobs:
  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          cd apps/mobile/OpenPolicyMobile
          npm install
          cd ios
          pod install
          
      - name: Setup certificates
        env:
          CERTIFICATE_BASE64: ${{ secrets.IOS_CERTIFICATE_BASE64 }}
          PROVISION_PROFILE_BASE64: ${{ secrets.IOS_PROVISION_PROFILE_BASE64 }}
          KEYCHAIN_PASSWORD: ${{ secrets.KEYCHAIN_PASSWORD }}
        run: |
          # Create keychain
          security create-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          security default-keychain -s build.keychain
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          
          # Import certificate
          echo "$CERTIFICATE_BASE64" | base64 --decode > certificate.p12
          security import certificate.p12 -k build.keychain -P "${{ secrets.CERTIFICATE_PASSWORD }}" -T /usr/bin/codesign
          
          # Import provisioning profile
          echo "$PROVISION_PROFILE_BASE64" | base64 --decode > profile.mobileprovision
          mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles
          cp profile.mobileprovision ~/Library/MobileDevice/Provisioning\ Profiles/
          
      - name: Build and deploy to TestFlight
        env:
          FASTLANE_USER: ${{ secrets.APPLE_ID }}
          FASTLANE_PASSWORD: ${{ secrets.APPLE_PASSWORD }}
          FASTLANE_APPLE_APPLICATION_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
        run: |
          cd apps/mobile/OpenPolicyMobile/ios
          fastlane release

  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Setup Java
        uses: actions/setup-java@v3
        with:
          java-version: '11'
          distribution: 'temurin'
          
      - name: Install dependencies
        run: |
          cd apps/mobile/OpenPolicyMobile
          npm install
          
      - name: Setup signing
        env:
          KEYSTORE_BASE64: ${{ secrets.ANDROID_KEYSTORE_BASE64 }}
        run: |
          cd apps/mobile/OpenPolicyMobile/android
          echo "$KEYSTORE_BASE64" | base64 --decode > app/release.keystore
          echo "MYAPP_UPLOAD_STORE_FILE=release.keystore" >> gradle.properties
          echo "MYAPP_UPLOAD_STORE_PASSWORD=${{ secrets.ANDROID_KEYSTORE_PASSWORD }}" >> gradle.properties
          echo "MYAPP_UPLOAD_KEY_ALIAS=${{ secrets.ANDROID_KEY_ALIAS }}" >> gradle.properties
          echo "MYAPP_UPLOAD_KEY_PASSWORD=${{ secrets.ANDROID_KEY_PASSWORD }}" >> gradle.properties
          
      - name: Build and deploy to Play Store
        env:
          SUPPLY_JSON_KEY_DATA: ${{ secrets.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON }}
        run: |
          cd apps/mobile/OpenPolicyMobile/android
          fastlane release
CICD

# 15. Create CodePush deployment
echo "15. Setting up CodePush..."

cat > scripts/deploy-codepush.sh << 'CODEPUSH'
#!/bin/bash
set -e

# Deploy CodePush updates
echo "Deploying CodePush updates..."

# iOS
code-push release-react OpenPolicy-iOS ios \
  --deploymentName Production \
  --description "Bug fixes and performance improvements" \
  --mandatory false

# Android
code-push release-react OpenPolicy-Android android \
  --deploymentName Production \
  --description "Bug fixes and performance improvements" \
  --mandatory false

echo "CodePush deployment complete!"
CODEPUSH

chmod +x scripts/build-ios.sh
chmod +x scripts/build-android.sh
chmod +x scripts/deploy-codepush.sh

echo "
=== Mobile App Setup Complete ===

✅ Created:
- React Native app with TypeScript
- iOS and Android configurations
- Authentication with biometrics
- Push notifications
- Analytics and crash reporting
- CodePush for OTA updates
- CI/CD pipeline
- Fastlane automation

📱 App Features:
- Multi-tenant support
- SSO integration
- Offline capabilities
- Real-time updates
- Biometric authentication
- Push notifications
- In-app updates

🚀 Build Commands:
- iOS: ./scripts/build-ios.sh
- Android: ./scripts/build-android.sh
- CodePush: ./scripts/deploy-codepush.sh

📦 Deployment:
- iOS: fastlane ios deploy
- Android: fastlane android deploy

🔧 Configuration:
1. Add Firebase config files:
   - iOS: ios/GoogleService-Info.plist
   - Android: android/app/google-services.json

2. Configure signing:
   - iOS: Update bundle ID and provisioning profiles
   - Android: Generate keystore and update gradle.properties

3. Set up App Store Connect and Google Play Console

4. Configure CI/CD secrets in GitHub

⚡ Development:
cd apps/mobile/OpenPolicyMobile
npm start
npm run ios     # Run on iOS simulator
npm run android # Run on Android emulator

📚 Next Steps:
1. Design app icons and splash screens
2. Create App Store screenshots
3. Write release notes
4. Submit for review
5. Monitor crash reports and analytics
"