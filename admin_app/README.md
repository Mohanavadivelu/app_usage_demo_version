# App Usage Admin Dashboard

A modern Bootstrap 5+ admin dashboard for managing applications with full CRUD operations.

## Features

- 📊 **Dashboard Overview**: Statistics cards, charts, and recent applications
- 🔧 **App Manager**: Full CRUD operations with pagination (10 items per page)
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🎨 **Modern UI**: Bootstrap 5.3+ with custom styling
- 🔔 **Toast Notifications**: User feedback for all operations
- 🔍 **Real-time Data**: Direct integration with REST API

## Quick Start

### 1. Start the REST API Backend
```bash
cd rest
python main.py
```
The API will run on `http://localhost:8000`

### 2. Start the Frontend Server
```bash
cd admin_app
python server.py
```
The dashboard will run on `http://localhost:3000` and automatically open in your browser.

## File Structure

```
admin_app/
├── index.html          # Main dashboard HTML
├── server.py           # Python HTTP server
├── README.md           # This file
└── assets/
    ├── css/
    │   └── styles.css  # Custom styles
    └── js/
        └── scripts.js  # Dashboard functionality
```

## Usage

1. **Dashboard**: View application statistics, charts, and recent apps
2. **App Manager**: 
   - View all applications with pagination
   - Add new applications using the modal form
   - Edit existing applications
   - Delete applications with confirmation
3. **Navigation**: Use the sidebar to switch between Dashboard and App Manager

## API Configuration

The frontend is configured to connect to:
- **API Base URL**: `http://localhost:8000/api/v1`
- **API Key**: Pre-configured (update in `assets/js/scripts.js` if needed)

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

To modify the dashboard:
1. Edit HTML in `index.html`
2. Update styles in `assets/css/styles.css`
3. Modify functionality in `assets/js/scripts.js`
4. Restart the server to see changes

## Troubleshooting

**Port 3000 already in use?**
- Stop other services using port 3000
- Or modify the `PORT` variable in `server.py`

**API connection issues?**
- Ensure the REST API is running on `http://localhost:8000`
- Check the API key in `assets/js/scripts.js`
- Verify CORS settings in the server

**Browser not opening automatically?**
- Manually navigate to `http://localhost:3000`
- Check your default browser settings
