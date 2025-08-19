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

// Health check routes (no auth required)
Route::get('/v1/health', [App\Http\Controllers\HealthController::class, 'health']);
Route::get('/v1/health/detailed', [App\Http\Controllers\HealthController::class, 'detailedHealth']);

// Public data routes (no auth required for reading)
Route::prefix('v1')->group(function () {
    Route::get('/bills', [App\Http\Controllers\v1\PublicDataController::class, 'getBills']);
    Route::get('/bills/{id}', [App\Http\Controllers\v1\PublicDataController::class, 'getBill']);
    Route::get('/representatives', [App\Http\Controllers\v1\PublicDataController::class, 'getRepresentatives']);
    Route::get('/representatives/{id}', [App\Http\Controllers\v1\PublicDataController::class, 'getRepresentative']);
    Route::get('/votes', [App\Http\Controllers\v1\PublicDataController::class, 'getVotes']);
    Route::get('/committees', [App\Http\Controllers\v1\PublicDataController::class, 'getCommittees']);
    Route::get('/debates', [App\Http\Controllers\v1\PublicDataController::class, 'getDebates']);
    Route::get('/search', [App\Http\Controllers\v1\PublicDataController::class, 'search']);
});