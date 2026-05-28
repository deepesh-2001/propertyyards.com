// Test Data Utilities for Housing Platform
// These provide sample data for testing components

// Property Test Data
export const testProperties = [
  {
    id: 1,
    title: 'Modern 3BHK Apartment',
    description: 'Spacious apartment with great amenities',
    price: 750000,
    city: 'Mumbai',
    state: 'Maharashtra',
    location: 'Andheri West',
    bedrooms: 3,
    bathrooms: 2,
    area: 1200,
    property_type: 'apartment',
    images: ['https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=400'],
    amenities: ['Swimming Pool', 'Gym', 'Parking', 'Security'],
    status: 'available'
  },
  {
    id: 2,
    title: 'Luxury Villa with Garden',
    description: 'Beautiful villa in a prime location',
    price: 2500000,
    city: 'Bangalore',
    state: 'Karnataka',
    location: 'Whitefield',
    bedrooms: 4,
    bathrooms: 3,
    area: 3500,
    property_type: 'house',
    images: ['https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400'],
    amenities: ['Garden', 'Swimming Pool', 'Gym', 'Clubhouse'],
    status: 'available'
  },
  {
    id: 3,
    title: 'Cozy Studio Apartment',
    description: 'Perfect for young professionals',
    price: 350000,
    city: 'Pune',
    state: 'Maharashtra',
    location: 'Koregaon Park',
    bedrooms: 1,
    bathrooms: 1,
    area: 450,
    property_type: 'apartment',
    images: ['https://images.unsplash.com/photo-1502672260266-12c4d4867efb?w=400'],
    amenities: ['Parking', 'Security'],
    status: 'available'
  }
]

// Whiteboard Test Data
export const testWhiteboards = [
  {
    id: 'floor-plan-1',
    name: '2BHK Floor Plan',
    data: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2Y5ZmFmYiIgc3Ryb2tlPSIjZTJhODdmIiBzdHJva2Utd2lkdGg9IjIiLz48cmVjdCB4PSI1MCIgeT0iNTAiIHdpZHRoPSIzMDAiIGhlaWdodD0iMjUwIiBmaWxsPSIjZGZlNmViIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjIwMCIgeT0iMTgwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjMzc0MTUxIj5MaXZpbmcgUm9vbTwvdGV4dD48cmVjdCB4PSIzNzAiIHk9IjUwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2RiZTJmNyIgc3Ryb2tlPSIjNmI3MjgwIiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI0NzAiIHk9IjEzMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzM3NDE1MSI+S2l0Y2hlbjwvdGV4dD48cmVjdCB4PSIzNzAiIHk9IjIyMCIgd2lkdGg9IjE4MCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNkZmU2ZWIiIHN0cm9rZT0iIzZiNzI4MCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDYwIiB5PSIzMzAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiMzNzQxNTEiPk1hc3RlciBCZWQ8L3RleHQ+PHJlY3QgeD0iNTgwIiB5PSIyMjAiIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZGZlNmViIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjY4MCIgeT0iMzMwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE2IiBmaWxsPSIjMzc0MTUxIj5CZWQgUm9vbSAyPC90ZXh0Pjwvc3ZnPg=='
  },
  {
    id: 'garden-layout-1',
    name: 'Garden Layout',
    data: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2YwZmRmNCIgc3Ryb2tlPSIjODRjYzE2IiBzdHJva2Utd2lkdGg9IjMiLz48Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjgwIiBmaWxsPSIjYmJmN2QwIiBzdHJva2U9IiM0NDhkMTgiIHN0cm9rZS13aWR0aD0iMiIvPjx0ZXh0IHg9IjIwMCIgeT0iMjA1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjMjJiYzMzIj5UcmVlPC90ZXh0PjxjaXJjbGUgY3g9IjQwMCIgY3k9IjMwMCIgcj0iNjAiIGZpbGw9IiNiYmY3ZDAiIHN0cm9rZT0iIzQ0OGQxOCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDAwIiB5PSIzMDUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiMyMmJjMzMiPlRyZWU8L3RleHQ+PGNpcmNsZSBjeD0iNjAwIiBjeT0iMjAwIiByPSI3MCIgZmlsbD0iI2JiZjdkMCIgc3Ryb2tlPSIjNDQ4ZDE4IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSI2MDAiIHk9IjIwNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzIyYmMzMyI+VHJlZTwvdGV4dD48cmVjdCB4PSIzMDAiIHk9IjQwMCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmZWUwYTAiIHN0cm9rZT0iI2Q5N2EwMCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHRleHQgeD0iNDAwIiB5PSI0NTUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5MjQwMDAiPlBhdGlvPC90ZXh0Pjwvc3ZnPg=='
  }
]

// 3D Structure Test Images
export const test3DImages = [
  {
    id: 'house-elevation',
    name: 'House Elevation',
    type: 'house',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzg3Y2VlYiIvPjxwb2x5Z29uIHBvaW50cz0iMjAwLDUwIDgwLDE4MCAzMjAsMTgwIiBmaWxsPSIjOGI0NTEzIi8+PHJlY3QgeD0iODAiIHk9IjE4MCIgd2lkdGg9IjI0MCIgaGVpZ2h0PSIxODAiIGZpbGw9IiNmZmYiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTIwIiB5PSIyMjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY2YjJmZiIgc3Ryb2tlPSIjMzMzIi8+PHJlY3QgeD0iMjIwIiB5PSIyMjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY2YjJmZiIgc3Ryb2tlPSIjMzMzIi8+PHJlY3QgeD0iMTgwIiB5PSIzMDAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzhiNDUxMyIgc3Ryb2tlPSIjMzMzIi8+PC9zdmc+'
  },
  {
    id: 'apartment-building',
    name: 'Apartment Building',
    type: 'apartment',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjUwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjUwMCIgZmlsbD0iI2Y1ZjVmNSIvPjxyZWN0IHg9IjgwIiB5PSI1MCIgd2lkdGg9IjI0MCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNkZGRkZGQiIHN0cm9rZT0iIzk5OSIgc3Ryb2tlLXdpZHRoPSIzIi8+PHJlY3QgeD0iMTAwIiB5PSI4MCIgd2lkdGg9IjYwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjYmFkZmZmIiBzdHJva2U9IiM2NjYiLz48cmVjdCB4PSIxODAiIHk9IjgwIiB3aWR0aD0iNjAiIGhlaWdodD0iNTAiIGZpbGw9IiNiYWRmZmYiIHN0cm9rZT0iIzY2NiIvPjxyZWN0IHg9IjI2MCIgeT0iODAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTAwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMjYwIiB5PSIxNjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTAwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMjYwIiB5PSIyNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI1MCIgZmlsbD0iI2JhZGZmZiIgc3Ryb2tlPSIjNjY2Ii8+PHJlY3QgeD0iMTgwIiB5PSIzNDAiIHdpZHRoPSI0MCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzhhNTQyMyIgc3Ryb2tlPSIjMzMzIi8+PC9zdmc+'
  },
  {
    id: 'modern-villa',
    name: 'Modern Villa',
    type: 'villa',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2YwZjBmMCIvPjxyZWN0IHg9IjUwIiB5PSIxMDAiIHdpZHRoPSIzMDAiIGhlaWdodD0iMTgwIiBmaWxsPSIjZmZmIiBzdHJva2U9IiMzMzMiIHN0cm9rZS13aWR0aD0iNCIvPjxyZWN0IHg9IjgwIiB5PSIxMzAiIHdpZHRoPSIxMDAiIGhlaWdodD0iODAiIGZpbGw9IiMwMDYzMzMiIHN0cm9rZT0iIzMzMyIvPjxyZWN0IHg9IjIyMCIgeT0iMTMwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjMDA2MzMzIiBzdHJva2U9IiMzMzMiLz48bGluZSB4MT0iNTAiIHkxPSIxMDAiIHgyPSIyMDAiIHkyPSI1MCIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjMiLz48bGluZSB4MT0iMzUwIiB5MT0iMTAwIiB4Mj0iMjAwIiB5Mj0iNTAiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PC9zdmc+'
  },
  {
    id: 'simple-cube',
    name: 'Cube Test',
    type: 'cube',
    src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y1ZjVmNSIvPjxyZWN0IHg9IjUwIiB5PSI1MCIgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiM2MzY2ZjEiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PHRleHQgeD0iMTAwIiB5PSIxMTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IndoaXRlIiBmb250LXNpemU9IjE0IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiI+Q1VCRTwvdGV4dD48L3N2Zz4='
  }
]

// Test Users
export const testUsers = [
  {
    id: 1,
    email: 'buyer@housing.com',
    first_name: 'John',
    last_name: 'Buyer',
    role: 'buyer',
    phone_number: '+91-9876543210'
  },
  {
    id: 2,
    email: 'seller@housing.com',
    first_name: 'Jane',
    last_name: 'Seller',
    role: 'seller',
    phone_number: '+91-9876543211'
  },
  {
    id: 3,
    email: 'agent@housing.com',
    first_name: 'Mike',
    last_name: 'Agent',
    role: 'agent',
    phone_number: '+91-9876543212'
  }
]

// Cache Test Helpers
export const testCacheHelpers = {
  // Generate a test whiteboard drawing
  generateTestDrawing: (name = 'Test Drawing') => ({
    name,
    data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
    timestamp: Date.now()
  }),

  // Generate a test 3D model
  generateTest3DModel: (type = 'house', name = 'Test Model') => ({
    type,
    name,
    imageId: `test-${Date.now()}`,
    imageName: 'test-image.jpg',
    generatedAt: new Date().toISOString(),
    parameters: {
      width: 10,
      height: type === 'apartment' ? 16 : 8,
      depth: 10,
      rooms: type === 'apartment' ? 12 : 5,
      floors: type === 'apartment' ? 4 : 1
    }
  })
}

// Mock API Responses
export const mockAPIResponses = {
  login: {
    access_token: 'mock-access-token-' + Date.now(),
    refresh_token: 'mock-refresh-token-' + Date.now(),
    user: testUsers[0]
  },

  properties: {
    items: testProperties,
    total: testProperties.length,
    page: 1,
    pages: 1
  },

  propertySearch: {
    items: [testProperties[0]],
    total: 1,
    page: 1,
    pages: 1
  }
}

// Export all test data
export default {
  testProperties,
  testWhiteboards,
  test3DImages,
  testUsers,
  testCacheHelpers,
  mockAPIResponses
}
