// router.tsx
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';

import App from './src/App';
import GovernmentBills from './src/pages/government-bills';
import Login from './src/pages/auth/login';

// ✅ Utility for auth check
const isAuthenticated = () => !!localStorage.getItem('token');

// ✅ Protected wrapper: only allow if logged in
function ProtectedRoute() {
  return isAuthenticated() ? <Outlet /> : <Navigate to="/auth/login" replace />;
}

// ✅ Auth wrapper: only allow if NOT logged in
function AuthRoute() {
  return isAuthenticated() ? <Navigate to="/" replace /> : <Outlet />;
}

// ✅ Final router config
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      // Protected routes
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: '',
            element: <GovernmentBills />,
          },
        ],
      },

      // Auth routes
      {
        path: 'auth',
        element: <AuthRoute />,
        children: [
          {
            path: 'login',
            element: <Login />, // Replace with your actual login page
          },
        ],
      },

      // Catch-all (optional)
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

export default router;
