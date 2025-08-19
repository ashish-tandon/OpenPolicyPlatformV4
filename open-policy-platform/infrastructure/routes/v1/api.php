<?php

use App\Http\Controllers\v1\AuthController;
use App\Http\Controllers\v1\Admin\AdminDashboardController;
use App\Http\Middleware\AdminMiddleware;
use Illuminate\Support\Facades\Route;

/**
 * API V1 Routes that match frontend expectations
 */

// Authentication routes
Route::prefix('v1/auth')->group(function () {
    Route::post('/login', [AuthController::class, 'login']);
    Route::post('/register', [AuthController::class, 'register']);
    
    // Protected auth routes
    Route::middleware('auth:sanctum')->group(function () {
        Route::get('/me', [AuthController::class, 'me']);
        Route::post('/logout', [AuthController::class, 'logout']);
    });
});

// Admin routes
Route::prefix('v1/admin')->middleware(['auth:sanctum', AdminMiddleware::class])->group(function () {
    // Dashboard
    Route::get('/dashboard', [AdminDashboardController::class, 'getDashboardStats']);
    Route::get('/health', [AdminDashboardController::class, 'getSystemHealth']);
});

// Health check route (no auth required)
Route::get('/v1/health', function () {
    return response()->json([
        'status' => 'ok',
        'service' => 'api',
        'timestamp' => now()->toIso8601String()
    ]);
});