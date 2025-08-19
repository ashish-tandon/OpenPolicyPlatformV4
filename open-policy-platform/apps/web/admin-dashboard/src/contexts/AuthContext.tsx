import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  lastLogin: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async (): Promise<boolean> => {
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setLoading(false);
        return false;
      }

      // Verify token with backend
      const response = await fetch('/api/auth/verify', {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setToken(storedToken);
        setLoading(false);
        return true;
      } else {
        // Token is invalid
        localStorage.removeItem('token');
        setUser(null);
        setToken(null);
        setLoading(false);
        return false;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setLoading(false);
      return false;
    }
  };

  const login = (userData: User, authToken: string) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    
    // Log login event
    logActivity('login', { userId: userData.id, timestamp: new Date().toISOString() });
  };

  const logout = async () => {
    try {
      // Call logout endpoint
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    }

    // Clear local state
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    
    // Log logout event
    if (user) {
      logActivity('logout', { userId: user.id, timestamp: new Date().toISOString() });
    }

    // Redirect to login
    navigate('/login');
  };

  const updateUser = (updates: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updates });
    }
  };

  // Activity logging helper
  const logActivity = async (action: string, details: any) => {
    try {
      await fetch('/api/audit/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          action,
          details,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Failed to log activity:', error);
    }
  };

  // Token refresh logic
  useEffect(() => {
    if (!token) return;

    // Set up token refresh interval (refresh every 50 minutes for 1-hour tokens)
    const refreshInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setToken(data.token);
          localStorage.setItem('token', data.token);
        } else {
          // Refresh failed, logout user
          logout();
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }, 50 * 60 * 1000); // 50 minutes

    return () => clearInterval(refreshInterval);
  }, [token]);

  // Session timeout warning
  useEffect(() => {
    if (!user) return;

    let warningTimer: NodeJS.Timeout;
    let logoutTimer: NodeJS.Timeout;

    const resetTimers = () => {
      clearTimeout(warningTimer);
      clearTimeout(logoutTimer);

      // Warn after 25 minutes of inactivity
      warningTimer = setTimeout(() => {
        if (window.confirm('Your session will expire in 5 minutes. Do you want to continue?')) {
          checkAuth(); // Refresh session
          resetTimers();
        }
      }, 25 * 60 * 1000);

      // Auto logout after 30 minutes of inactivity
      logoutTimer = setTimeout(() => {
        logout();
      }, 30 * 60 * 1000);
    };

    // Track user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, resetTimers);
    });

    resetTimers();

    return () => {
      clearTimeout(warningTimer);
      clearTimeout(logoutTimer);
      events.forEach(event => {
        document.removeEventListener(event, resetTimers);
      });
    };
  }, [user]);

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    updateUser,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;