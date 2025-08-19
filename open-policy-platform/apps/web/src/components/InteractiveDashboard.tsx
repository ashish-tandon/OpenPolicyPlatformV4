import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  Stack,
  Paper,
  Button,
  Avatar,
  AvatarGroup,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  MoreVert,
  TrendingUp,
  TrendingDown,
  Refresh,
  Download,
  Fullscreen,
  Info,
  Policy,
  People,
  Gavel,
  Analytics,
  CalendarToday,
  Assessment,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import CountUp from 'react-countup';

const MotionCard = motion(Card);

interface DashboardMetric {
  label: string;
  value: number;
  change: number;
  icon: React.ReactNode;
  color: string;
}

const InteractiveDashboard: React.FC = () => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState('7d');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('all');

  // Mock data - replace with real API calls
  const metrics: DashboardMetric[] = [
    {
      label: 'Total Policies',
      value: 1247,
      change: 12.5,
      icon: <Policy />,
      color: theme.palette.primary.main,
    },
    {
      label: 'Active Bills',
      value: 384,
      change: -5.2,
      icon: <Gavel />,
      color: theme.palette.secondary.main,
    },
    {
      label: 'Representatives',
      value: 535,
      change: 2.1,
      icon: <People />,
      color: theme.palette.success.main,
    },
    {
      label: 'Committees',
      value: 89,
      change: 0,
      icon: <Analytics />,
      color: theme.palette.warning.main,
    },
  ];

  const timeSeriesData = [
    { date: 'Mon', policies: 45, bills: 23, debates: 67 },
    { date: 'Tue', policies: 52, bills: 28, debates: 72 },
    { date: 'Wed', policies: 48, bills: 31, debates: 69 },
    { date: 'Thu', policies: 63, bills: 27, debates: 81 },
    { date: 'Fri', policies: 58, bills: 35, debates: 76 },
    { date: 'Sat', policies: 42, bills: 19, debates: 54 },
    { date: 'Sun', policies: 38, bills: 15, debates: 48 },
  ];

  const categoryData = [
    { name: 'Healthcare', value: 312, color: theme.palette.primary.main },
    { name: 'Education', value: 246, color: theme.palette.secondary.main },
    { name: 'Environment', value: 198, color: theme.palette.success.main },
    { name: 'Economy', value: 287, color: theme.palette.warning.main },
    { name: 'Technology', value: 165, color: theme.palette.info.main },
    { name: 'Other', value: 89, color: theme.palette.grey[400] },
  ];

  const performanceData = [
    { metric: 'Response Time', current: 85, target: 95 },
    { metric: 'Data Accuracy', current: 98, target: 99 },
    { metric: 'User Satisfaction', current: 92, target: 90 },
    { metric: 'System Uptime', current: 99.9, target: 99.5 },
    { metric: 'API Reliability', current: 97, target: 95 },
  ];

  const radarData = [
    { category: 'Policies', A: 120, B: 110, fullMark: 150 },
    { category: 'Bills', A: 98, B: 130, fullMark: 150 },
    { category: 'Debates', A: 86, B: 130, fullMark: 150 },
    { category: 'Committees', A: 99, B: 100, fullMark: 150 },
    { category: 'Representatives', A: 85, B: 90, fullMark: 150 },
    { category: 'Votes', A: 65, B: 85, fullMark: 150 },
  ];

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const MetricCard = ({ metric, index }: { metric: DashboardMetric; index: number }) => (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      whileHover={{ y: -5 }}
      sx={{
        height: '100%',
        background: alpha(metric.color, 0.04),
        border: `1px solid ${alpha(metric.color, 0.1)}`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {metric.label}
            </Typography>
            <Typography variant="h3" fontWeight="bold" sx={{ my: 1 }}>
              <CountUp end={metric.value} duration={1.5} separator="," />
            </Typography>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              {metric.change > 0 ? (
                <TrendingUp fontSize="small" color="success" />
              ) : metric.change < 0 ? (
                <TrendingDown fontSize="small" color="error" />
              ) : null}
              <Typography
                variant="body2"
                color={metric.change > 0 ? 'success.main' : metric.change < 0 ? 'error.main' : 'text.secondary'}
              >
                {metric.change > 0 && '+'}
                {metric.change}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vs last period
              </Typography>
            </Stack>
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              bgcolor: alpha(metric.color, 0.1),
              color: metric.color,
            }}
          >
            {metric.icon}
          </Box>
        </Stack>
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 4,
            bgcolor: alpha(metric.color, 0.1),
          }}
        >
          <Box
            sx={{
              height: '100%',
              width: `${Math.min(100, (metric.value / 1500) * 100)}%`,
              bgcolor: metric.color,
              borderRadius: 1,
            }}
          />
        </Box>
      </CardContent>
    </MotionCard>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Analytics Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time platform metrics and insights
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              displayEmpty
            >
              <MenuItem value="24h">Last 24h</MenuItem>
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<Download />}
            sx={{ textTransform: 'none' }}
          >
            Export
          </Button>
          <IconButton onClick={handleRefresh}>
            <Refresh />
          </IconButton>
        </Stack>
      </Stack>

      {isLoading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={metric.label}>
            <MetricCard metric={metric} index={index} />
          </Grid>
        ))}
      </Grid>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Time Series Chart */}
        <Grid item xs={12} lg={8}>
          <MotionCard
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <CardHeader
              title="Activity Timeline"
              subheader="Daily activity across all categories"
              action={
                <IconButton size="small">
                  <Fullscreen />
                </IconButton>
              }
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={timeSeriesData}>
                  <defs>
                    <linearGradient id="colorPolicies" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorBills" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={theme.palette.secondary.main} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={theme.palette.secondary.main} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorDebates" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={theme.palette.success.main} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={theme.palette.success.main} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.3)} />
                  <XAxis dataKey="date" stroke={theme.palette.text.secondary} />
                  <YAxis stroke={theme.palette.text.secondary} />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="policies"
                    stroke={theme.palette.primary.main}
                    fillOpacity={1}
                    fill="url(#colorPolicies)"
                  />
                  <Area
                    type="monotone"
                    dataKey="bills"
                    stroke={theme.palette.secondary.main}
                    fillOpacity={1}
                    fill="url(#colorBills)"
                  />
                  <Area
                    type="monotone"
                    dataKey="debates"
                    stroke={theme.palette.success.main}
                    fillOpacity={1}
                    fill="url(#colorDebates)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </MotionCard>
        </Grid>

        {/* Category Distribution */}
        <Grid item xs={12} lg={4}>
          <MotionCard
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <CardHeader
              title="Category Distribution"
              subheader="Policy breakdown by category"
              action={
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              }
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <Stack spacing={1} sx={{ mt: 2 }}>
                {categoryData.slice(0, 4).map((cat) => (
                  <Stack key={cat.name} direction="row" justifyContent="space-between" alignItems="center">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          bgcolor: cat.color,
                        }}
                      />
                      <Typography variant="body2">{cat.name}</Typography>
                    </Stack>
                    <Typography variant="body2" fontWeight="medium">
                      {cat.value}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} md={6}>
          <MotionCard
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <CardHeader
              title="System Performance"
              subheader="Key performance indicators"
              action={
                <Chip
                  label="Live"
                  color="success"
                  size="small"
                  sx={{ animation: 'pulse 2s infinite' }}
                />
              }
            />
            <CardContent>
              <Stack spacing={3}>
                {performanceData.map((item) => (
                  <Box key={item.metric}>
                    <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
                      <Typography variant="body2">{item.metric}</Typography>
                      <Typography variant="body2" fontWeight="medium">
                        {item.current}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={item.current}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          bgcolor: item.current >= item.target ? 'success.main' : 'warning.main',
                        },
                      }}
                    />
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </MotionCard>
        </Grid>

        {/* Comparative Analysis */}
        <Grid item xs={12} md={6}>
          <MotionCard
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <CardHeader
              title="Comparative Analysis"
              subheader="Current vs Previous Period"
              action={
                <IconButton size="small">
                  <Info />
                </IconButton>
              }
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke={alpha(theme.palette.divider, 0.3)} />
                  <PolarAngleAxis dataKey="category" />
                  <PolarRadiusAxis angle={90} domain={[0, 150]} />
                  <Radar
                    name="Current"
                    dataKey="A"
                    stroke={theme.palette.primary.main}
                    fill={theme.palette.primary.main}
                    fillOpacity={0.6}
                  />
                  <Radar
                    name="Previous"
                    dataKey="B"
                    stroke={theme.palette.secondary.main}
                    fill={theme.palette.secondary.main}
                    fillOpacity={0.6}
                  />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </MotionCard>
        </Grid>
      </Grid>

      <style jsx global>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
          }
        }
      `}</style>
    </Box>
  );
};

export default InteractiveDashboard;