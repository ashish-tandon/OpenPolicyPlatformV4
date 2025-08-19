import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  IconButton,
  Badge,
  Popover,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Divider,
  Button,
  Stack,
  Tabs,
  Tab,
  Chip,
  CircularProgress,
  useTheme,
  alpha,
  Fade,
  Collapse,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Notifications,
  NotificationsActive,
  NotificationsOff,
  Info,
  CheckCircle,
  Warning,
  Error,
  Policy,
  Gavel,
  People,
  TrendingUp,
  Close,
  DoneAll,
  Settings,
  VolumeUp,
  VolumeOff,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'policy' | 'bill' | 'update';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
}

interface NotificationPreferences {
  sound: boolean;
  desktop: boolean;
  email: boolean;
  categories: {
    policy: boolean;
    bills: boolean;
    updates: boolean;
    system: boolean;
  };
}

const NotificationCenter: React.FC = () => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedTab, setSelectedTab] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    sound: true,
    desktop: true,
    email: false,
    categories: {
      policy: true,
      bills: true,
      updates: true,
      system: true,
    },
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Mock notifications for demo
  useEffect(() => {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'policy',
        title: 'New Policy Published',
        message: 'Healthcare Reform Act 2024 has been published and is now available for review.',
        timestamp: new Date(Date.now() - 1000 * 60 * 5),
        read: false,
        actionUrl: '/policies/healthcare-reform-2024',
        actionLabel: 'View Policy',
        category: 'policy',
        priority: 'high',
      },
      {
        id: '2',
        type: 'success',
        title: 'Analysis Complete',
        message: 'Your requested policy analysis has been completed successfully.',
        timestamp: new Date(Date.now() - 1000 * 60 * 30),
        read: false,
        category: 'system',
        priority: 'medium',
      },
      {
        id: '3',
        type: 'bill',
        title: 'Bill Status Update',
        message: 'Bill C-45 has moved to second reading in Parliament.',
        timestamp: new Date(Date.now() - 1000 * 60 * 60),
        read: true,
        actionUrl: '/bills/c-45',
        actionLabel: 'Track Bill',
        category: 'bills',
        priority: 'medium',
      },
      {
        id: '4',
        type: 'warning',
        title: 'Upcoming Maintenance',
        message: 'Platform maintenance scheduled for tomorrow at 2:00 AM EST.',
        timestamp: new Date(Date.now() - 1000 * 60 * 120),
        read: true,
        category: 'system',
        priority: 'low',
      },
    ];
    
    setNotifications(mockNotifications);
    setUnreadCount(mockNotifications.filter(n => !n.read).length);
  }, []);

  // WebSocket connection
  useEffect(() => {
    // Connect to WebSocket
    // wsRef.current = new WebSocket('ws://localhost:9000/notifications');
    
    // wsRef.current.onmessage = (event) => {
    //   const notification = JSON.parse(event.data);
    //   handleNewNotification(notification);
    // };
    
    return () => {
      // wsRef.current?.close();
    };
  }, []);

  const handleNewNotification = (notification: Notification) => {
    // Check preferences
    if (!preferences.categories[notification.category as keyof typeof preferences.categories]) {
      return;
    }
    
    // Add notification
    setNotifications(prev => [notification, ...prev]);
    setUnreadCount(prev => prev + 1);
    
    // Play sound
    if (preferences.sound) {
      audioRef.current?.play();
    }
    
    // Show desktop notification
    if (preferences.desktop && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
      });
    }
  };

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setShowSettings(false);
  };

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n))
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const handleClearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const handleAction = (notification: Notification) => {
    handleMarkAsRead(notification.id);
    if (notification.actionUrl) {
      // Navigate to action URL
      window.location.href = notification.actionUrl;
    }
    handleClose();
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setPreferences(prev => ({ ...prev, desktop: true }));
      }
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <Info />;
      case 'success':
        return <CheckCircle />;
      case 'warning':
        return <Warning />;
      case 'error':
        return <Error />;
      case 'policy':
        return <Policy />;
      case 'bill':
        return <Gavel />;
      case 'update':
        return <TrendingUp />;
      default:
        return <Info />;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'info':
        return theme.palette.info.main;
      case 'success':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'error':
        return theme.palette.error.main;
      case 'policy':
        return theme.palette.primary.main;
      case 'bill':
        return theme.palette.secondary.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const filteredNotifications = notifications.filter(notification => {
    if (selectedTab === 0) return true; // All
    if (selectedTab === 1) return !notification.read; // Unread
    if (selectedTab === 2) return notification.priority === 'high'; // Important
    return true;
  });

  const open = Boolean(anchorEl);

  return (
    <>
      <IconButton
        onClick={handleClick}
        sx={{
          color: unreadCount > 0 ? theme.palette.primary.main : 'inherit',
        }}
      >
        <Badge
          badgeContent={unreadCount}
          color="error"
          overlap="circular"
          sx={{
            '& .MuiBadge-badge': {
              animation: unreadCount > 0 ? 'pulse 2s infinite' : 'none',
            },
          }}
        >
          {unreadCount > 0 ? <NotificationsActive /> : <Notifications />}
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            width: 420,
            maxHeight: 600,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <AnimatePresence mode="wait">
          {!showSettings ? (
            <motion.div
              key="notifications"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
            >
              {/* Header */}
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">Notifications</Typography>
                  <Stack direction="row" spacing={1}>
                    <IconButton size="small" onClick={() => setShowSettings(true)}>
                      <Settings fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={handleClose}>
                      <Close fontSize="small" />
                    </IconButton>
                  </Stack>
                </Stack>
              </Box>

              {/* Tabs */}
              <Tabs
                value={selectedTab}
                onChange={(e, newValue) => setSelectedTab(newValue)}
                sx={{ borderBottom: 1, borderColor: 'divider' }}
              >
                <Tab label={`All (${notifications.length})`} />
                <Tab label={`Unread (${unreadCount})`} />
                <Tab label="Important" />
              </Tabs>

              {/* Actions */}
              {filteredNotifications.length > 0 && (
                <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
                  <Stack direction="row" justifyContent="flex-end" spacing={1}>
                    <Button
                      size="small"
                      startIcon={<DoneAll />}
                      onClick={handleMarkAllAsRead}
                      disabled={unreadCount === 0}
                    >
                      Mark all read
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={handleClearAll}
                    >
                      Clear all
                    </Button>
                  </Stack>
                </Box>
              )}

              {/* Notifications List */}
              <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : filteredNotifications.length === 0 ? (
                  <Box sx={{ textAlign: 'center', p: 4 }}>
                    <NotificationsOff sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      No notifications
                    </Typography>
                  </Box>
                ) : (
                  <List sx={{ p: 0 }}>
                    {filteredNotifications.map((notification, index) => (
                      <motion.div
                        key={notification.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <ListItem
                          sx={{
                            bgcolor: notification.read ? 'transparent' : alpha(theme.palette.primary.main, 0.04),
                            borderLeft: notification.read ? 'none' : `4px solid ${theme.palette.primary.main}`,
                            '&:hover': {
                              bgcolor: alpha(theme.palette.primary.main, 0.08),
                            },
                          }}
                        >
                          <ListItemAvatar>
                            <Avatar
                              sx={{
                                bgcolor: alpha(getColor(notification.type), 0.1),
                                color: getColor(notification.type),
                              }}
                            >
                              {getIcon(notification.type)}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={
                              <Stack direction="row" spacing={1} alignItems="center">
                                <Typography variant="subtitle2">
                                  {notification.title}
                                </Typography>
                                {notification.priority === 'high' && (
                                  <Chip
                                    label="Important"
                                    size="small"
                                    color="error"
                                    sx={{ height: 20 }}
                                  />
                                )}
                              </Stack>
                            }
                            secondary={
                              <>
                                <Typography
                                  component="span"
                                  variant="body2"
                                  color="text.primary"
                                  sx={{ display: 'block', mb: 0.5 }}
                                >
                                  {notification.message}
                                </Typography>
                                <Typography
                                  component="span"
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                                </Typography>
                                {notification.actionUrl && (
                                  <Button
                                    size="small"
                                    sx={{ mt: 1 }}
                                    onClick={() => handleAction(notification)}
                                  >
                                    {notification.actionLabel || 'View'}
                                  </Button>
                                )}
                              </>
                            }
                            primaryTypographyProps={{ sx: { mb: 0.5 } }}
                          />
                          {!notification.read && (
                            <ListItemSecondaryAction>
                              <IconButton
                                edge="end"
                                size="small"
                                onClick={() => handleMarkAsRead(notification.id)}
                              >
                                <Close fontSize="small" />
                              </IconButton>
                            </ListItemSecondaryAction>
                          )}
                        </ListItem>
                        {index < filteredNotifications.length - 1 && <Divider />}
                      </motion.div>
                    ))}
                  </List>
                )}
              </Box>
            </motion.div>
          ) : (
            <motion.div
              key="settings"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Settings Header */}
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">Notification Settings</Typography>
                  <IconButton size="small" onClick={() => setShowSettings(false)}>
                    <Close fontSize="small" />
                  </IconButton>
                </Stack>
              </Box>

              {/* Settings Content */}
              <Box sx={{ p: 2 }}>
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Notification Methods
                    </Typography>
                    <Stack spacing={1}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={preferences.sound}
                            onChange={(e) => setPreferences(prev => ({ ...prev, sound: e.target.checked }))}
                          />
                        }
                        label={
                          <Stack direction="row" spacing={1} alignItems="center">
                            {preferences.sound ? <VolumeUp fontSize="small" /> : <VolumeOff fontSize="small" />}
                            <Typography variant="body2">Sound notifications</Typography>
                          </Stack>
                        }
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={preferences.desktop}
                            onChange={(e) => {
                              if (e.target.checked) {
                                requestNotificationPermission();
                              } else {
                                setPreferences(prev => ({ ...prev, desktop: false }));
                              }
                            }}
                          />
                        }
                        label="Desktop notifications"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={preferences.email}
                            onChange={(e) => setPreferences(prev => ({ ...prev, email: e.target.checked }))}
                          />
                        }
                        label="Email notifications"
                      />
                    </Stack>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Notification Categories
                    </Typography>
                    <Stack spacing={1}>
                      {Object.entries(preferences.categories).map(([key, value]) => (
                        <FormControlLabel
                          key={key}
                          control={
                            <Switch
                              checked={value}
                              onChange={(e) => setPreferences(prev => ({
                                ...prev,
                                categories: { ...prev.categories, [key]: e.target.checked },
                              }))}
                            />
                          }
                          label={key.charAt(0).toUpperCase() + key.slice(1)}
                        />
                      ))}
                    </Stack>
                  </Box>

                  <Button
                    variant="contained"
                    fullWidth
                    onClick={() => {
                      // Save preferences
                      setShowSettings(false);
                    }}
                  >
                    Save Settings
                  </Button>
                </Stack>
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Popover>

      {/* Hidden audio element for notification sounds */}
      <audio ref={audioRef} src="/notification-sound.mp3" />

      <style jsx global>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(244, 67, 54, 0);
          }
        }
      `}</style>
    </>
  );
};

export default NotificationCenter;