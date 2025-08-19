<?php

namespace App\Http\Controllers\v1;

use App\Http\Controllers\Controller;
use App\Models\Bill;
use App\Models\Representative;
use App\Models\Vote;
use App\Models\Committee;
use App\Models\Debate;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

class PublicDataController extends Controller
{
    /**
     * Get list of bills
     */
    public function getBills(Request $request)
    {
        try {
            $perPage = $request->get('per_page', 20);
            $status = $request->get('status');
            $search = $request->get('search');
            
            $query = Bill::query();
            
            if ($status) {
                $query->where('status', $status);
            }
            
            if ($search) {
                $query->where(function($q) use ($search) {
                    $q->where('bill_number', 'LIKE', "%{$search}%")
                      ->orWhere('title', 'LIKE', "%{$search}%")
                      ->orWhere('summary', 'LIKE', "%{$search}%");
                });
            }
            
            $bills = $query->orderBy('latest_activity_date', 'desc')
                          ->paginate($perPage);
            
            return response()->json([
                'success' => true,
                'bills' => $bills->items(),
                'pagination' => [
                    'total' => $bills->total(),
                    'per_page' => $bills->perPage(),
                    'current_page' => $bills->currentPage(),
                    'last_page' => $bills->lastPage()
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch bills',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Get single bill details
     */
    public function getBill($id)
    {
        try {
            $bill = Bill::findOrFail($id);
            
            // Get related votes
            $votes = Vote::where('bill_id', $id)
                        ->orderBy('vote_date', 'desc')
                        ->get();
            
            return response()->json([
                'success' => true,
                'bill' => $bill,
                'votes' => $votes
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Bill not found',
                'error' => $e->getMessage()
            ], 404);
        }
    }
    
    /**
     * Get list of representatives
     */
    public function getRepresentatives(Request $request)
    {
        try {
            $party = $request->get('party');
            $province = $request->get('province');
            $search = $request->get('search');
            
            $query = Representative::where('active', true);
            
            if ($party) {
                $query->where('party', $party);
            }
            
            if ($province) {
                $query->where('province', $province);
            }
            
            if ($search) {
                $query->where(function($q) use ($search) {
                    $q->where('name', 'LIKE', "%{$search}%")
                      ->orWhere('constituency', 'LIKE', "%{$search}%");
                });
            }
            
            $representatives = $query->orderBy('name')
                                   ->get();
            
            // Cache for 1 hour
            $cacheKey = 'representatives:' . md5(json_encode($request->all()));
            Cache::put($cacheKey, $representatives, 3600);
            
            return response()->json([
                'success' => true,
                'representatives' => $representatives,
                'total' => $representatives->count()
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch representatives',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Get representative details
     */
    public function getRepresentative($id)
    {
        try {
            $representative = Representative::findOrFail($id);
            
            // Get their activity
            $activities = $representative->activityLogs()
                                       ->orderBy('created_at', 'desc')
                                       ->limit(10)
                                       ->get();
            
            return response()->json([
                'success' => true,
                'representative' => $representative,
                'recent_activities' => $activities
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Representative not found',
                'error' => $e->getMessage()
            ], 404);
        }
    }
    
    /**
     * Get list of votes
     */
    public function getVotes(Request $request)
    {
        try {
            $perPage = $request->get('per_page', 20);
            $dateFrom = $request->get('date_from');
            $dateTo = $request->get('date_to');
            
            $query = Vote::query();
            
            if ($dateFrom) {
                $query->where('vote_date', '>=', $dateFrom);
            }
            
            if ($dateTo) {
                $query->where('vote_date', '<=', $dateTo);
            }
            
            $votes = $query->with('bill')
                         ->orderBy('vote_date', 'desc')
                         ->paginate($perPage);
            
            return response()->json([
                'success' => true,
                'votes' => $votes->items(),
                'pagination' => [
                    'total' => $votes->total(),
                    'per_page' => $votes->perPage(),
                    'current_page' => $votes->currentPage(),
                    'last_page' => $votes->lastPage()
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch votes',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Get committees list
     */
    public function getCommittees(Request $request)
    {
        try {
            $committees = Committee::where('active', true)
                                 ->orderBy('name')
                                 ->get();
            
            return response()->json([
                'success' => true,
                'committees' => $committees
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch committees',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Get debates
     */
    public function getDebates(Request $request)
    {
        try {
            $perPage = $request->get('per_page', 20);
            
            $debates = Debate::orderBy('debate_date', 'desc')
                           ->paginate($perPage);
            
            return response()->json([
                'success' => true,
                'debates' => $debates->items(),
                'pagination' => [
                    'total' => $debates->total(),
                    'per_page' => $debates->perPage(),
                    'current_page' => $debates->currentPage(),
                    'last_page' => $debates->lastPage()
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch debates',
                'error' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Search across all data
     */
    public function search(Request $request)
    {
        try {
            $query = $request->get('q');
            
            if (!$query || strlen($query) < 3) {
                return response()->json([
                    'success' => false,
                    'message' => 'Search query must be at least 3 characters'
                ], 400);
            }
            
            // Search bills
            $bills = Bill::where('bill_number', 'LIKE', "%{$query}%")
                        ->orWhere('title', 'LIKE', "%{$query}%")
                        ->limit(5)
                        ->get();
            
            // Search representatives
            $representatives = Representative::where('name', 'LIKE', "%{$query}%")
                                           ->orWhere('constituency', 'LIKE', "%{$query}%")
                                           ->limit(5)
                                           ->get();
            
            // Search committees
            $committees = Committee::where('name', 'LIKE', "%{$query}%")
                                 ->limit(5)
                                 ->get();
            
            return response()->json([
                'success' => true,
                'results' => [
                    'bills' => $bills,
                    'representatives' => $representatives,
                    'committees' => $committees
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Search failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }
}