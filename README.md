# ZTNAS - Zero Trust Network Access System

A comprehensive full-stack implementation of a Zero Trust Network Access System with advanced authentication, multi-factor authentication (including innovative picture password), role-based access control, device trust scoring, behavioral analytics, and audit logging.

## Project Structure

```
ztnas/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── routes/            # API endpoints
│   │   ├── schemas/           # Pydantic schemas for request/response validation
│   │   └── services/          # Business logic
│   ├── utils/                 # Helper utilities
│   ├── config/                # Configuration and database setup
│   ├── migrations/            # Alembic database migrations
│   ├── main.py                # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── .env                   # Environment variables
├── frontend/                  # HTML/CSS/JS frontend
│   ├── static/
│   │   ├── html/              # HTML templates
│   │   ├── css/               # Stylesheets
│   │   └── js/                # JavaScript files
│   ├── assets/                # Images, icons, etc.
│   └── templates/             # Template files
├── database/                  # Database schema files
└── logs/                      # Application logs
```

## Features

### Authentication & MFA
- ✅ User registration and login
- ✅ Password hashing with bcrypt
- ✅ **6+ Multi-Factor Authentication methods:**
  - TOTP (Time-based One-Time Password)
  - SMS OTP
  - Email OTP
  - FIDO2 Hardware tokens
  - Biometric authentication
  - **Picture Password (innovative gesture-based)**
  - Push notifications
  - Backup codes

### Zero Trust Architecture
- ✅ Continuous authentication and verification
- ✅ Device trust scoring
- ✅ Device registry and fingerprinting
- ✅ Risk-based access control
- ✅ Behavioral analytics
- ✅ Anomaly detection (8 types)
- ✅ Adaptive authentication

### Admin Dashboard (Phase 5)
- ✅ Real-time risk metrics
- ✅ Device management interface
- ✅ Behavioral analytics visualization
- ✅ Anomaly investigation panel
- ✅ Comprehensive audit logging
- ✅ User management
- ✅ Risk trend analysis
- ✅ Responsive design (mobile-friendly)
- ✅ Device compliance verification
- ✅ Behavioral analytics and anomaly detection
- ✅ Network and device context verification
- ✅ Micro-segmentation with zone-based access

### Authorization & Access Control
- ✅ Role-Based Access Control (RBAC)
- ✅ Permission management
- ✅ Attribute-Based Access Control (ABAC)
- ✅ Dynamic permission assignment

### Security & Monitoring
- ✅ Comprehensive audit logging
- ✅ Real-time threat detection
- ✅ Anomaly detection with risk scoring
- ✅ Session management
- ✅ Account lockout protection
- ✅ Login attempt tracking

## Technology Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL 18
- **ORM:** SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens)
- **Password Hashing:** bcrypt
- **MFA:** pyotp, webauthn

### Frontend
- **HTML5, CSS3, JavaScript (Vanilla)**
- **No frameworks** (as per requirements)

## Prerequisites

- Python 3.10+
- PostgreSQL 18
- pip (Python package manager)

## Installation & Setup

### Step 1: Install PostgreSQL
1. Download and install PostgreSQL 18 from https://www.postgresql.org/
2. Remember the password for the `postgres` superuser
3. Verify installation: `psql --version`

### Step 2: Clone/Navigate to Project
```bash
cd d:\projects\ztnas
```

### Step 3: Create Python Virtual Environment
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
1. Edit `backend/.env` file
2. Update DATABASE_URL with your PostgreSQL credentials:
   ```
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ztnas_db
   ```
3. Generate a secure SECRET_KEY (min 32 characters)

### Step 6: Create Database
```bash
python config/create_db.py
```

### Step 7: Initialize Database Schema
```bash
python main.py
```

The application will automatically create all tables on startup.

### Step 8: Start the Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Step 9: Serve Frontend
Option A: Use Python's simple HTTP server
```bash
cd ../frontend
python -m http.server 5500
```

Access frontend at: http://localhost:5500/static/html/index.html

Option B: Use VS Code Live Server extension

## API Endpoints (To Be Implemented)

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh-token` - Refresh JWT token
- `POST /api/auth/password-reset` - Password reset request

### MFA Management
- `POST /api/mfa/enroll` - Enroll in MFA method
- `POST /api/mfa/verify` - Verify MFA code
- `GET /api/mfa/methods` - Get user's MFA methods
- `DELETE /api/mfa/methods/{id}` - Remove MFA method

### User Management
- `GET /api/users` - List users (admin)
- `GET /api/users/{id}` - Get user details
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Role & Permission Management
- `GET /api/roles` - List roles
- `POST /api/roles` - Create role
- `PUT /api/roles/{id}` - Update role
- `DELETE /api/roles/{id}` - Delete role
- `GET /api/permissions` - List permissions
- `POST /api/roles/{id}/permissions` - Assign permissions to role

### Device Management
- `GET /api/devices` - List user's devices
- `POST /api/devices` - Register device
- `PUT /api/devices/{id}` - Update device trust
- `DELETE /api/devices/{id}` - Remove device

### Audit & Security
- `GET /api/audit-logs` - Get audit logs (paginated)
- `GET /api/anomalies` - Get detected anomalies
- `GET /api/sessions` - Get active sessions
- `DELETE /api/sessions/{id}` - Revoke session

## Database Schema

### Core Tables
- **users** - User accounts
- **roles** - User roles
- **permissions** - System permissions
- **user_roles** - User-to-role mapping
- **role_permissions** - Role-to-permission mapping

### MFA & Security
- **mfa_methods** - Enrolled MFA methods
- **sessions** - Active sessions
- **device_registries** - Trusted devices
- **audit_logs** - Action audit trail
- **behavior_profiles** - User behavior patterns
- **anomalies** - Detected anomalies

## Security Best Practices

1. ✅ **Passwords:** Hashed with bcrypt (cost factor 12)
2. ✅ **Tokens:** JWTs with expiration
3. ✅ **Database:** No plaintext secrets stored
4. ✅ **CORS:** Configured for specific origins
5. ✅ **Anomaly Detection:** Risk-based authentication
6. ✅ **Audit Trail:** Comprehensive logging
7. ✅ **Session Management:** Token-based with refresh
8. ✅ **Rate Limiting:** To be implemented

## Development Roadmap

### Phase 1: ✅ Project Initialization
- [x] Project structure setup
- [x] Database models
- [x] Environment configuration

### Phase 2: ✅ Authentication & RBAC
- [x] User registration & login endpoints
- [x] JWT token generation & validation
- [x] Role and permission endpoints (4 roles, 16 permissions)
- [x] RBAC middleware

### Phase 3: ✅ MFA Implementation (All 6+ types)
- [x] TOTP setup & verification
- [x] SMS/Email OTP
- [x] FIDO2/Hardware tokens
- [x] **Picture Password MFA** (Custom gesture recognition with canvas)
- [x] Backup codes
- [x] Unified MFA endpoint
- [x] MFA enrollment UI

### Phase 4: ✅ Zero Trust Features
- [x] Device registration & trust scoring (0-1 scale)
- [x] Behavioral analytics & pattern learning
- [x] Anomaly detection (8 types)
- [x] Risk scoring (6-factor weighted model)
- [x] Adaptive access control
- [x] 18+ Zero Trust endpoints

### Phase 5: ✅ Frontend Dashboard
- [x] Admin dashboard with 8 sections
- [x] Real-time metrics & KPIs
- [x] Risk visualization with charts (Chart.js)
- [x] Device management interface
- [x] Behavioral analytics dashboard
- [x] Anomaly investigation panel
- [x] Audit logging viewer with export
- [x] User management interface
- [x] Responsive design (mobile-friendly)

### Phase 6: Testing & Deployment
- [ ] Unit tests
- [ ] Integration tests
- [ ] Load/stress testing
- [ ] Security testing (penetration testing)
- [ ] Documentation & deployment guide
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Production deployment

## Configuration

### .env File Variables

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ztnas_db

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Security
PASSWORD_MIN_LENGTH=8
SESSION_TIMEOUT_MINUTES=60
MAX_LOGIN_ATTEMPTS=5

# Features
MFA_REQUIRED=False
ANOMALY_DETECTION_ENABLED=True
```

## Testing

### Test Database Connection
```bash
python -c "from config.database import engine; print('Connected!' if engine.connect() else 'Failed')"
```

### Check Health Endpoint
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### PostgreSQL Connection Error
```
Error: could not translate host name "localhost" to address
```
**Solution:** Ensure PostgreSQL is running and credentials in .env are correct

### Port Already in Use
```
Address already in use ('::', 8000)
```
**Solution:** Change port in startup command
```bash
uvicorn main:app --reload --port 8001
```

### Database Migration Issues
Drop and recreate the database:
```bash
python config/create_db.py
```

## Contributing

This is a final year B.Tech project. All features must follow the Zero Trust architecture principles.

## License

This project is for educational purposes.

## Support

For issues or questions, refer to the troubleshooting section or consult the project documentation.
