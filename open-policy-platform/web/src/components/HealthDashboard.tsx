import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  AlertTitle,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Refresh,
  Speed,
  Storage,
  Memory,
  NetworkCheck,
} from '@mui/icons-material';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  responseTime: number;
  errorRate: number;
  lastCheck: string;
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
}

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  timestamp: string;
}

const HealthDashboard: React.FC = () => {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(fetchHealthData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchHealthData = async () => {
    try {
      // Fetch service health
      const servicesRes = await fetch('/api/monitoring/services');
      const servicesData = await servicesRes.json();
      setServices(servicesData);

      // Fetch system metrics
      const metricsRes = await fetch('/api/monitoring/metrics');
      const metricsData = await metricsRes.json();
      setMetrics(metricsData);

      // Fetch active alerts
      const alertsRes = await fetch('/api/monitoring/alerts');
      const alertsData = await alertsRes.json();
      setAlerts(alertsData);

      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'degraded':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'down':
        return <Error sx={{ color: 'error.main' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  const healthyServices = services.filter(s => s.status === 'healthy').length;
  const totalServices = services.length;
  const platformHealth = (healthyServices / totalServices) * 100;

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Platform Health Dashboard
        </Typography>
        <Box>
          <Typography variant="body2" color="text.secondary" component="span">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchHealthData} sx={{ ml: 1 }}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Platform Health Score */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Overall Platform Health
          </Typography>
          <Box display="flex" alignItems="center">
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={platformHealth}
                sx={{
                  height: 20,
                  borderRadius: 10,
                  backgroundColor: 'grey.300',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: platformHealth > 80 ? 'success.main' : platformHealth > 50 ? 'warning.main' : 'error.main',
                  },
                }}
              />
            </Box>
            <Typography variant="h5" color="text.secondary">
              {platformHealth.toFixed(0)}%
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {healthyServices} of {totalServices} services operational
          </Typography>
        </CardContent>
      </Card>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          {alerts.map((alert) => (
            <Alert key={alert.id} severity={getSeverityColor(alert.severity) as any} sx={{ mb: 1 }}>
              <AlertTitle>{alert.title}</AlertTitle>
              {alert.description} — {new Date(alert.timestamp).toLocaleTimeString()}
            </Alert>
          ))}
        </Box>
      )}

      {/* System Metrics */}
      {metrics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Speed sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography color="text.secondary" variant="h6">
                    CPU Usage
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {metrics.cpu.toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={metrics.cpu}
                  sx={{ mt: 1 }}
                  color={metrics.cpu > 80 ? 'error' : metrics.cpu > 60 ? 'warning' : 'primary'}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Memory sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography color="text.secondary" variant="h6">
                    Memory
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {metrics.memory.toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={metrics.memory}
                  sx={{ mt: 1 }}
                  color={metrics.memory > 85 ? 'error' : metrics.memory > 70 ? 'warning' : 'primary'}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Storage sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography color="text.secondary" variant="h6">
                    Disk Usage
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {metrics.disk.toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={metrics.disk}
                  sx={{ mt: 1 }}
                  color={metrics.disk > 90 ? 'error' : metrics.disk > 75 ? 'warning' : 'primary'}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <NetworkCheck sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography color="text.secondary" variant="h6">
                    Network I/O
                  </Typography>
                </Box>
                <Typography variant="body1">
                  ↓ {(metrics.network.in / 1024 / 1024).toFixed(1)} MB/s
                </Typography>
                <Typography variant="body1">
                  ↑ {(metrics.network.out / 1024 / 1024).toFixed(1)} MB/s
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Service Status Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Service</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Uptime</TableCell>
              <TableCell align="center">Response Time</TableCell>
              <TableCell align="center">Error Rate</TableCell>
              <TableCell align="center">Last Check</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {services.map((service) => (
              <TableRow key={service.name}>
                <TableCell component="th" scope="row">
                  <Typography variant="body1">{service.name}</Typography>
                </TableCell>
                <TableCell align="center">
                  <Chip
                    icon={getStatusIcon(service.status)}
                    label={service.status.toUpperCase()}
                    color={getStatusColor(service.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2">
                    {service.uptime.toFixed(2)}%
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2">
                    {service.responseTime}ms
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography
                    variant="body2"
                    color={service.errorRate > 5 ? 'error' : service.errorRate > 1 ? 'warning' : 'text.primary'}
                  >
                    {service.errorRate.toFixed(2)}%
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2" color="text.secondary">
                    {new Date(service.lastCheck).toLocaleTimeString()}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default HealthDashboard;