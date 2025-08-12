# Flask RFID System

A comprehensive Flask-based RFID system for school cafeteria operations, converted from Node.js to Python with best practices.

## Features

- **RFID Card Scanning**: Support for ACR1252 USB NFC readers
- **User Management**: Student and staff user lookup and management
- **Purchase Processing**: Complete purchase flow with cash and monthly billing
- **Meal Reservations**: Handle pre-ordered meals and mark as served
- **Real-time Updates**: WebSocket support for live updates
- **Multi-language Support**: English and German translations
- **Admin Authentication**: JWT-based authentication for RFID operators
- **Database Integration**: MongoDB with MongoEngine ODM
- **Mock Mode**: Development mode without physical RFID hardware

## Technology Stack

- **Backend**: Flask 3.0 with Flask-SocketIO
- **Database**: MongoDB with MongoEngine ODM
- **RFID**: pyscard library for NFC/RFID communication
- **Authentication**: Flask-JWT-Extended
- **Logging**: structlog for structured logging
- **Internationalization**: Flask-Babel
- **Security**: Flask-CORS, rate limiting, input validation

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- ACR1252 USB NFC Reader (optional, can run in mock mode)

### Step 1: Clone and Setup

```bash
# Navigate to the flaskrfid directory
cd flaskrfid

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### Step 3: Install RFID Dependencies (Optional)

For physical RFID reader support:

**Windows:**
```bash
# Install PC/SC service (usually pre-installed)
# Download and install PC/SC drivers for ACR1252
pip install pyscard
```

**macOS:**
```bash
# Install PC/SC Lite
brew install pcsc-lite
pip install pyscard
```

**Linux (Ubuntu/Debian):**
```bash
# Install PC/SC daemon and development files
sudo apt-get update
sudo apt-get install pcscd pcsc-tools libpcsclite-dev

# Install Python RFID libraries
pip install pyscard
```

### Step 4: Setup MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB Community Edition
# Follow official MongoDB installation guide for your OS

# Start MongoDB service
# Windows: Start MongoDB service from Services
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

**Option B: MongoDB Atlas (Cloud)**
```bash
# Create account at https://www.mongodb.com/atlas
# Create cluster and get connection string
# Use connection string in .env file
```

### Step 5: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

Key environment variables:
```env
FLASK_ENV=development
MONGODB_URI=mongodb://localhost:27017/rfid_system
MOCK_RFID_READER=true  # Set to false for real hardware
CAFETERIA_NAME=School Cafeteria
STATION_ID=STATION_001
```

### Step 6: Initialize Database

```bash
# Run the application once to create database collections
python run.py
```

### Step 7: Run the Application

```bash
# Development mode
python run.py

# Or using Flask command
flask run --host=0.0.0.0 --port=3003
```

## Development Setup

### Code Formatting and Linting

```bash
# Install development tools
pip install black flake8 pytest

# Format code
black .

# Lint code
flake8 .

# Run tests
pytest
```

### Mock Mode Development

For development without physical RFID hardware:

```bash
# Set in .env file
MOCK_RFID_READER=true

# Use manual scan endpoint for testing
curl -X POST http://localhost:3003/api/rfid/manual-scan \
  -H "Content-Type: application/json" \
  -d '{"uid": "1234567890"}'
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login
- `GET /api/auth/profile` - Get admin profile
- `POST /api/auth/logout` - Admin logout

### RFID Operations
- `GET /api/rfid/status` - Get reader status
- `GET /api/rfid/history` - Get scan history
- `POST /api/rfid/manual-scan` - Manual scan (mock mode)
- `POST /api/rfid/reconnect` - Reconnect reader

### User Management
- `GET /api/users/uid/<uid>` - Get user by UID
- `GET /api/users/<user_id>` - Get user by ID
- `GET /api/users/search?q=<query>` - Search users
- `POST /api/users/register` - Register new user

### Purchase Processing
- `GET /api/purchases/foods` - Get available foods
- `POST /api/purchases/complete` - Complete purchase
- `GET /api/purchases/user/<user_id>` - Get user purchases

### Reservations
- `GET /api/reservations/user/<user_id>/today` - Get today's reservations
- `POST /api/reservations/<id>/confirm` - Confirm reservation
- `GET /api/reservations/<id>` - Get reservation details

### Health Check
- `GET /api/health` - System health status

## WebSocket Events

### Client to Server
- `connect` - Client connection
- `requestRfidStatus` - Request RFID status
- `manualScan` - Trigger manual scan
- `completePurchase` - Complete purchase
- `confirmReservation` - Confirm reservation

### Server to Client
- `connected` - Connection established
- `rfidConnected` - RFID reader connected
- `rfidDisconnected` - RFID reader disconnected
- `cardScanned` - Card detected
- `scanResult` - Scan processing result
- `purchaseCompleted` - Purchase completed
- `reservationConfirmed` - Reservation confirmed

## Configuration

### RFID Reader Settings

```env
RFID_READER_TYPE=ACR1252
RFID_READER_NAME=ACR1252
RFID_SCAN_TIMEOUT=5000
RFID_AUTO_RECONNECT=true
RFID_BEEP_ON_SCAN=true
```

### Cafeteria Settings

```env
CAFETERIA_NAME=School Cafeteria
CAFETERIA_LOCATION=Main Building
STATION_ID=STATION_001
OPERATING_START_TIME=07:00
OPERATING_END_TIME=15:00
```

### Security Settings

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
```

## Logging

Logs are stored in the `logs/` directory:
- `rfid-server.log` - General application logs
- `error.log` - Error logs only

Log levels can be controlled via environment:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Troubleshooting

### RFID Reader Issues

1. **Reader not detected:**
   ```bash
   # Check if reader is connected
   # Linux/macOS:
   pcsc_scan
   
   # Windows: Check Device Manager
   ```

2. **Permission issues (Linux):**
   ```bash
   # Add user to pcscd group
   sudo usermod -a -G pcscd $USER
   # Restart session
   ```

3. **Driver issues:**
   - Download latest drivers from ACS website
   - Ensure PC/SC service is running

### Database Issues

1. **Connection failed:**
   ```bash
   # Check MongoDB status
   # Linux: sudo systemctl status mongod
   # macOS: brew services list | grep mongodb
   # Windows: Check Services for MongoDB
   ```

2. **Authentication errors:**
   - Check MongoDB URI format
   - Verify credentials if using authentication

### Application Issues

1. **Import errors:**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

2. **Port conflicts:**
   ```bash
   # Change port in .env
   PORT=3004
   ```

## Production Deployment

### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn eventlet

# Run with Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:3003 run:app
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3003

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:3003", "run:app"]
```

### Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
JWT_SECRET=your-production-jwt-secret
MONGODB_URI=mongodb://your-production-db/rfid_system
MOCK_RFID_READER=false
LOG_LEVEL=WARNING
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs in `logs/` directory