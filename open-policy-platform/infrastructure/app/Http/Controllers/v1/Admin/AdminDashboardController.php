<?php

namespace App\Http\Controllers\v1\Admin;

use App\Http\Controllers\Controller;
use App\Models\Bill;
use App\Models\Issue;
use App\Models\User;
use App\Models\Representative;
use App\Models\Vote;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class AdminDashboardController extends Controller
{
    /**
     * Get dashboard statistics for admin
     */
    public function getDashboardStats(Request $request)
    {
        try {
            // Get various statistics
            $totalUsers = User::count();
            $totalBills = Bill::count();
            $totalIssues = Issue::count();
            $totalRepresentatives = Representative::count();
            $totalVotes = Vote::count();
            
            // Get recent activity counts
            $recentUsers = User::where('created_at', '>=', now()->subDays(7))->count();
            $recentBills = Bill::where('created_at', '>=', now()->subDays(7))->count();
            
            // Get scraper status (this is a placeholder - adjust based on your actual scraper implementation)
            $totalScrapers = 5; // Number of configured scrapers
            $activeScrapers = 3; // Number of currently active scrapers
            
            // Get last update time
            $lastUpdate = DB::table('bills')
                ->latest('updated_at')
                ->value('updated_at') ?? now();
            
            return response()->json([
                'success' => true,
                'data' => [
                    'totalPolicies' => $totalBills,
                    'totalScrapers' => $totalScrapers,
                    'activeScrapers' => $activeScrapers,
                    'lastUpdate' => $lastUpdate,
                    'statistics' => [
                        'users' => [
                            'total' => $totalUsers,
                            'recent' => $recentUsers
                        ],
                        'bills' => [
                            'total' => $totalBills,
                            'recent' => $recentBills
                        ],
                        'issues' => [
                            'total' => $totalIssues
                        ],
                        'representatives' => [
                            'total' => $totalRepresentatives
                        ],
                        'votes' => [
                            'total' => $totalVotes
                        ]
                    ]
                ]
            ], 200);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch dashboard statistics',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Get system health status
     */
    public function getSystemHealth(Request $request)
    {
        try {
            // Check database connection
            $dbHealthy = true;
            try {
                DB::connection()->getPdo();
            } catch (\Exception $e) {
                $dbHealthy = false;
            }
            
            // Check cache connection (if using Redis)
            $cacheHealthy = true;
            try {
                cache()->ping();
            } catch (\Exception $e) {
                $cacheHealthy = false;
            }
            
            return response()->json([
                'success' => true,
                'data' => [
                    'status' => $dbHealthy && $cacheHealthy ? 'healthy' : 'degraded',
                    'services' => [
                        'database' => $dbHealthy ? 'operational' : 'down',
                        'cache' => $cacheHealthy ? 'operational' : 'down',
                        'api' => 'operational'
                    ],
                    'timestamp' => now()->toIso8601String()
                ]
            ], 200);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to check system health',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}