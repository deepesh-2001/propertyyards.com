# Housing Platform API Specification

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints except `/api/auth/register`, `/api/auth/login`, and public endpoints require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Authentication

#### Register User
- **Endpoint**: `POST /api/auth/register`
- **Description**: Register a new user account
- **Request Body**:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1-555-0100",
  "password": "securepassword123",
  "role": "buyer"
}
```
- **Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1-555-0100",
  "role": "buyer",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### Login
- **Endpoint**: `POST /api/auth/login`
- **Description**: Login user and get tokens
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```
- **Response**: `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Refresh Token
- **Endpoint**: `POST /api/auth/refresh`
- **Description**: Refresh access token
- **Request Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```
- **Response**: `200 OK` (same as login response)

---

### Users

#### Get Current User Profile
- **Endpoint**: `GET /api/users/me`
- **Description**: Get authenticated user's profile
- **Auth Required**: Yes
- **Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1-555-0100",
  "role": "buyer",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "properties_count": 5,
  "inquiries_count": 3
}
```

#### Update User Profile
- **Endpoint**: `PUT /api/users/me`
- **Description**: Update current user's profile
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone_number": "+1-555-0101"
}
```
- **Response**: `200 OK`

#### Get User By ID
- **Endpoint**: `GET /api/users/{user_id}`
- **Description**: Get user profile by ID (public)
- **Auth Required**: No
- **Response**: `200 OK`

#### Get User Properties
- **Endpoint**: `GET /api/users/{user_id}/properties?page=1&limit=20`
- **Description**: Get all properties by a user
- **Auth Required**: No
- **Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Luxury Apartment",
      "location": "123 Main St",
      "city": "New York",
      "price": 500000,
      "property_type": "apartment",
      "bedrooms": 3,
      "bathrooms": 2,
      "area": 1500,
      "status": "listed",
      "images": [],
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

---

### Properties

#### List Properties
- **Endpoint**: `GET /api/properties?page=1&limit=20&status=listed`
- **Description**: List all properties with pagination
- **Auth Required**: No
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20, max: 100)
  - `status`: Filter by status (listed, sold, rented, pending)
- **Response**: `200 OK`

#### Search Properties
- **Endpoint**: `GET /api/properties/search`
- **Description**: Advanced property search with filters
- **Auth Required**: No
- **Query Parameters**:
  - `query`: Search text
  - `city`: City name
  - `state`: State name
  - `min_price`: Minimum price
  - `max_price`: Maximum price
  - `property_type`: Type of property
  - `min_bedrooms`: Minimum bedrooms
  - `max_bedrooms`: Maximum bedrooms
  - `min_bathrooms`: Minimum bathrooms
  - `max_bathrooms`: Maximum bathrooms
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
- **Response**: `200 OK`

#### Get Property Details
- **Endpoint**: `GET /api/properties/{property_id}`
- **Description**: Get detailed information about a property
- **Auth Required**: No
- **Response**: `200 OK`

#### Create Property
- **Endpoint**: `POST /api/properties`
- **Description**: Create a new property listing
- **Auth Required**: Yes (seller or agent only)
- **Request Body**:
```json
{
  "title": "Luxury Apartment",
  "description": "Beautiful 3 bedroom apartment",
  "location": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "price": 500000,
  "property_type": "apartment",
  "bedrooms": 3,
  "bathrooms": 2,
  "area": 1500,
  "amenities": ["wifi", "parking", "pool"],
  "images": ["url1", "url2"]
}
```
- **Response**: `200 OK`

#### Update Property
- **Endpoint**: `PUT /api/properties/{property_id}`
- **Description**: Update property listing
- **Auth Required**: Yes (property owner or admin)
- **Request Body**: Same as create (all fields optional)
- **Response**: `200 OK`

#### Delete Property
- **Endpoint**: `DELETE /api/properties/{property_id}`
- **Description**: Delete property listing
- **Auth Required**: Yes (property owner or admin)
- **Response**: `200 OK`
```json
{
  "message": "Property deleted successfully"
}
```

#### Add Property to Wishlist
- **Endpoint**: `POST /api/properties/{property_id}/wishlist`
- **Description**: Add property to user's wishlist
- **Auth Required**: Yes
- **Response**: `200 OK`
```json
{
  "message": "Added to wishlist"
}
```

#### Remove Property from Wishlist
- **Endpoint**: `DELETE /api/properties/{property_id}/wishlist`
- **Description**: Remove property from wishlist
- **Auth Required**: Yes
- **Response**: `200 OK`
```json
{
  "message": "Removed from wishlist"
}
```

---

### Inquiries

#### Create Inquiry
- **Endpoint**: `POST /api/inquiries`
- **Description**: Create inquiry for a property
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "property_id": "property-uuid",
  "message": "I'm very interested in this property. Please contact me soon."
}
```
- **Response**: `200 OK`

#### Get User Inquiries
- **Endpoint**: `GET /api/inquiries?page=1&limit=20`
- **Description**: Get current user's inquiries
- **Auth Required**: Yes
- **Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "user-uuid",
      "property_id": "property-uuid",
      "message": "I'm interested in this property",
      "status": "pending",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

#### Get Inquiry By ID
- **Endpoint**: `GET /api/inquiries/{inquiry_id}`
- **Description**: Get specific inquiry details
- **Auth Required**: Yes (owner or property owner)
- **Response**: `200 OK`

#### Update Inquiry
- **Endpoint**: `PUT /api/inquiries/{inquiry_id}`
- **Description**: Update inquiry
- **Auth Required**: Yes
- **Request Body**:
```json
{
  "message": "Updated message",
  "status": "responded"
}
```
- **Response**: `200 OK`

#### Delete Inquiry
- **Endpoint**: `DELETE /api/inquiries/{inquiry_id}`
- **Description**: Delete inquiry
- **Auth Required**: Yes
- **Response**: `200 OK`

#### Get Property Inquiries
- **Endpoint**: `GET /api/inquiries/property/{property_id}/inquiries?page=1&limit=20`
- **Description**: Get all inquiries for a property
- **Auth Required**: Yes (property owner only)
- **Response**: `200 OK`

---

### Admin

#### Get Analytics
- **Endpoint**: `GET /api/admin/analytics`
- **Description**: Get platform analytics
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`
```json
{
  "users": {
    "total_users": 1000,
    "active_users": 950,
    "total_sellers": 250,
    "total_buyers": 700,
    "total_agents": 50
  },
  "properties": {
    "total_properties": 5000,
    "active_listings": 4500,
    "sold_properties": 400,
    "rented_properties": 100,
    "total_value": 2500000000
  },
  "total_inquiries": 15000,
  "total_wishlist_items": 8000
}
```

#### Get All Users
- **Endpoint**: `GET /api/admin/users?page=1&limit=50&role=buyer`
- **Description**: List all users (admin only)
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`

#### Get All Properties
- **Endpoint**: `GET /api/admin/properties?page=1&limit=50&status=pending`
- **Description**: List all properties (admin only)
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`

#### Approve Property
- **Endpoint**: `POST /api/admin/properties/{property_id}/approve`
- **Description**: Approve pending property listing
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`
```json
{
  "message": "Property approved"
}
```

#### Reject Property
- **Endpoint**: `POST /api/admin/properties/{property_id}/reject`
- **Description**: Reject property listing
- **Auth Required**: Yes (admin only)
- **Request Body**:
```json
{
  "reason": "Property images not clear"
}
```
- **Response**: `200 OK`
```json
{
  "message": "Property rejected"
}
```

#### Delete User
- **Endpoint**: `DELETE /api/admin/users/{user_id}`
- **Description**: Delete user account (admin only)
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`

#### Deactivate User
- **Endpoint**: `POST /api/admin/users/{user_id}/deactivate`
- **Description**: Deactivate user account
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`

#### Get Audit Logs
- **Endpoint**: `GET /api/admin/audit-logs?page=1&limit=50&action=approve_property`
- **Description**: Get admin audit logs
- **Auth Required**: Yes (admin only)
- **Response**: `200 OK`

---

### System

#### Health Check
- **Endpoint**: `GET /health`
- **Description**: Check API health status
- **Auth Required**: No
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "environment": "production"
}
```

#### API Info
- **Endpoint**: `GET /api/info`
- **Description**: Get API information
- **Auth Required**: No
- **Response**: `200 OK`
```json
{
  "title": "Housing Platform API",
  "version": "1.0.0",
  "description": "Real estate management system",
  "endpoints": {
    "auth": "/api/auth",
    "users": "/api/users",
    "properties": "/api/properties",
    "inquiries": "/api/inquiries",
    "admin": "/api/admin"
  },
  "documentation": {
    "swagger": "/docs",
    "redoc": "/redoc"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Permission denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting

- **General endpoints**: 10 requests/second
- **API endpoints**: 100 requests/second

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Total limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time

---

## Caching

The following endpoints support caching:
- `GET /api/properties` - 5 minutes
- `GET /api/properties/search` - 5 minutes
- `GET /api/properties/{id}` - 10 minutes
- `GET /api/users/{id}` - 30 minutes
- `GET /api/admin/analytics` - 15 minutes

---

## Pagination

Paginated endpoints use:
- `page`: 1-indexed page number
- `limit`: Items per page (1-100, default: 20)

Response includes:
- `items`: Array of results
- `total`: Total number of items
- `page`: Current page
- `limit`: Items per page
- `pages`: Total number of pages

---

## Sorting

Default sorting is by creation date in descending order (newest first).

---

## Examples

### Create Property and Get Details
```bash
# 1. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seller@housing.com","password":"seller@housing123"}'

# 2. Create property (use access_token from login)
curl -X POST http://localhost:8000/api/properties \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Beautiful 3-Bedroom House",
    "description": "Spacious house with garden",
    "location": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "price": 750000,
    "property_type": "house",
    "bedrooms": 3,
    "bathrooms": 2,
    "area": 2000,
    "amenities": ["garden", "parking", "modern kitchen"],
    "images": []
  }'

# 3. Get property details
curl -X GET http://localhost:8000/api/properties/{property_id}
```

### Search Properties
```bash
curl -X GET "http://localhost:8000/api/properties/search?city=New+York&min_price=500000&max_price=1000000&property_type=apartment&min_bedrooms=2"
```

---

## Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See interactive API documentation at these URLs once the server is running.

