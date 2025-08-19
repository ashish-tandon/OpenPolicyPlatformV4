import React, { useState, useMemo } from 'react';
import {
  ThemeProvider,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Container,
  Stack,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home,
  Dashboard,
  Search,
  Policy,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { lightTheme, darkTheme } from './theme';
import HeroSection from './components/HeroSection';
import EnhancedSearch from './components/EnhancedSearch';
import InteractiveDashboard from './components/InteractiveDashboard';
import AdvancedDataTable from './components/AdvancedDataTable';
import NotificationCenter from './components/NotificationCenter';

// Mock data for the data table
const mockTableData = [
  {
    id: '1',
    title: 'Healthcare Reform Act 2024',
    type: 'Policy',
    status: 'Active',
    category: 'Healthcare',
    date: '2024-01-15',
    author: 'Jane Smith',
    priority: 'high' as const,
    starred: true,
  },
  {
    id: '2',
    title: 'Digital Privacy Protection Bill',
    type: 'Bill',
    status: 'Pending',
    category: 'Technology',
    date: '2024-01-10',
    author: 'John Doe',
    priority: 'medium' as const,
    starred: false,
  },
  {
    id: '3',
    title: 'Climate Action Initiative',
    type: 'Policy',
    status: 'Active',
    category: 'Environment',
    date: '2024-01-08',
    author: 'Sarah Johnson',
    priority: 'high' as const,
    starred: true,
  },
  {
    id: '4',
    title: 'Education Funding Reform',
    type: 'Bill',
    status: 'Completed',
    category: 'Education',
    date: '2024-01-05',
    author: 'Michael Brown',
    priority: 'medium' as const,
    starred: false,
  },
  {
    id: '5',
    title: 'Infrastructure Modernization Act',
    type: 'Policy',
    status: 'Active',
    category: 'Infrastructure',
    date: '2024-01-03',
    author: 'Emily Davis',
    priority: 'low' as const,
    starred: false,
  },
];

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const isMobile = useMediaQuery('(max-width: 600px)');

  const theme = useMemo(
    () => (darkMode || prefersDarkMode) ? darkTheme : lightTheme,
    [darkMode, prefersDarkMode]
  );

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const NavigationContent = () => {
    const location = useLocation();
    
    const menuItems = [
      { text: 'Home', icon: <Home />, path: '/' },
      { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
      { text: 'Search', icon: <Search />, path: '/search' },
      { text: 'Policies', icon: <Policy />, path: '/policies' },
    ];

    return (
      <List>
        {menuItems.map((item) => (
          <ListItem
            key={item.text}
            button
            component={Link}
            to={item.path}
            selected={location.pathname === item.path}
            onClick={() => setDrawerOpen(false)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {/* App Bar */}
          <AppBar position="fixed" elevation={0}>
            <Toolbar>
              <IconButton
                edge="start"
                color="inherit"
                aria-label="menu"
                onClick={() => setDrawerOpen(true)}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                OpenPolicy Platform V4
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <NotificationCenter />
                <FormControlLabel
                  control={
                    <Switch
                      checked={darkMode || prefersDarkMode}
                      onChange={toggleDarkMode}
                      icon={<Brightness7 />}
                      checkedIcon={<Brightness4 />}
                    />
                  }
                  label=""
                />
              </Stack>
            </Toolbar>
          </AppBar>

          {/* Navigation Drawer */}
          <Drawer
            anchor="left"
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
          >
            <Box sx={{ width: 250 }}>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6">Navigation</Typography>
              </Box>
              <Divider />
              <NavigationContent />
            </Box>
          </Drawer>

          {/* Main Content */}
          <Box component="main" sx={{ flexGrow: 1, mt: 8 }}>
            <Routes>
              <Route path="/" element={<HeroSection />} />
              <Route path="/dashboard" element={
                <Container maxWidth="xl" sx={{ py: 4 }}>
                  <InteractiveDashboard />
                </Container>
              } />
              <Route path="/search" element={
                <Container maxWidth="lg" sx={{ py: 4 }}>
                  <Typography variant="h4" gutterBottom>
                    Advanced Search
                  </Typography>
                  <Box sx={{ mt: 4 }}>
                    <EnhancedSearch />
                  </Box>
                </Container>
              } />
              <Route path="/policies" element={
                <Container maxWidth="xl" sx={{ py: 4 }}>
                  <Typography variant="h4" gutterBottom>
                    Policy Management
                  </Typography>
                  <Box sx={{ mt: 4 }}>
                    <AdvancedDataTable
                      data={mockTableData}
                      title="Active Policies and Bills"
                      onRowClick={(row) => console.log('Row clicked:', row)}
                      onEdit={(row) => console.log('Edit:', row)}
                      onDelete={(selected) => console.log('Delete:', selected)}
                    />
                  </Box>
                </Container>
              } />
            </Routes>
          </Box>

          {/* Footer */}
          <Box
            component="footer"
            sx={{
              py: 3,
              px: 2,
              mt: 'auto',
              backgroundColor: (theme) =>
                theme.palette.mode === 'light'
                  ? theme.palette.grey[200]
                  : theme.palette.grey[800],
            }}
          >
            <Container maxWidth="lg">
              <Typography variant="body2" color="text.secondary" align="center">
                © 2024 OpenPolicy Platform V4. All rights reserved.
              </Typography>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;