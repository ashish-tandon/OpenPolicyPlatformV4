# Authentication

## Flow
1. Obtain tokens via `POST /api/v1/auth/login` (OAuth2 password form fields `username`, `password`)
2. Use access token in requests: `Authorization: Bearer <access_token>`
3. Refresh access token via `POST /api/v1/auth/refresh` with `refresh_token`

## Endpoints
- `POST /api/v1/auth/login`
  - Request (form): `username`, `password`
  - Response: `{ access_token, refresh_token, token_type, expires_in, user }`
- `POST /api/v1/auth/register`
  - Body: `{ username, email, password, full_name?, role? }`
  - Response: confirmation + user summary
- `POST /api/v1/auth/refresh`
  - Body: `refresh_token: string`
  - Response: `{ access_token, token_type, expires_in }`
- `GET /api/v1/auth/me`
  - Requires `Authorization: Bearer ...`
  - Response: current user profile
- `PUT /api/v1/auth/me`
  - Body: partial fields `{ email?, full_name?, password?, is_active? }`
- `POST /api/v1/auth/change-password`
  - Body: `{ current_password, new_password }`
- `POST /api/v1/auth/logout`
  - Response: confirmation
- `POST /api/v1/auth/forgot-password`
  - Body: `{ email }`
  - Response: confirmation (email with reset link in background)
- `GET /api/v1/auth/users` (admin)
  - Requires admin role
  - Response: user list
- `GET /api/v1/auth/permissions`
  - Requires auth
  - Response: `{ permissions, role }`

## Notes
- Tokens are JWT (HS256) with default lifetimes in code; replace secrets in production via environment.
- Admin-only routes also exist in `/api/v1/admin` with separate capabilities.