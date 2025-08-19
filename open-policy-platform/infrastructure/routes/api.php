<?php

use App\Http\Controllers\DeveloperController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

//route for auth
require __DIR__.'/v1/auth.php';
// route for app version 
require __DIR__.'/v1/app.php';
// route for admin version 
require __DIR__.'/v1/admin.php';
// route for web info
require __DIR__.'/v1/web.php';
// route for unified API v1
require __DIR__.'/v1/api.php';

// Route::post('/upload-db', [DeveloperController::class, 'uploadDb']);


