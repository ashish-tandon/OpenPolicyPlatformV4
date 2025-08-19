import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  CircularProgress,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Switch,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People,
  Policy,
  Storage,
  Security,
  Settings,
  Notifications,
  CheckCircle,
  Warning,
  Error,
  Refresh,
  Add,
  Edit,
  Delete,
  PowerSettingsNew,
  RestartAlt,
  CloudUpload,
  CloudDownload,
  Speed,
  Memory,
  NetworkCheck,
  BarChart,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import HealthDashboard from '../components/HealthDashboard';
import ServiceManager from '../components/ServiceManager';
import UserManagement from '../components/UserManagement';
import SystemLogs from '../components/SystemLogs';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface ServiceStatus {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error';
  cpu: number;
  memory: number;
  uptime: string;
  version: string;
  port: number;
  healthEndpoint: string;
}

interface SystemStats {
  totalServices: number;
  runningServices: number;
  totalUsers: number;
  activeUsers: number;
  totalPolicies: number;
  totalScrapers: number;
  systemUptime: string;
  lastBackup: string;
}

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState<ServiceStatus | null>(null);
  const [actionDialog, setActionDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as any });
  const [alerts, setAlerts] = useState(0);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch services status
      const servicesRes = await fetch('/api/dashboard/services', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const servicesData = await servicesRes.json();
      setServices(servicesData);

      // Fetch system stats
      const statsRes = await fetch('/api/dashboard/stats', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const statsData = await statsRes.json();
      setSystemStats(statsData);

      // Fetch active alerts count
      const alertsRes = await fetch('/api/monitoring/alerts/count', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const alertsData = await alertsRes.json();
      setAlerts(alertsData.count);

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  const handleServiceAction = async (serviceId: string, action: string) => {
    try {
      const response = await fetch(`/api/dashboard/services/${serviceId}/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setSnackbar({
          open: true,
          message: `Service ${action} successful`,
          severity: 'success',
        });
        fetchDashboardData();
      } else {
        throw new Error('Action failed');
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to ${action} service`,
        severity: 'error',
      });
    }
    setActionDialog(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle />;
      case 'stopped':
        return <PowerSettingsNew />;
      case 'error':
        return <Error />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Admin Dashboard
        </Typography>
        <Box>
          <Typography variant="body2" color="text.secondary">
            Welcome, {user?.name || 'Admin'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Last login: {new Date().toLocaleString()}
          </Typography>
        </Box>
      </Box>

      {/* System Overview Cards */}
      {systemStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Services Status
                </Typography>
                <Typography variant="h4">
                  {systemStats.runningServices}/{systemStats.totalServices}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(systemStats.runningServices / systemStats.totalServices) * 100}
                  sx={{ mt: 1 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Services Running
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active Users
                </Typography>
                <Typography variant="h4">
                  {systemStats.activeUsers}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Total: {systemStats.totalUsers}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Policies
                </Typography>
                <Typography variant="h4">
                  {systemStats.totalPolicies}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Active Scrapers: {systemStats.totalScrapers}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  System Uptime
                </Typography>
                <Typography variant="h4">
                  {systemStats.systemUptime}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Last backup: {systemStats.lastBackup}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Admin Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="admin dashboard tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<DashboardIcon />} label="Overview" />
          <Tab icon={<Storage />} label="Services" />
          <Tab
            icon={
              <Badge badgeContent={alerts} color="error">
                <BarChart />
              </Badge>
            }
            label="Monitoring"
          />
          <Tab icon={<People />} label="Users" />
          <Tab icon={<Security />} label="Security" />
          <Tab icon={<Settings />} label="System" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Services Overview Table */}
          <Typography variant="h6" gutterBottom>
            Services Overview
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Service</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>CPU</TableCell>
                  <TableCell>Memory</TableCell>
                  <TableCell>Uptime</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {services.map((service) => (
                  <TableRow key={service.id}>
                    <TableCell>{service.name}</TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(service.status)}
                        label={service.status.toUpperCase()}
                        color={getStatusColor(service.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{service.cpu}%</TableCell>
                    <TableCell>{service.memory}%</TableCell>
                    <TableCell>{service.uptime}</TableCell>
                    <TableCell>{service.version}</TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedService(service);
                          setActionDialog(true);
                        }}
                      >
                        <Settings />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ServiceManager services={services} onUpdate={fetchDashboardData} />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <HealthDashboard />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <UserManagement />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <SecuritySettings />
        </TabPanel>

        <TabPanel value={tabValue} index={5}>
          <SystemLogs />
        </TabPanel>
      </Paper>

      {/* Service Action Dialog */}
      <Dialog open={actionDialog} onClose={() => setActionDialog(false)}>
        <DialogTitle>Service Actions - {selectedService?.name}</DialogTitle>
        <DialogContent>
          <List>
            <ListItem button onClick={() => handleServiceAction(selectedService!.id, 'restart')}>
              <ListItemIcon>
                <RestartAlt />
              </ListItemIcon>
              <ListItemText primary="Restart Service" secondary="Restart the service process" />
            </ListItem>
            <ListItem button onClick={() => handleServiceAction(selectedService!.id, 'stop')}>
              <ListItemIcon>
                <PowerSettingsNew />
              </ListItemIcon>
              <ListItemText primary="Stop Service" secondary="Stop the service process" />
            </ListItem>
            <ListItem button onClick={() => handleServiceAction(selectedService!.id, 'logs')}>
              <ListItemIcon>
                <Storage />
              </ListItemIcon>
              <ListItemText primary="View Logs" secondary="View service logs" />
            </ListItem>
            <ListItem button onClick={() => handleServiceAction(selectedService!.id, 'update')}>
              <ListItemIcon>
                <CloudUpload />
              </ListItemIcon>
              <ListItemText primary="Update Service" secondary="Update to latest version" />
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

// Placeholder component for Security Settings
const SecuritySettings: React.FC = () => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Security Settings
    </Typography>
    <Alert severity="info">Security settings component coming soon...</Alert>
  </Box>
);

export default AdminDashboard;