# PropertyYards Frontend

React frontend for the PropertyYards real estate platform.

## Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000/api
```

For production, update the API URL in `src/config/api.js`:

```javascript
production: {
  baseURL: 'https://your-production-api.com/api',
}
```

## Features

- 🏠 Property listings and search
- 🎨 Interactive whiteboard for floor plans
- 📊 3D property visualization
- 👥 User authentication and profiles
- 💰 Referral program with commission tracking
- 📈 Analytics dashboard
- 🤖 AI-powered features

## Deployment

### Vercel

1. Push to GitHub
2. Connect repository to Vercel
3. Set environment variables
4. Deploy automatically

The configuration is already set up in `vercel.json`.

### Manual Deployment

```bash
# Build
npm run build

# Deploy dist folder to your hosting provider
```

## Troubleshooting

### Common Issues

1. **Build fails**: Check if all dependencies are installed
2. **API calls fail**: Verify API URL configuration
3. **Routing issues**: Ensure Vercel configuration is correct

### Development Tips

- Use `npm run dev` for local development
- Check browser console for errors
- Verify API endpoints are accessible
- Test both authenticated and unauthenticated flows

## Project Structure

```
src/
├── components/          # React components
│   ├── Auth/           # Authentication components
│   ├── Home/           # Landing page
│   ├── Properties/     # Property listings
│   └── ...
├── config/             # Configuration files
├── services/           # API services
├── stores/             # State management (Zustand)
├── utils/              # Utility functions
├── App.jsx             # Main app component
├── main.jsx            # App entry point
└── index.css           # Global styles
```

## Technologies Used

- React 18
- React Router 6
- Zustand (state management)
- Axios (HTTP client)
- Vite (build tool)
- Tailwind CSS (styling)
- React Icons (icons)
