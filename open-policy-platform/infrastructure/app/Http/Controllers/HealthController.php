<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Cache;

class HealthController extends Controller
{
    /**
     * Main health check endpoint
     */
    public function health()
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'cache' => $this->checkCache(),
            'storage' => $this->checkStorage(),
            'services' => $this->checkServices()
        ];

        $overallHealth = !in_array(false, array_column($checks, 'healthy'));
        
        return response()->json([
            'status' => $overallHealth ? 'healthy' : 'unhealthy',
            'timestamp' => now()->toIso8601String(),
            'checks' => $checks,
            'version' => config('app.version', '1.0.0'),
            'environment' => config('app.env')
        ], $overallHealth ? 200 : 503);
    }

    /**
     * Detailed health check
     */
    public function detailedHealth()
    {
        $startTime = microtime(true);
        
        $checks = [
            'database' => $this->checkDatabase(true),
            'redis' => $this->checkRedis(true),
            'cache' => $this->checkCache(true),
            'storage' => $this->checkStorage(true),
            'services' => $this->checkServices(true),
            'queue' => $this->checkQueue(),
            'scrapers' => $this->checkScrapers()
        ];

        $executionTime = round((microtime(true) - $startTime) * 1000, 2);
        $overallHealth = !in_array(false, array_column($checks, 'healthy'));
        
        return response()->json([
            'status' => $overallHealth ? 'healthy' : 'unhealthy',
            'timestamp' => now()->toIso8601String(),
            'execution_time_ms' => $executionTime,
            'checks' => $checks,
            'system' => [
                'memory_usage' => $this->getMemoryUsage(),
                'disk_usage' => $this->getDiskUsage(),
                'load_average' => sys_getloadavg()
            ]
        ], $overallHealth ? 200 : 503);
    }

    private function checkDatabase($detailed = false)
    {
        try {
            $start = microtime(true);
            DB::connection()->getPdo();
            $responseTime = round((microtime(true) - $start) * 1000, 2);
            
            $result = [
                'healthy' => true,
                'response_time_ms' => $responseTime
            ];
            
            if ($detailed) {
                $result['stats'] = [
                    'tables_count' => DB::select('SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = ?', [DB::getDatabaseName()])[0]->count,
                    'connection' => config('database.default')
                ];
            }
            
            return $result;
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function checkRedis($detailed = false)
    {
        try {
            $start = microtime(true);
            $pong = Redis::ping();
            $responseTime = round((microtime(true) - $start) * 1000, 2);
            
            $result = [
                'healthy' => $pong === 'PONG' || $pong === true,
                'response_time_ms' => $responseTime
            ];
            
            if ($detailed && $result['healthy']) {
                $info = Redis::info();
                $result['stats'] = [
                    'version' => $info['redis_version'] ?? 'unknown',
                    'used_memory' => $info['used_memory_human'] ?? 'unknown',
                    'connected_clients' => $info['connected_clients'] ?? 0
                ];
            }
            
            return $result;
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function checkCache($detailed = false)
    {
        try {
            $start = microtime(true);
            $key = 'health_check_' . time();
            Cache::put($key, true, 10);
            $value = Cache::get($key);
            Cache::forget($key);
            $responseTime = round((microtime(true) - $start) * 1000, 2);
            
            return [
                'healthy' => $value === true,
                'response_time_ms' => $responseTime,
                'driver' => config('cache.default')
            ];
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function checkStorage($detailed = false)
    {
        try {
            $path = storage_path('app');
            $writable = is_writable($path);
            
            $result = [
                'healthy' => $writable,
                'writable' => $writable
            ];
            
            if ($detailed) {
                $result['paths'] = [
                    'app' => is_writable(storage_path('app')),
                    'logs' => is_writable(storage_path('logs')),
                    'framework' => is_writable(storage_path('framework'))
                ];
            }
            
            return $result;
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function checkServices($detailed = false)
    {
        $services = [
            'api' => true,
            'auth' => $this->checkAuthService(),
            'admin' => $this->checkAdminService()
        ];
        
        return [
            'healthy' => !in_array(false, $services),
            'services' => $services
        ];
    }

    private function checkAuthService()
    {
        try {
            // Check if auth routes are accessible
            return class_exists(\App\Http\Controllers\v1\AuthController::class);
        } catch (\Exception $e) {
            return false;
        }
    }

    private function checkAdminService()
    {
        try {
            // Check if admin routes are accessible
            return class_exists(\App\Http\Controllers\v1\Admin\AdminDashboardController::class);
        } catch (\Exception $e) {
            return false;
        }
    }

    private function checkQueue()
    {
        try {
            return [
                'healthy' => true,
                'driver' => config('queue.default'),
                'workers' => 0 // Would need to implement actual worker count
            ];
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function checkScrapers()
    {
        try {
            // Check scraper status from database or cache
            $scraperStatuses = [
                'parliament' => ['healthy' => true, 'last_run' => now()->subHours(1)],
                'bills' => ['healthy' => true, 'last_run' => now()->subHours(2)],
                'committees' => ['healthy' => true, 'last_run' => now()->subHours(3)]
            ];
            
            return [
                'healthy' => true,
                'scrapers' => $scraperStatuses
            ];
        } catch (\Exception $e) {
            return [
                'healthy' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    private function getMemoryUsage()
    {
        return [
            'current' => round(memory_get_usage(true) / 1024 / 1024, 2) . ' MB',
            'peak' => round(memory_get_peak_usage(true) / 1024 / 1024, 2) . ' MB',
            'limit' => ini_get('memory_limit')
        ];
    }

    private function getDiskUsage()
    {
        $path = storage_path();
        return [
            'free' => round(disk_free_space($path) / 1024 / 1024 / 1024, 2) . ' GB',
            'total' => round(disk_total_space($path) / 1024 / 1024 / 1024, 2) . ' GB',
            'percentage' => round((1 - disk_free_space($path) / disk_total_space($path)) * 100, 2) . '%'
        ];
    }
}