<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Representative extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'email',
        'phone',
        'party',
        'constituency',
        'province',
        'photo_url',
        'bio',
        'active'
    ];

    public function issues()
    {
        return $this->hasMany(RepresentativeIssue::class);
    }

    public function activityLogs()
    {
        return $this->hasMany(PoliticianActivityLog::class, 'politician_id');
    }
}