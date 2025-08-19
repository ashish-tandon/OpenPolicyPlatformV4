import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

interface Bill {
  id: number;
  bill_number: string;
  title: string;
  summary: string;
  status: string;
  sponsor: string;
  introduction_date: string;
  latest_activity_date: string;
}

interface Representative {
  id: number;
  name: string;
  party: string;
  constituency: string;
  email: string;
  photo_url: string;
}

interface Vote {
  id: number;
  bill_number: string;
  vote_date: string;
  result: string;
  yeas: number;
  nays: number;
}

const UserDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('bills');
  const [bills, setBills] = useState<Bill[]>([]);
  const [representatives, setRepresentatives] = useState<Representative[]>([]);
  const [votes, setVotes] = useState<Vote[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Authorization': token ? `Bearer ${token}` : '',
      };

      switch (activeTab) {
        case 'bills':
          const billsRes = await fetch('/api/v1/bills', { headers });
          if (billsRes.ok) {
            const data = await billsRes.json();
            setBills(data.bills || []);
          }
          break;
        case 'representatives':
          const repsRes = await fetch('/api/v1/representatives', { headers });
          if (repsRes.ok) {
            const data = await repsRes.json();
            setRepresentatives(data.representatives || []);
          }
          break;
        case 'votes':
          const votesRes = await fetch('/api/v1/votes', { headers });
          if (votesRes.ok) {
            const data = await votesRes.json();
            setVotes(data.votes || []);
          }
          break;
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'First Reading': 'bg-blue-100 text-blue-800',
      'Second Reading': 'bg-yellow-100 text-yellow-800',
      'Committee': 'bg-purple-100 text-purple-800',
      'Third Reading': 'bg-orange-100 text-orange-800',
      'Royal Assent': 'bg-green-100 text-green-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPartyColor = (party: string) => {
    const colors: { [key: string]: string } = {
      'Liberal': 'bg-red-500',
      'Conservative': 'bg-blue-500',
      'NDP': 'bg-orange-500',
      'Bloc Québécois': 'bg-cyan-500',
      'Green': 'bg-green-500',
    };
    return colors[party] || 'bg-gray-500';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Open Policy Platform
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {user?.username || 'User'}
              </span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['bills', 'representatives', 'votes'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {/* Bills Tab */}
            {activeTab === 'bills' && (
              <div className="space-y-6">
                <div className="bg-white shadow rounded-lg">
                  <div className="px-6 py-4 border-b">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Parliamentary Bills
                    </h2>
                  </div>
                  <div className="divide-y">
                    {bills.map((bill) => (
                      <div key={bill.id} className="p-6 hover:bg-gray-50">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h3 className="text-lg font-medium text-gray-900">
                                {bill.bill_number}
                              </h3>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(bill.status)}`}>
                                {bill.status}
                              </span>
                            </div>
                            <p className="mt-1 text-gray-600">{bill.title}</p>
                            <p className="mt-2 text-sm text-gray-500">{bill.summary}</p>
                            <div className="mt-3 text-sm text-gray-500">
                              <span>Sponsor: {bill.sponsor}</span>
                              <span className="mx-2">•</span>
                              <span>Introduced: {new Date(bill.introduction_date).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <button className="ml-4 text-blue-600 hover:text-blue-800 text-sm font-medium">
                            View Details →
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Representatives Tab */}
            {activeTab === 'representatives' && (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {representatives.map((rep) => (
                  <div key={rep.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                    <div className="p-6">
                      <div className="flex items-start space-x-4">
                        <img
                          className="h-16 w-16 rounded-full object-cover"
                          src={rep.photo_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(rep.name)}&background=random`}
                          alt={rep.name}
                        />
                        <div className="flex-1">
                          <h3 className="text-lg font-medium text-gray-900">
                            {rep.name}
                          </h3>
                          <div className="mt-1 flex items-center space-x-2">
                            <span className={`inline-block h-2 w-2 rounded-full ${getPartyColor(rep.party)}`}></span>
                            <span className="text-sm text-gray-600">{rep.party}</span>
                          </div>
                          <p className="mt-1 text-sm text-gray-500">
                            {rep.constituency}
                          </p>
                          <a
                            href={`mailto:${rep.email}`}
                            className="mt-3 inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                          >
                            Contact →
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Votes Tab */}
            {activeTab === 'votes' && (
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Recent Votes
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Bill
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Result
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Yeas
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Nays
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {votes.map((vote) => (
                        <tr key={vote.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {vote.bill_number}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(vote.vote_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              vote.result === 'Agreed To'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {vote.result}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {vote.yeas}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {vote.nays}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default UserDashboard;