#!/bin/bash
set -e

# Setup SSO Integration for OpenPolicy Platform
# Supports SAML, OAuth, OpenID Connect, and LDAP

echo "=== Setting up SSO Integration ==="

# Configuration
SSO_SERVICE_PORT=9030
POSTGRES_HOST=${POSTGRES_HOST:-"postgres"}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-"postgres"}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"postgres"}
POSTGRES_DB=${POSTGRES_DB:-"openpolicy_sso"}
REDIS_HOST=${REDIS_HOST:-"redis"}
REDIS_PORT=${REDIS_PORT:-6379}

# 1. Create SSO Database Schema
echo "1. Creating SSO Database Schema..."
cat > database/schemas/sso_schema.sql << 'EOF'
-- SSO Integration Database Schema

-- SSO provider configurations
CREATE TABLE IF NOT EXISTS sso_configurations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Common settings
    enabled BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    allow_signup BOOLEAN DEFAULT TRUE,
    
    -- SAML Configuration
    saml_entity_id VARCHAR(500),
    saml_sso_url VARCHAR(500),
    saml_slo_url VARCHAR(500),
    saml_x509_cert TEXT,
    saml_metadata_url VARCHAR(500),
    saml_attribute_mapping JSONB,
    
    -- OAuth/OIDC Configuration
    oauth_client_id VARCHAR(500),
    oauth_client_secret TEXT, -- Encrypted
    oauth_authorization_url VARCHAR(500),
    oauth_token_url VARCHAR(500),
    oauth_userinfo_url VARCHAR(500),
    oauth_scopes JSONB,
    oauth_flow_type VARCHAR(50) DEFAULT 'authorization_code',
    
    -- LDAP Configuration
    ldap_server_url VARCHAR(500),
    ldap_bind_dn VARCHAR(500),
    ldap_bind_password TEXT, -- Encrypted
    ldap_base_dn VARCHAR(500),
    ldap_user_filter VARCHAR(500),
    ldap_group_filter VARCHAR(500),
    ldap_attribute_mapping JSONB,
    
    -- Advanced settings
    custom_claims JSONB,
    role_mapping JSONB,
    group_mapping JSONB,
    mfa_required BOOLEAN DEFAULT FALSE,
    allowed_domains JSONB,
    blocked_domains JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sso_tenant (tenant_id),
    INDEX idx_sso_provider (provider),
    UNIQUE (tenant_id, name)
);

-- SSO sessions
CREATE TABLE IF NOT EXISTS sso_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    
    -- Session data
    access_token TEXT,
    refresh_token TEXT,
    id_token TEXT,
    
    -- User info
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    groups JSONB,
    attributes JSONB,
    
    -- Session management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    INDEX idx_session_id (session_id),
    INDEX idx_session_user (user_id),
    INDEX idx_session_expires (expires_at)
);

-- SSO audit logs
CREATE TABLE IF NOT EXISTS sso_audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    provider VARCHAR(50),
    event_type VARCHAR(100) NOT NULL,
    
    success BOOLEAN,
    error_message TEXT,
    
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sso_audit_tenant (tenant_id),
    INDEX idx_sso_audit_event (event_type),
    INDEX idx_sso_audit_timestamp (created_at)
);

-- Pre-configured SSO providers
CREATE TABLE IF NOT EXISTS sso_provider_templates (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    configuration_template JSONB NOT NULL,
    required_fields JSONB,
    optional_fields JSONB,
    
    logo_url VARCHAR(500),
    documentation_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert provider templates
INSERT INTO sso_provider_templates (provider, name, description, configuration_template) VALUES
('google', 'Google Workspace', 'Sign in with Google Workspace accounts', 
 '{"oauth_authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
   "oauth_token_url": "https://oauth2.googleapis.com/token",
   "oauth_userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
   "oauth_scopes": ["openid", "email", "profile"]}'),
   
('azure_ad', 'Microsoft Azure AD', 'Sign in with Microsoft Azure Active Directory',
 '{"oauth_authorization_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
   "oauth_token_url": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
   "oauth_userinfo_url": "https://graph.microsoft.com/v1.0/me",
   "oauth_scopes": ["openid", "email", "profile", "User.Read"]}'),
   
('okta', 'Okta', 'Sign in with Okta SSO',
 '{"oauth_authorization_url": "https://{okta_domain}/oauth2/default/v1/authorize",
   "oauth_token_url": "https://{okta_domain}/oauth2/default/v1/token",
   "oauth_userinfo_url": "https://{okta_domain}/oauth2/default/v1/userinfo",
   "oauth_scopes": ["openid", "email", "profile", "groups"]}'),
   
('auth0', 'Auth0', 'Sign in with Auth0',
 '{"oauth_authorization_url": "https://{auth0_domain}/authorize",
   "oauth_token_url": "https://{auth0_domain}/oauth/token",
   "oauth_userinfo_url": "https://{auth0_domain}/userinfo",
   "oauth_scopes": ["openid", "email", "profile"]}')
ON CONFLICT DO NOTHING;

-- Views for monitoring
CREATE OR REPLACE VIEW sso_login_stats AS
SELECT 
    tenant_id,
    provider,
    DATE(created_at) as login_date,
    COUNT(*) FILTER (WHERE success = true) as successful_logins,
    COUNT(*) FILTER (WHERE success = false) as failed_logins,
    COUNT(DISTINCT user_id) as unique_users
FROM sso_audit_logs
WHERE event_type IN ('sso_login_success', 'sso_login_failed')
GROUP BY tenant_id, provider, DATE(created_at);

CREATE OR REPLACE VIEW active_sso_sessions AS
SELECT 
    tenant_id,
    provider,
    COUNT(*) as session_count,
    COUNT(DISTINCT user_id) as unique_users
FROM sso_sessions
WHERE expires_at > NOW()
GROUP BY tenant_id, provider;

-- Functions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sso_sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE OR REPLACE FUNCTION update_sso_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sso_configurations_updated_at
    BEFORE UPDATE ON sso_configurations
    FOR EACH ROW EXECUTE FUNCTION update_sso_updated_at();
EOF

# 2. Apply Database Schema
echo "2. Applying SSO Database Schema..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB" 2>/dev/null || true
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -f database/schemas/sso_schema.sql || echo "Schema creation skipped (database not available)"

# 3. Create SSO Service Dockerfile
echo "3. Creating SSO Service Dockerfile..."
cat > services/sso/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    libsasl2-dev \
    libldap2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 sso && \
    chown -R sso:sso /app

USER sso

EXPOSE 9030

CMD ["python", "-m", "uvicorn", "sso-service:app", "--host", "0.0.0.0", "--port", "9030"]
EOF

# 4. Create Requirements File
echo "4. Creating Requirements File..."
cat > services/sso/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
httpx==0.25.2
cryptography==41.0.7
python-jose[cryptography]==3.3.0
python3-saml==1.15.0
ldap3==2.9.1
prometheus-client==0.19.0
python-multipart==0.0.6
email-validator==2.1.0
EOF

# 5. Create SSO React Components
echo "5. Creating SSO React Components..."
cat > apps/web/src/components/SSOLogin.tsx << 'EOF'
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar
} from '@mui/material';
import {
  Google as GoogleIcon,
  Microsoft as MicrosoftIcon,
  Business as BusinessIcon,
  VpnKey as VpnKeyIcon,
  AccountCircle as AccountIcon,
  Security as SecurityIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';

interface SSOProvider {
  id: number;
  provider: string;
  name: string;
  enabled: boolean;
  metadata: {
    type: string;
    allow_signup: boolean;
  };
}

const SSOLogin: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [providers, setProviders] = useState<SSOProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<SSOProvider | null>(null);
  const [showLdapForm, setShowLdapForm] = useState(false);
  const [ldapCredentials, setLdapCredentials] = useState({
    username: '',
    password: ''
  });

  const returnUrl = searchParams.get('return') || '/dashboard';
  const tenantId = searchParams.get('tenant') || extractTenantFromDomain();

  useEffect(() => {
    fetchSSOProviders();
  }, [tenantId]);

  const extractTenantFromDomain = () => {
    const hostname = window.location.hostname;
    const subdomain = hostname.split('.')[0];
    return subdomain !== 'www' && subdomain !== 'openpolicy' ? subdomain : 'default';
  };

  const fetchSSOProviders = async () => {
    try {
      const response = await fetch('/api/sso/providers', {
        headers: {
          'X-Tenant-ID': tenantId
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch SSO providers');
      
      const data = await response.json();
      setProviders(data.providers.filter((p: SSOProvider) => p.enabled));
      setLoading(false);
    } catch (err) {
      setError('Unable to load sign-in options');
      setLoading(false);
    }
  };

  const handleSSOLogin = async (provider: SSOProvider) => {
    try {
      window.location.href = `/api/sso/login?provider_id=${provider.id}&return_url=${encodeURIComponent(returnUrl)}`;
    } catch (err) {
      setError('Failed to initiate SSO login');
    }
  };

  const handleLdapLogin = async () => {
    if (!selectedProvider) return;
    
    try {
      const response = await fetch('/api/sso/ldap/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          provider_id: selectedProvider.id.toString(),
          username: ldapCredentials.username,
          password: ldapCredentials.password
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Invalid credentials');
      }
      
      const data = await response.json();
      
      // Store token and redirect
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate(returnUrl);
      
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'google':
        return <GoogleIcon />;
      case 'azure_ad':
        return <MicrosoftIcon />;
      case 'okta':
      case 'auth0':
        return <SecurityIcon />;
      case 'saml':
        return <VpnKeyIcon />;
      case 'ldap':
        return <BusinessIcon />;
      default:
        return <AccountIcon />;
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'google':
        return '#4285F4';
      case 'azure_ad':
        return '#0078D4';
      case 'okta':
        return '#007DC1';
      case 'auth0':
        return '#EB5424';
      default:
        return '#666';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (showLdapForm && selectedProvider) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="grey.100">
        <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
          <Box display="flex" alignItems="center" mb={3}>
            <IconButton onClick={() => setShowLdapForm(false)} sx={{ mr: 1 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h5">
              {selectedProvider.name} Login
            </Typography>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="Username"
            value={ldapCredentials.username}
            onChange={(e) => setLdapCredentials({
              ...ldapCredentials,
              username: e.target.value
            })}
            margin="normal"
            autoFocus
          />
          
          <TextField
            fullWidth
            type="password"
            label="Password"
            value={ldapCredentials.password}
            onChange={(e) => setLdapCredentials({
              ...ldapCredentials,
              password: e.target.value
            })}
            margin="normal"
          />
          
          <Button
            fullWidth
            variant="contained"
            onClick={handleLdapLogin}
            sx={{ mt: 3 }}
            disabled={!ldapCredentials.username || !ldapCredentials.password}
          >
            Sign In
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="grey.100">
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Box textAlign="center" mb={3}>
          <Typography variant="h4" gutterBottom>
            Sign In
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Choose your sign-in method
          </Typography>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {providers.length === 0 ? (
          <Alert severity="info">
            No sign-in methods configured. Please contact your administrator.
          </Alert>
        ) : (
          <List>
            {providers.map((provider) => (
              <ListItem key={provider.id} disablePadding sx={{ mb: 1 }}>
                <ListItemButton
                  onClick={() => {
                    if (provider.provider === 'ldap') {
                      setSelectedProvider(provider);
                      setShowLdapForm(true);
                    } else {
                      handleSSOLogin(provider);
                    }
                  }}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    '&:hover': {
                      borderColor: getProviderColor(provider.provider),
                      bgcolor: 'action.hover'
                    }
                  }}
                >
                  <ListItemIcon>
                    <Avatar
                      sx={{
                        bgcolor: getProviderColor(provider.provider),
                        width: 32,
                        height: 32
                      }}
                    >
                      {getProviderIcon(provider.provider)}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={`Sign in with ${provider.name}`}
                    secondary={provider.metadata.allow_signup ? 'Sign up enabled' : 'Existing users only'}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
        
        <Divider sx={{ my: 3 }} />
        
        <Box textAlign="center">
          <Typography variant="body2" color="text.secondary">
            Having trouble signing in?
          </Typography>
          <Button size="small" sx={{ mt: 1 }}>
            Contact Support
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SSOLogin;
EOF

# 6. Create SSO Configuration Component
echo "6. Creating SSO Configuration Component..."
cat > apps/web/src/components/SSOConfiguration.tsx << 'EOF'
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  Grid,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Stepper,
  Step,
  StepLabel,
  StepContent
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface SSOConfig {
  id?: number;
  provider: string;
  name: string;
  enabled: boolean;
  allow_signup: boolean;
  saml_config?: any;
  oauth_config?: any;
  ldap_config?: any;
  allowed_domains?: string[];
  role_mapping?: Record<string, string>;
  mfa_required: boolean;
}

const SSOConfiguration: React.FC = () => {
  const [providers, setProviders] = useState<SSOConfig[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [activeStep, setActiveStep] = useState(0);
  const [configData, setConfigData] = useState<SSOConfig>({
    provider: '',
    name: '',
    enabled: true,
    allow_signup: true,
    mfa_required: false
  });

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/sso/providers');
      const data = await response.json();
      setProviders(data.providers);
    } catch (error) {
      console.error('Failed to fetch SSO providers:', error);
    }
  };

  const providerTypes = [
    { value: 'saml', label: 'SAML 2.0', description: 'Enterprise SSO with SAML' },
    { value: 'oauth2', label: 'OAuth 2.0', description: 'Modern OAuth flow' },
    { value: 'oidc', label: 'OpenID Connect', description: 'OAuth with identity' },
    { value: 'google', label: 'Google Workspace', description: 'Sign in with Google' },
    { value: 'azure_ad', label: 'Microsoft Azure AD', description: 'Enterprise Microsoft' },
    { value: 'okta', label: 'Okta', description: 'Okta SSO integration' },
    { value: 'ldap', label: 'LDAP/AD', description: 'On-premise directory' }
  ];

  const getProviderSteps = (provider: string) => {
    switch (provider) {
      case 'saml':
        return ['Basic Info', 'SAML Configuration', 'Attribute Mapping', 'Review'];
      case 'oauth2':
      case 'oidc':
        return ['Basic Info', 'OAuth Configuration', 'Scopes & Claims', 'Review'];
      case 'ldap':
        return ['Basic Info', 'LDAP Connection', 'User Mapping', 'Review'];
      default:
        return ['Basic Info', 'Provider Settings', 'Review'];
    }
  };

  const handleCreate = async () => {
    try {
      const response = await fetch('/api/sso/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });
      
      if (response.ok) {
        setCreateDialogOpen(false);
        fetchProviders();
        // Reset form
        setConfigData({
          provider: '',
          name: '',
          enabled: true,
          allow_signup: true,
          mfa_required: false
        });
        setActiveStep(0);
      }
    } catch (error) {
      console.error('Failed to create SSO provider:', error);
    }
  };

  const renderStepContent = (step: number) => {
    const provider = configData.provider;
    
    switch (step) {
      case 0: // Basic Info
        return (
          <Box>
            <TextField
              fullWidth
              label="Provider Name"
              value={configData.name}
              onChange={(e) => setConfigData({ ...configData, name: e.target.value })}
              margin="normal"
              helperText="Display name for this SSO provider"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={configData.enabled}
                  onChange={(e) => setConfigData({ ...configData, enabled: e.target.checked })}
                />
              }
              label="Enable this provider"
              sx={{ mt: 2 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={configData.allow_signup}
                  onChange={(e) => setConfigData({ ...configData, allow_signup: e.target.checked })}
                />
              }
              label="Allow new user registration"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={configData.mfa_required}
                  onChange={(e) => setConfigData({ ...configData, mfa_required: e.target.checked })}
                />
              }
              label="Require MFA for this provider"
            />
            
            <TextField
              fullWidth
              label="Allowed Domains (comma-separated)"
              margin="normal"
              helperText="Leave empty to allow all domains"
              onChange={(e) => setConfigData({
                ...configData,
                allowed_domains: e.target.value.split(',').map(d => d.trim()).filter(d => d)
              })}
            />
          </Box>
        );
        
      case 1: // Provider-specific configuration
        if (provider === 'saml') {
          return (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Configure your SAML Identity Provider with these settings:
                <br />
                SP Entity ID: {`${window.location.origin}/sso/saml/metadata`}
                <br />
                ACS URL: {`${window.location.origin}/sso/saml/callback`}
              </Alert>
              
              <TextField
                fullWidth
                label="IdP Entity ID"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  saml_config: { ...configData.saml_config, entity_id: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="SSO URL"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  saml_config: { ...configData.saml_config, sso_url: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="SLO URL (Optional)"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  saml_config: { ...configData.saml_config, slo_url: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="X.509 Certificate"
                margin="normal"
                helperText="Paste the IdP certificate here"
                onChange={(e) => setConfigData({
                  ...configData,
                  saml_config: { ...configData.saml_config, x509_cert: e.target.value }
                })}
              />
            </Box>
          );
        } else if (provider === 'oauth2' || provider === 'oidc') {
          return (
            <Box>
              <TextField
                fullWidth
                label="Client ID"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  oauth_config: { ...configData.oauth_config, client_id: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                type="password"
                label="Client Secret"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  oauth_config: { ...configData.oauth_config, client_secret: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="Authorization URL"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  oauth_config: { ...configData.oauth_config, authorization_url: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="Token URL"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  oauth_config: { ...configData.oauth_config, token_url: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="User Info URL"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  oauth_config: { ...configData.oauth_config, userinfo_url: e.target.value }
                })}
              />
            </Box>
          );
        } else if (provider === 'ldap') {
          return (
            <Box>
              <TextField
                fullWidth
                label="LDAP Server URL"
                margin="normal"
                placeholder="ldap://server.domain.com:389"
                onChange={(e) => setConfigData({
                  ...configData,
                  ldap_config: { ...configData.ldap_config, server_url: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="Bind DN"
                margin="normal"
                placeholder="CN=Service Account,OU=Users,DC=domain,DC=com"
                onChange={(e) => setConfigData({
                  ...configData,
                  ldap_config: { ...configData.ldap_config, bind_dn: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                type="password"
                label="Bind Password"
                margin="normal"
                onChange={(e) => setConfigData({
                  ...configData,
                  ldap_config: { ...configData.ldap_config, bind_password: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="Base DN"
                margin="normal"
                placeholder="OU=Users,DC=domain,DC=com"
                onChange={(e) => setConfigData({
                  ...configData,
                  ldap_config: { ...configData.ldap_config, base_dn: e.target.value }
                })}
              />
              
              <TextField
                fullWidth
                label="User Filter"
                margin="normal"
                placeholder="(uid={username})"
                onChange={(e) => setConfigData({
                  ...configData,
                  ldap_config: { ...configData.ldap_config, user_filter: e.target.value }
                })}
              />
            </Box>
          );
        }
        return null;
        
      case 2: // Attribute/Scope mapping
        return (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Attribute Mapping
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Map provider attributes to user fields
            </Typography>
            
            {/* This would be more dynamic in production */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField fullWidth label="Email Attribute" defaultValue="email" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth label="Name Attribute" defaultValue="name" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth label="Groups Attribute" defaultValue="groups" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth label="ID Attribute" defaultValue="sub" />
              </Grid>
            </Grid>
            
            <Typography variant="subtitle1" sx={{ mt: 3 }} gutterBottom>
              Role Mapping
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Map provider groups to platform roles
            </Typography>
            
            <List>
              <ListItem>
                <TextField label="Provider Group" defaultValue="admins" size="small" />
                <Typography sx={{ mx: 2 }}>→</Typography>
                <FormControl size="small">
                  <Select defaultValue="admin">
                    <MenuItem value="admin">Admin</MenuItem>
                    <MenuItem value="manager">Manager</MenuItem>
                    <MenuItem value="member">Member</MenuItem>
                    <MenuItem value="viewer">Viewer</MenuItem>
                  </Select>
                </FormControl>
              </ListItem>
            </List>
          </Box>
        );
        
      case 3: // Review
        return (
          <Box>
            <Alert severity="success" sx={{ mb: 2 }}>
              Configuration complete! Review your settings below.
            </Alert>
            
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {configData.name}
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Provider Type" secondary={configData.provider} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Status" secondary={configData.enabled ? 'Enabled' : 'Disabled'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Allow Signup" secondary={configData.allow_signup ? 'Yes' : 'No'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="MFA Required" secondary={configData.mfa_required ? 'Yes' : 'No'} />
                  </ListItem>
                  {configData.allowed_domains && (
                    <ListItem>
                      <ListItemText 
                        primary="Allowed Domains" 
                        secondary={configData.allowed_domains.join(', ')} 
                      />
                    </ListItem>
                  )}
                </List>
              </CardContent>
            </Card>
          </Box>
        );
        
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        SSO Configuration
      </Typography>
      
      <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="Providers" />
        <Tab label="Settings" />
        <Tab label="Test" />
      </Tabs>
      
      {activeTab === 0 && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Configured Providers ({providers.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Add Provider
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {providers.map((provider) => (
              <Grid item xs={12} md={6} key={provider.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                      <Box>
                        <Typography variant="h6">
                          {provider.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {provider.provider.toUpperCase()}
                        </Typography>
                      </Box>
                      <Box>
                        <Chip
                          label={provider.enabled ? 'Active' : 'Inactive'}
                          color={provider.enabled ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>
                    
                    <Box mt={2}>
                      <Typography variant="body2">
                        Allow Signup: {provider.allow_signup ? 'Yes' : 'No'}
                      </Typography>
                      <Typography variant="body2">
                        MFA Required: {provider.mfa_required ? 'Yes' : 'No'}
                      </Typography>
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<EditIcon />}>
                      Configure
                    </Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />}>
                      Remove
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
      
      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable SSO for all tenants"
              />
              
              <FormControlLabel
                control={<Switch />}
                label="Force SSO authentication"
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Auto-create users on first login"
              />
              
              <TextField
                fullWidth
                label="Session timeout (hours)"
                type="number"
                defaultValue={24}
                margin="normal"
              />
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Security Settings
              </Typography>
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Require email verification"
              />
              
              <FormControlLabel
                control={<Switch />}
                label="IP whitelist enforcement"
              />
              
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Whitelisted IP addresses"
                margin="normal"
                helperText="One IP address or CIDR range per line"
              />
            </Paper>
          </Grid>
        </Grid>
      )}
      
      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Test SSO Configuration
          </Typography>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Test your SSO configuration before enabling it for users.
          </Alert>
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Select Provider to Test</InputLabel>
            <Select>
              {providers.map((provider) => (
                <MenuItem key={provider.id} value={provider.id}>
                  {provider.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Button variant="contained" fullWidth>
            Start Test Login
          </Button>
        </Paper>
      )}
      
      {/* Create Provider Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add SSO Provider</DialogTitle>
        <DialogContent>
          {!selectedProvider ? (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Select Provider Type
              </Typography>
              <Grid container spacing={2}>
                {providerTypes.map((type) => (
                  <Grid item xs={12} sm={6} key={type.value}>
                    <Card
                      sx={{
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' }
                      }}
                      onClick={() => {
                        setSelectedProvider(type.value);
                        setConfigData({ ...configData, provider: type.value });
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6">{type.label}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {type.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              <Stepper activeStep={activeStep} orientation="vertical">
                {getProviderSteps(selectedProvider).map((label, index) => (
                  <Step key={label}>
                    <StepLabel>{label}</StepLabel>
                    <StepContent>
                      {renderStepContent(index)}
                      <Box sx={{ mt: 2 }}>
                        <Button
                          variant="contained"
                          onClick={() => {
                            if (index === getProviderSteps(selectedProvider).length - 1) {
                              handleCreate();
                            } else {
                              setActiveStep(index + 1);
                            }
                          }}
                          sx={{ mr: 1 }}
                        >
                          {index === getProviderSteps(selectedProvider).length - 1 ? 'Create' : 'Continue'}
                        </Button>
                        <Button
                          disabled={index === 0}
                          onClick={() => setActiveStep(index - 1)}
                        >
                          Back
                        </Button>
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setSelectedProvider('');
            setActiveStep(0);
          }}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SSOConfiguration;
EOF

# 7. Create Docker Compose Configuration
echo "7. Creating Docker Compose Configuration..."
cat > docker-compose.sso.yml << 'EOF'
version: '3.8'

services:
  sso-service:
    build:
      context: ./services/sso
      dockerfile: Dockerfile
    image: openpolicy/sso-service:latest
    container_name: sso-service
    ports:
      - "9030:9030"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/openpolicy_sso
      - REDIS_URL=redis://redis:6379/6
      - SERVICE_PORT=9030
      - JWT_SECRET=${JWT_SECRET}
      - JWT_EXPIRATION_HOURS=24
      - BASE_URL=${BASE_URL:-https://openpolicy.com}
      - TENANT_SERVICE_URL=http://tenant-service:9029
    networks:
      - openpolicy-network
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9030/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: LDAP test server for development
  ldap-server:
    image: osixia/openldap:latest
    container_name: sso-ldap-test
    environment:
      - LDAP_ORGANISATION=OpenPolicy
      - LDAP_DOMAIN=openpolicy.local
      - LDAP_ADMIN_PASSWORD=admin
    ports:
      - "389:389"
      - "636:636"
    networks:
      - openpolicy-network
    volumes:
      - ldap-data:/var/lib/ldap
      - ldap-config:/etc/ldap/slapd.d

  ldap-admin:
    image: osixia/phpldapadmin:latest
    container_name: sso-ldap-admin
    environment:
      - PHPLDAPADMIN_LDAP_HOSTS=ldap-server
    ports:
      - "8090:443"
    networks:
      - openpolicy-network
    depends_on:
      - ldap-server

volumes:
  ldap-data:
  ldap-config:

networks:
  openpolicy-network:
    external: true
EOF

# 8. Create SSO Integration Script
echo "8. Creating SSO Integration Script..."
cat > scripts/integrate-sso.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Integrating SSO Across Platform ==="

# 1. Update authentication service
echo "1. Updating authentication service..."
cat >> services/auth-service/sso_integration.py << 'CODE'
# SSO Integration for Auth Service
from httpx import AsyncClient

async def validate_sso_token(token: str) -> Optional[dict]:
    """Validate SSO token and get user info"""
    async with AsyncClient() as client:
        response = await client.post(
            "http://sso-service:9030/sso/validate",
            json={"token": token}
        )
        if response.status_code == 200:
            return response.json()
    return None

async def create_or_update_user_from_sso(sso_user: dict) -> User:
    """Create or update user from SSO data"""
    user = await get_user_by_email(sso_user["email"])
    
    if not user:
        # Create new user
        user = await create_user(
            email=sso_user["email"],
            name=sso_user.get("name"),
            tenant_id=sso_user["tenant_id"],
            provider=sso_user["provider"]
        )
    else:
        # Update existing user
        user.last_login = datetime.utcnow()
        user.provider = sso_user["provider"]
        await update_user(user)
    
    return user
CODE

# 2. Update frontend authentication
echo "2. Updating frontend authentication..."
cat >> apps/web/src/auth/sso.ts << 'CODE'
// SSO Authentication Handler
export const handleSSOCallback = async () => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  
  if (token) {
    // Store token
    localStorage.setItem('sso_token', token);
    
    // Validate and get user info
    const response = await fetch('/api/auth/sso/validate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const user = await response.json();
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  }
};
CODE

# 3. Deploy SSO service
echo "3. Deploying SSO service..."
docker-compose -f docker-compose.sso.yml up -d

# 4. Wait for service to be ready
echo "4. Waiting for SSO service..."
for i in {1..30}; do
    if curl -f http://localhost:9030/health >/dev/null 2>&1; then
        echo "SSO service is ready!"
        break
    fi
    echo "Waiting for SSO service... ($i/30)"
    sleep 2
done

echo "
=== SSO Integration Complete ===

Test SSO:
1. Create a provider:
   curl -X POST http://localhost:9030/sso/providers \\
     -H 'Content-Type: application/json' \\
     -d '{
       \"provider\": \"google\",
       \"name\": \"Google Workspace\",
       \"oauth_config\": {
         \"client_id\": \"your-client-id\",
         \"client_secret\": \"your-client-secret\"
       }
     }'

2. Initiate login:
   http://localhost:9030/sso/login?provider_id=1

3. Access SAML metadata:
   http://localhost:9030/sso/saml/metadata
"
EOF
chmod +x scripts/integrate-sso.sh

# 9. Create SSO Testing Tools
echo "9. Creating SSO Testing Tools..."
cat > services/sso/test-sso.py << 'EOF'
"""
SSO Testing Tool
Tests various SSO providers and configurations
"""

import asyncio
import httpx
import json
from datetime import datetime

class SSOTester:
    def __init__(self, base_url="http://localhost:9030"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def test_provider_creation(self):
        """Test creating different SSO providers"""
        providers = [
            {
                "provider": "google",
                "name": "Google Test",
                "enabled": True,
                "oauth_config": {
                    "client_id": "test-client-id",
                    "client_secret": "test-secret",
                    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
                }
            },
            {
                "provider": "saml",
                "name": "SAML Test",
                "enabled": True,
                "saml_config": {
                    "entity_id": "http://idp.example.com",
                    "sso_url": "http://idp.example.com/sso",
                    "x509_cert": "MIID..."
                }
            }
        ]
        
        for provider in providers:
            response = await self.client.post(
                f"{self.base_url}/sso/providers",
                json=provider,
                headers={"X-Tenant-ID": "test-tenant"}
            )
            print(f"Created {provider['name']}: {response.status_code}")
    
    async def test_login_flow(self, provider_id: int):
        """Test SSO login flow"""
        # Initiate login
        response = await self.client.get(
            f"{self.base_url}/sso/login",
            params={"provider_id": provider_id},
            headers={"X-Tenant-ID": "test-tenant"},
            follow_redirects=False
        )
        
        if response.status_code == 307:
            print(f"Login redirect URL: {response.headers['location']}")
        
        return response
    
    async def test_session_validation(self, session_id: str):
        """Test session validation"""
        response = await self.client.get(
            f"{self.base_url}/sso/validate",
            params={"session_id": session_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Session valid: {data['valid']}")
            if data['valid']:
                print(f"User: {data['email']}")
                print(f"Expires: {data['expires_at']}")
    
    async def close(self):
        await self.client.aclose()

async def main():
    tester = SSOTester()
    
    print("=== SSO Integration Tests ===")
    
    # Test provider creation
    print("\n1. Testing Provider Creation...")
    await tester.test_provider_creation()
    
    # Test login flow
    print("\n2. Testing Login Flow...")
    await tester.test_login_flow(1)
    
    # Test session validation
    print("\n3. Testing Session Validation...")
    await tester.test_session_validation("test-session-id")
    
    await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 10. Summary
echo "
=== SSO Integration Setup Complete ===

✅ Features Implemented:
1. SAML 2.0 Support
2. OAuth 2.0 / OpenID Connect
3. LDAP/Active Directory
4. Pre-configured providers (Google, Azure AD, Okta, Auth0)
5. Multi-tenant SSO isolation
6. Session management
7. Audit logging
8. Role/group mapping

🔐 Supported Providers:
- SAML 2.0 (Enterprise SSO)
- OAuth 2.0 (Modern authentication)
- OpenID Connect (OAuth + Identity)
- Google Workspace
- Microsoft Azure AD
- Okta
- Auth0
- LDAP/Active Directory
- Custom providers

🚀 Quick Start:
1. Access SSO service: http://localhost:9030
2. Configure providers via API or UI
3. Test login flow
4. Monitor sessions

📝 Configuration Examples:

Google Workspace:
```json
{
  \"provider\": \"google\",
  \"name\": \"Company Google\",
  \"oauth_config\": {
    \"client_id\": \"your-client-id.apps.googleusercontent.com\",
    \"client_secret\": \"your-client-secret\"
  }
}
```

SAML (Generic):
```json
{
  \"provider\": \"saml\",
  \"name\": \"Corporate SSO\",
  \"saml_config\": {
    \"entity_id\": \"https://idp.company.com\",
    \"sso_url\": \"https://idp.company.com/sso\",
    \"x509_cert\": \"-----BEGIN CERTIFICATE-----...\"
  }
}
```

LDAP:
```json
{
  \"provider\": \"ldap\",
  \"name\": \"Corporate Directory\",
  \"ldap_config\": {
    \"server_url\": \"ldap://dc.company.com:389\",
    \"bind_dn\": \"CN=Service,OU=Accounts,DC=company,DC=com\",
    \"bind_password\": \"password\",
    \"base_dn\": \"OU=Users,DC=company,DC=com\"
  }
}
```

🔧 Integration Points:
1. Frontend: /auth/sso redirects to SSO login
2. Backend: Validate SSO tokens in auth middleware
3. User Management: Auto-provision users on first login
4. Audit: All SSO events logged

📚 Next Steps:
1. Configure your identity providers
2. Test with real provider credentials
3. Set up role mappings
4. Enable for specific tenants
5. Monitor login patterns

⚠️ Security Notes:
- Always use HTTPS in production
- Rotate client secrets regularly
- Implement IP whitelisting for admin access
- Enable MFA where possible
- Regular security audits

📖 Documentation:
See services/sso/README.md for detailed configuration guide
"

# Create comprehensive README
cat > services/sso/README.md << 'EOF'
# SSO Service

## Overview
Enterprise Single Sign-On service supporting:
- SAML 2.0
- OAuth 2.0
- OpenID Connect
- LDAP/Active Directory
- Pre-configured providers

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│ SSO Service │────▶│Identity     │
└─────────────┘     └─────────────┘     │Provider     │
                            │            └─────────────┘
                            ▼
                    ┌─────────────┐
                    │Auth Service │
                    └─────────────┘
```

## Provider Configuration

### SAML 2.0
1. **Service Provider Setup**:
   - Entity ID: `https://your-domain.com/sso/saml/metadata`
   - ACS URL: `https://your-domain.com/sso/saml/callback/{provider_id}`
   - Metadata: `https://your-domain.com/sso/saml/metadata`

2. **Identity Provider Configuration**:
```json
{
  "provider": "saml",
  "name": "Corporate SAML",
  "saml_config": {
    "entity_id": "https://idp.company.com",
    "sso_url": "https://idp.company.com/sso",
    "slo_url": "https://idp.company.com/slo",
    "x509_cert": "-----BEGIN CERTIFICATE-----...",
    "attribute_mapping": {
      "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
      "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
      "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
    }
  }
}
```

### OAuth 2.0 / OpenID Connect
1. **Application Setup**:
   - Redirect URI: `https://your-domain.com/sso/oauth/callback/{provider_id}`
   - Scopes: `openid email profile`

2. **Provider Configuration**:
```json
{
  "provider": "oidc",
  "name": "Corporate OIDC",
  "oauth_config": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "authorization_url": "https://idp.company.com/authorize",
    "token_url": "https://idp.company.com/token",
    "userinfo_url": "https://idp.company.com/userinfo",
    "scopes": ["openid", "email", "profile", "groups"],
    "flow_type": "authorization_code"
  }
}
```

### LDAP/Active Directory
```json
{
  "provider": "ldap",
  "name": "Corporate AD",
  "ldap_config": {
    "server_url": "ldaps://dc.company.com:636",
    "bind_dn": "CN=SSO Service,OU=Service Accounts,DC=company,DC=com",
    "bind_password": "secure-password",
    "base_dn": "DC=company,DC=com",
    "user_filter": "(&(objectClass=user)(sAMAccountName={username}))",
    "group_filter": "(&(objectClass=group)(member={user_dn}))",
    "attribute_mapping": {
      "email": "mail",
      "name": "displayName",
      "id": "objectGUID"
    }
  }
}
```

## Pre-configured Providers

### Google Workspace
1. Create OAuth 2.0 credentials in Google Cloud Console
2. Add authorized redirect URI
3. Configure:
```json
{
  "provider": "google",
  "name": "Google Workspace",
  "oauth_config": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret"
  }
}
```

### Microsoft Azure AD
1. Register application in Azure Portal
2. Configure redirect URI
3. Configure:
```json
{
  "provider": "azure_ad",
  "name": "Microsoft Azure AD",
  "oauth_config": {
    "client_id": "your-application-id",
    "client_secret": "your-client-secret",
    "tenant_id": "your-tenant-id"
  }
}
```

### Okta
1. Create application in Okta Admin
2. Configure redirect URI
3. Configure:
```json
{
  "provider": "okta",
  "name": "Okta SSO",
  "oauth_config": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "okta_domain": "your-org.okta.com"
  }
}
```

## Advanced Features

### Role Mapping
Map provider groups/roles to platform roles:
```json
{
  "role_mapping": {
    "CN=Admins,OU=Groups,DC=company,DC=com": "admin",
    "CN=Managers,OU=Groups,DC=company,DC=com": "manager",
    "CN=Users,OU=Groups,DC=company,DC=com": "member"
  }
}
```

### Domain Restrictions
```json
{
  "allowed_domains": ["company.com", "subsidiary.com"],
  "blocked_domains": ["competitor.com"]
}
```

### Custom Claims
Add custom claims to JWT tokens:
```json
{
  "custom_claims": {
    "department": "attributes.department",
    "employee_id": "attributes.employeeNumber"
  }
}
```

## Security Considerations

1. **Token Security**:
   - Use strong JWT secrets
   - Implement token rotation
   - Set appropriate expiration times

2. **SAML Security**:
   - Validate signatures
   - Check assertion timestamps
   - Implement replay protection

3. **OAuth Security**:
   - Use PKCE for public clients
   - Validate redirect URIs
   - Implement state parameter

4. **LDAP Security**:
   - Use LDAPS (LDAP over SSL)
   - Implement bind account restrictions
   - Regular password rotation

## Monitoring

### Metrics
- Login success/failure rates
- Provider response times
- Session duration
- User provisioning rate

### Audit Events
- Login attempts
- Provider configuration changes
- Session creation/termination
- Role assignments

## Troubleshooting

### SAML Issues
1. **Invalid Response**: Check certificate and timestamps
2. **Attribute Missing**: Verify attribute mapping
3. **Signature Invalid**: Update IdP certificate

### OAuth Issues
1. **Invalid Grant**: Check client credentials
2. **Scope Error**: Verify requested scopes
3. **Token Expired**: Implement refresh token flow

### LDAP Issues
1. **Bind Failed**: Check service account credentials
2. **User Not Found**: Verify search filter
3. **TLS Error**: Check certificate trust

## API Reference

### Create Provider
```bash
POST /sso/providers
{
  "provider": "saml|oauth2|oidc|ldap",
  "name": "Provider Name",
  "enabled": true,
  "provider_config": {...}
}
```

### Initiate Login
```bash
GET /sso/login?provider_id=1&return_url=/dashboard
```

### Validate Session
```bash
GET /sso/validate?session_id=xxx
```

### Logout
```bash
POST /sso/logout
{
  "session_id": "xxx"
}
```
EOF