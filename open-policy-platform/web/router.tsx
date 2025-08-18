import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './src/App';
import Debates from './src/pages/debates';
import GovernmentBills from './src/pages/government-bills';
import HouseCommitte from './src/pages/house-committee';
import Mps from './src/pages/mps';
import Bills from './src/pages/bills';
import About from './src/pages/about';
import MPProfile from './src/pages/mps/[id]';
import FormerMps from './src/pages/mps/former-mp';
import DebateSearch from './src/pages/other/debtaes';
import BillSearch from './src/pages/other/bills';
import VotePage from './src/pages/vote';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        path: '/',
        element: <Navigate to="/bills" replace />,
      },
      {
        path: '/',
        element: <GovernmentBills />,
      },
      {
        path: '/debates',
        element: <Debates />,
      },
      {
        path: '/committees',
        element: <HouseCommitte />,
      },
      {
        path: '/mps',
        element: <Mps />,
      },
      {
        path: '/former-mps',
        element: <FormerMps />,
      },
      {
        path: '/bills',
        element: <GovernmentBills />,
      },
      {
        path: '/bills/:id',
        element: <Bills />,
      },
      {
        path: '/about',
        element: <About />,
      },
      {
        path: '/debates/*',
        element: <DebateSearch />,
      },
      {
        path: '/committees/*',
        element: <DebateSearch />,
      },
      {
        path: '/bills/*',
        element: <BillSearch />,
      },
      {
        path: '/mps/:id',
        element: <MPProfile />,
      },
      {
        path: '/votes/*',
        element: <VotePage />,
      },
    ],
  },
]);

export default router;
