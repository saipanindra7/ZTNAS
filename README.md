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
- ✅ **Implemented Multi-Factor Authentication methods:**
  - TOTP (Time-based One-Time Password)
  - SMS OTP
  - Email OTP
  - **Picture Password (innovative gesture-based)**
  - Backup codes
- ℹ️ FIDO2/Biometric/Push schemas exist as design scaffolding but are not fully implemented end-to-end in this build.

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

## API Endpoints (Implemented)

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/change-password` - Password change

### MFA Management
- `POST /api/v1/mfa/totp/setup` - Create TOTP secret + QR
- `POST /api/v1/mfa/totp/enroll` - Enroll/verify TOTP
- `POST /api/v1/mfa/sms/setup` - Send SMS OTP
- `POST /api/v1/mfa/email/setup` - Send Email OTP
- `POST /api/v1/mfa/otp/verify` - Verify SMS/Email OTP
- `POST /api/v1/mfa/picture/setup` - Upload picture password image
- `POST /api/v1/mfa/picture/define` - Save picture tap pattern
- `POST /api/v1/mfa/backup-codes/generate` - Generate backup codes
- `POST /api/v1/mfa/verify` - Verify MFA code during auth flow
- `GET /api/v1/mfa/status` - MFA readiness status
- `GET /api/v1/mfa/methods` - List user MFA methods
- `DELETE /api/v1/mfa/methods/{id}` - Remove MFA method

### User Management
- `GET /api/v1/admin/users` - List users (admin)
- `GET /api/v1/admin/users/{id}` - Get user details (admin)
- `POST /api/v1/admin/users` - Create user (admin)
- `PUT /api/v1/admin/users/{id}` - Update user (admin)
- `DELETE /api/v1/admin/users/{id}` - Delete user (admin)

### Role & Permission Management
- `GET /api/v1/admin/roles` - List roles (admin)
- `POST /api/v1/admin/roles` - Create role (admin)
- `PUT /api/v1/admin/roles/{role_id}` - Update role (admin)
- `DELETE /api/v1/admin/roles/{role_id}` - Delete role (admin)
- `GET /api/v1/admin/permissions` - List permissions (admin)
- `POST /api/v1/admin/permissions` - Create permission (admin)
- `POST /api/v1/admin/roles/{role_id}/permissions` - Assign permissions to role (admin)
- `POST /api/v1/admin/users/{user_id}/roles` - Assign role to user (admin)
- `GET /api/v1/admin/users/{user_id}/roles` - Get user roles (admin)

### Device Management
- `POST /api/v1/zero-trust/devices/register` - Register trusted device
- `GET /api/v1/zero-trust/devices/trusted` - List trusted devices
- `DELETE /api/v1/zero-trust/devices/{device_id}` - Remove trusted device

### Audit & Security
- `GET /api/v1/auth/audit/logs` - User-facing audit feed
- `GET /api/v1/admin/audit/logs` - Filtered admin audit logs
- `GET /api/v1/zero-trust/anomalies/recent` - Detected anomalies
- `GET /api/v1/zero-trust/risk/timeline` - Risk history timeline

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
8. ✅ **Rate Limiting:** Implemented on critical auth endpoints

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

### Phase 3: ✅ MFA Implementation (Current Build)
- [x] TOTP setup & verification
- [x] SMS/Email OTP
- [x] **Picture Password MFA** (Custom gesture recognition with canvas)
- [x] Backup codes
- [x] Unified MFA verification endpoint
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
- [x] Integration tests (API smoke tests completed)
- [ ] Load/stress testing
- [ ] Security testing (penetration testing)
- [x] Documentation & deployment guide
- [x] Docker containerization
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
