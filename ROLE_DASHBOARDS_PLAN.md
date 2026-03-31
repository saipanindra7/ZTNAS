# ZTNAS Role-Based Dashboards - Implementation Plan

## Architecture Overview

### Current State
- Single dashboard trying to serve all roles
- Navigation buttons not properly wired
- No role-specific views
- No device authorization
- No MFA enforcement per login

### Desired State
- **Admin Dashboard**: System controls, user management, policies, audit logs
- **HOD Dashboard**: Department oversight, faculty/student management, department metrics
- **Faculty Dashboard**: Class management, attendance, marks, student assessments
- **Student Dashboard**: View own attendance, marks, schedule, device management

---

## Implementation Phases

### Phase 1: Fix Navigation (IMMEDIATE)
- Create separate dashboard pages for each role
- Implement proper navigation routing
- Fix button click handlers

### Phase 2: Role-Specific Features
**Admin**: User CRUD, View all devices, Audit logs, Policies
**HOD**: Manage faculty, view department students, approve requests
**Faculty**: Manage classes, attendance, marks, view students
**Student**: View own attendance, marks, request device access

### Phase 3: Device Authorization System
- Device registration on first login
- Device reject/verification on new device
- Permission request to HOD/Faculty
- Device approval workflow

### Phase 4: Enhanced MFA
- MFA required on every login (not just first time)
- MFA method options shown on login
- Session validation after MFA

### Phase 5: Permission Request System
- Student/Faculty requests device access
- HOD/Faculty reviews and approves
- Audit trail of approvals
- Auto-rejection after inactivity

---

## File Structure (Proposed)

```
frontend/static/html/
├── dashboard-admin.html      [NEW] Admin control panel
├── dashboard-hod.html        [NEW] HOD department view
├── dashboard-faculty.html    [NEW] Faculty class view
├── dashboard-student.html    [NEW] Student personal view
└── device-permission.html    [NEW] Device authorization request

frontend/static/js/
├── dashboards/
│   ├── admin-dashboard.js    [NEW]
│   ├── hod-dashboard.js      [NEW]
│   ├── faculty-dashboard.js  [NEW]
│   └── student-dashboard.js  [NEW]
├── device-auth.js            [NEW] Device authorization system
├── mfa-manager.js            [NEW] MFA enforcement
└── permission-flow.js        [NEW] Request/approval system

backend/app/routes/
├── faculty.py                [NEW] Faculty endpoints
├── hod.py                    [NEW] HOD endpoints
├── student.py                [NEW] Student endpoints
├── device_auth.py            [NEW] Device authorization
└── permissions.py            [NEW] Permission requests
```

---

## Database Changes Needed

### New Tables
```sql
device_authorizations - Track device approval status
class_sessions - Faculty class management
attendance_records - Track student attendance
marks_records - Student marks/grades
permission_requests - Device access requests
approval_workflows - Track approvals by role
```

### Modified Tables
```sql
devices - Add approval_status, approved_by
users - Add department_id (for HOD/Faculty association)
```

---

## Implementation Priority

### Week 1: Foundation
1. Create separate dashboard pages per role ✓ Priority 1
2. Implement navigation routing ✓ Priority 1
3. Fix dashboard button handlers ✓ Priority 1
4. Create basic role-specific views ✓ Priority 1

### Week 2: Device System
1. Device registration on first login ✓ Priority 2
2. Device verification/rejection ✓ Priority 2
3. Permission request UI ✓ Priority 2

### Week 3: MFA & Features
1. MFA enforcement on every login ✓ Priority 2
2. Faculty attendance/marks features ✓ Priority 3
3. HOD management features ✓ Priority 3

---

## Quick Start Actions

### Immediate (Next 30 min)
1. Create dashboard-student.html with basic student view
2. Create dashboard-faculty.html with class management
3. Create dashboard-hod.html with department view
4. Update login redirect logic to route to correct dashboard
5. Fix button navigation

### Short-term (Next 2 hours)
1. Implement device authorization flow
2. Add device verification UI
3. Add permission request modal

### Medium-term (Next 6 hours)
1. Create backend endpoints for each role
2. Implement attendance/marks system
3. Add MFA enforcement on login

---

## Current Blockers

❌ Dashboard navigation not working reliably
❌ No role-specific views
❌ Device authorization not implemented
❌ MFA enforcement missing from login flow
❌ No class/attendance management

---

## Questions to Clarify

1. Should HOD approve device access, or Class Teacher?
2. How many login attempts before device locked out?
3. Should MFA be skipped if device is trusted?
4. What are the approval workflow timeouts?
5. Should faculty see all student data or just their class?

---

## Success Criteria

✅ Admin logs in → sees Admin Dashboard → all buttons work
✅ Faculty logs in → sees Faculty Dashboard → attendance/marks visible
✅ HOD logs in → sees HOD Dashboard → can manage faculty/students
✅ Student logs in → sees Student Dashboard → own data only
✅ New device login → asks for verification → requires approval
✅ Every login → MFA verification → then dashboard access
✅ Device not approved → permissions request flows → admin/HOD reviews
