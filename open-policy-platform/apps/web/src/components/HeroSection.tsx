import React from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Stack,
  Card,
  CardContent,
  Chip,
  IconButton,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import {
  Search,
  Policy,
  Analytics,
  Security,
  Speed,
  CloudDone,
  ArrowForward,
  PlayCircleOutline,
  GitHub,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const MotionBox = motion(Box);
const MotionTypography = motion(Typography);
const MotionButton = motion(Button);

const HeroSection: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const features = [
    {
      icon: <Policy />,
      title: 'Policy Tracking',
      description: 'Real-time tracking of government policies and legislation',
      color: theme.palette.primary.main,
    },
    {
      icon: <Analytics />,
      title: 'Data Analytics',
      description: 'Advanced analytics and insights on political trends',
      color: theme.palette.secondary.main,
    },
    {
      icon: <Security />,
      title: 'Secure Platform',
      description: 'Enterprise-grade security for sensitive data',
      color: theme.palette.success.main,
    },
    {
      icon: <Speed />,
      title: 'High Performance',
      description: 'Lightning-fast search and data processing',
      color: theme.palette.warning.main,
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated background shapes */}
      <MotionBox
        animate={{
          rotate: 360,
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'linear',
        }}
        sx={{
          position: 'absolute',
          top: -200,
          right: -200,
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.1)} 0%, transparent 70%)`,
          filter: 'blur(40px)',
        }}
      />
      
      <MotionBox
        animate={{
          rotate: -360,
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: 'linear',
        }}
        sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(theme.palette.secondary.main, 0.1)} 0%, transparent 70%)`,
          filter: 'blur(40px)',
        }}
      />

      <Container maxWidth="lg" sx={{ pt: 12, pb: 8, position: 'relative', zIndex: 1 }}>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <MotionBox
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            >
              <Stack spacing={3}>
                <Box>
                  <Chip
                    icon={<CloudDone />}
                    label="V4.0 Now Live"
                    color="primary"
                    sx={{ mb: 2 }}
                  />
                  <MotionTypography
                    variant="h1"
                    component="h1"
                    gutterBottom
                    sx={{
                      fontWeight: 800,
                      background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                      backgroundClip: 'text',
                      textFillColor: 'transparent',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.8 }}
                  >
                    Open Policy Platform
                  </MotionTypography>
                </Box>
                
                <Typography
                  variant="h5"
                  color="text.secondary"
                  sx={{ maxWidth: 500, lineHeight: 1.6 }}
                >
                  The most comprehensive platform for tracking, analyzing, and understanding
                  government policies and political data in real-time.
                </Typography>

                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 4 }}>
                  <MotionButton
                    variant="contained"
                    size="large"
                    endIcon={<ArrowForward />}
                    onClick={() => navigate('/explore')}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    sx={{
                      px: 4,
                      py: 1.5,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                      boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
                      '&:hover': {
                        boxShadow: `0 12px 48px ${alpha(theme.palette.primary.main, 0.4)}`,
                      },
                    }}
                  >
                    Explore Platform
                  </MotionButton>
                  
                  <MotionButton
                    variant="outlined"
                    size="large"
                    startIcon={<PlayCircleOutline />}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    sx={{
                      px: 4,
                      py: 1.5,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      borderWidth: 2,
                      '&:hover': {
                        borderWidth: 2,
                      },
                    }}
                  >
                    Watch Demo
                  </MotionButton>
                </Stack>

                <Stack direction="row" spacing={3} sx={{ mt: 4 }}>
                  <Box>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      37+
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Microservices
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      99.9%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uptime SLA
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      <1s
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Response Time
                    </Typography>
                  </Box>
                </Stack>
              </Stack>
            </MotionBox>
          </Grid>

          <Grid item xs={12} md={6}>
            <MotionBox
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <Box sx={{ position: 'relative' }}>
                {/* Interactive search preview */}
                <Card
                  sx={{
                    p: 3,
                    mb: 3,
                    background: alpha(theme.palette.background.paper, 0.8),
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                  }}
                >
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                    <Search color="primary" />
                    <Typography variant="h6">Live Policy Search</Typography>
                  </Stack>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      bgcolor: 'background.default',
                      border: `2px solid ${theme.palette.primary.main}`,
                    }}
                  >
                    <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                      healthcare reform bill 2024...
                    </Typography>
                  </Box>
                </Card>

                {/* Feature cards */}
                <Grid container spacing={2}>
                  {features.map((feature, index) => (
                    <Grid item xs={6} key={index}>
                      <MotionBox
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 + index * 0.1, duration: 0.5 }}
                        whileHover={{ y: -5 }}
                      >
                        <Card
                          sx={{
                            p: 2,
                            height: '100%',
                            background: alpha(theme.palette.background.paper, 0.8),
                            backdropFilter: 'blur(20px)',
                            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              borderColor: feature.color,
                              boxShadow: `0 8px 32px ${alpha(feature.color, 0.2)}`,
                            },
                          }}
                        >
                          <Box
                            sx={{
                              display: 'inline-flex',
                              p: 1.5,
                              borderRadius: 2,
                              bgcolor: alpha(feature.color, 0.1),
                              color: feature.color,
                              mb: 2,
                            }}
                          >
                            {feature.icon}
                          </Box>
                          <Typography variant="h6" gutterBottom>
                            {feature.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {feature.description}
                          </Typography>
                        </Card>
                      </MotionBox>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </MotionBox>
          </Grid>
        </Grid>

        {/* Bottom CTA */}
        <MotionBox
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          sx={{ mt: 8, textAlign: 'center' }}
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Trusted by government agencies, researchers, and policy makers worldwide
          </Typography>
          <Stack
            direction="row"
            spacing={2}
            justifyContent="center"
            alignItems="center"
            sx={{ mt: 3 }}
          >
            <Button
              variant="text"
              startIcon={<GitHub />}
              href="https://github.com/openpolicy-platform"
              target="_blank"
            >
              View on GitHub
            </Button>
            <Typography variant="body2" color="text.secondary">
              •
            </Typography>
            <Button variant="text" onClick={() => navigate('/docs')}>
              Documentation
            </Button>
            <Typography variant="body2" color="text.secondary">
              •
            </Typography>
            <Button variant="text" onClick={() => navigate('/api')}>
              API Access
            </Button>
          </Stack>
        </MotionBox>
      </Container>
    </Box>
  );
};

export default HeroSection;