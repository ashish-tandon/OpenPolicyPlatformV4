import messaging from '@react-native-firebase/messaging';
import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { api } from './api';

class NotificationService {
  private static instance: NotificationService;

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  async initialize() {
    // Configure local notifications
    PushNotification.configure({
      onRegister: (token) => {
        console.log('FCM Token:', token);
        this.registerDeviceToken(token.token);
      },

      onNotification: (notification) => {
        console.log('Notification received:', notification);
        this.handleNotification(notification);
      },

      onAction: (notification) => {
        console.log('Notification action:', notification.action);
        this.handleNotificationAction(notification);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: true,
    });

    // Create notification channels for Android
    if (Platform.OS === 'android') {
      this.createNotificationChannels();
    }

    // Request permission for iOS
    if (Platform.OS === 'ios') {
      await this.requestIOSPermission();
    }

    // Handle background messages
    messaging().setBackgroundMessageHandler(this.handleBackgroundMessage);

    // Handle foreground messages
    messaging().onMessage(this.handleForegroundMessage);

    // Handle notification opened app
    messaging().onNotificationOpenedApp(this.handleNotificationOpened);

    // Check if app was opened from notification
    const initialNotification = await messaging().getInitialNotification();
    if (initialNotification) {
      this.handleNotificationOpened(initialNotification);
    }
  }

  private async requestIOSPermission() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log('iOS notification permission granted');
    }
  }

  private createNotificationChannels() {
    PushNotification.createChannel(
      {
        channelId: 'policy-updates',
        channelName: 'Policy Updates',
        channelDescription: 'Notifications about policy changes and updates',
        importance: 4,
        vibrate: true,
      },
      (created) => console.log(`Policy updates channel created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'votes',
        channelName: 'Voting Notifications',
        channelDescription: 'Notifications about upcoming votes',
        importance: 5,
        vibrate: true,
      },
      (created) => console.log(`Votes channel created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'representatives',
        channelName: 'Representative Updates',
        channelDescription: 'Updates from your representatives',
        importance: 3,
        vibrate: true,
      },
      (created) => console.log(`Representatives channel created: ${created}`)
    );

    PushNotification.createChannel(
      {
        channelId: 'general',
        channelName: 'General Notifications',
        channelDescription: 'General app notifications',
        importance: 3,
        vibrate: false,
      },
      (created) => console.log(`General channel created: ${created}`)
    );
  }

  private async registerDeviceToken(token: string) {
    try {
      // Save token locally
      await AsyncStorage.setItem('fcm_token', token);

      // Register with backend
      await api.post('/notifications/register', {
        token,
        platform: Platform.OS,
        device_info: {
          os_version: Platform.Version,
          app_version: '1.0.0', // Get from DeviceInfo
        },
      });
    } catch (error) {
      console.error('Failed to register device token:', error);
    }
  }

  private handleNotification(notification: any) {
    // Handle notification based on type
    const { data } = notification;

    if (data?.type === 'policy_update') {
      this.handlePolicyUpdate(data);
    } else if (data?.type === 'vote_reminder') {
      this.handleVoteReminder(data);
    } else if (data?.type === 'representative_message') {
      this.handleRepresentativeMessage(data);
    }

    // Update badge count
    this.updateBadgeCount();
  }

  private handleNotificationAction(notification: any) {
    const { action, data } = notification;

    switch (action) {
      case 'view':
        // Navigate to relevant screen
        this.navigateToContent(data);
        break;
      case 'dismiss':
        // Mark as read
        this.markAsRead(data.notification_id);
        break;
      default:
        break;
    }
  }

  private async handleBackgroundMessage(remoteMessage: any) {
    console.log('Background message:', remoteMessage);

    // Process background message
    const { data, notification } = remoteMessage;

    // Show local notification
    PushNotification.localNotification({
      channelId: data.channel || 'general',
      title: notification.title,
      message: notification.body,
      data: data,
      userInfo: data,
      playSound: true,
      vibrate: true,
    });
  }

  private async handleForegroundMessage(remoteMessage: any) {
    console.log('Foreground message:', remoteMessage);

    const { data, notification } = remoteMessage;

    // Show in-app notification
    PushNotification.localNotification({
      channelId: data.channel || 'general',
      title: notification.title,
      message: notification.body,
      data: data,
      userInfo: data,
      playSound: false,
      vibrate: false,
    });
  }

  private async handleNotificationOpened(remoteMessage: any) {
    console.log('Notification opened:', remoteMessage);

    const { data } = remoteMessage;
    this.navigateToContent(data);
  }

  private handlePolicyUpdate(data: any) {
    // Handle policy update notification
    console.log('Policy update:', data);
  }

  private handleVoteReminder(data: any) {
    // Handle vote reminder notification
    console.log('Vote reminder:', data);
  }

  private handleRepresentativeMessage(data: any) {
    // Handle representative message notification
    console.log('Representative message:', data);
  }

  private navigateToContent(data: any) {
    // Navigate to appropriate screen based on notification data
    // This would integrate with your navigation system
    console.log('Navigate to:', data);
  }

  private async markAsRead(notificationId: string) {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      this.updateBadgeCount();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }

  private async updateBadgeCount() {
    try {
      const response = await api.get('/notifications/unread-count');
      const count = response.data.count || 0;
      PushNotification.setApplicationIconBadgeNumber(count);
    } catch (error) {
      console.error('Failed to update badge count:', error);
    }
  }

  // Public methods
  async scheduleLocalNotification(
    title: string,
    message: string,
    date: Date,
    data?: any
  ) {
    PushNotification.localNotificationSchedule({
      channelId: 'general',
      title,
      message,
      date,
      data,
      userInfo: data,
    });
  }

  async cancelAllNotifications() {
    PushNotification.cancelAllLocalNotifications();
  }

  async getScheduledNotifications(): Promise<any[]> {
    return new Promise((resolve) => {
      PushNotification.getScheduledLocalNotifications((notifications) => {
        resolve(notifications);
      });
    });
  }

  async updateNotificationSettings(settings: any) {
    try {
      await api.put('/notifications/settings', settings);
    } catch (error) {
      console.error('Failed to update notification settings:', error);
    }
  }
}

export const setupPushNotifications = async () => {
  const notificationService = NotificationService.getInstance();
  await notificationService.initialize();
};

export default NotificationService.getInstance();