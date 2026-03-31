"""
ZTNAS HOD (Head of Department) Routes
Endpoints for department heads to manage faculty, students, and approve device requests
Refactored to use SQLAlchemy ORM for maintainability and security
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from config.database import get_db
from app.models import User, Role, AuditLog, Class, AttendanceRecord, MarksRecord, DeviceRegistry
from utils.security import verify_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hod", tags=["HOD"])

# ==================== PYDANTIC SCHEMAS ====================

class StudentOverview(BaseModel):
    student_id: int
    username: str
    email: str
    enrollment_year: int
    attendance_percentage: float
    average_marks: float
    average_grade: str

class FacultyMember(BaseModel):
    faculty_id: int
    username: str
    email: str
    classes_count: int

class ClassAttendanceStats(BaseModel):
    class_id: int
    class_name: str
    class_code: str
    total_students: int
    average_attendance: float

class DepartmentDashboardSummary(BaseModel):
    faculty_count: int
    students_count: int
    classes_count: int
    average_attendance: float

class AuditLogEntry(BaseModel):
    timestamp: str
    user_id: int
    username: str
    action: str
    resource: str
    resource_id: Optional[int]
    status: str

# ==================== DEPENDENCIES ====================

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header[7:]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_hod_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user has HOD or Dean role"""
    role_names = [role.name.lower() for role in current_user.roles]
    if "hod" not in role_names and "dean" not in role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires HOD or Dean role"
        )
    return current_user

# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/dashboard-summary", response_model=DepartmentDashboardSummary)
async def get_hod_dashboard(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for HOD - counts and averages for department"""
    try:
        # Count faculty members (has faculty role - lowercase)
        faculty_role = db.query(Role).filter(Role.name == "faculty").first()
        faculty_count = 0
        if faculty_role:
            faculty_count = db.query(User).filter(User.roles.any(Role.id == faculty_role.id)).count()
        
        # Count unique students (those with attendance records)
        students_count = db.query(func.count(func.distinct(AttendanceRecord.student_id))).scalar() or 0
        
        # Count classes
        classes_count = db.query(func.count(Class.id)).scalar() or 0
        
        # Calculate average attendance percentage manually
        # Get all attendance records and calculate percentage
        attendance_records = db.query(AttendanceRecord).all()
        if attendance_records:
            present_count = sum(1 for r in attendance_records if r.status == 'PRESENT')
            average_attendance = (present_count / len(attendance_records) * 100)
        else:
            average_attendance = 0.0
        
        return DepartmentDashboardSummary(
            faculty_count=faculty_count,
            students_count=int(students_count),
            classes_count=classes_count,
            average_attendance=round(average_attendance, 2)
        )
    
    except Exception as e:
        logger.error(f"Error getting HOD dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )

# ==================== FACULTY MANAGEMENT ====================

@router.get("/faculty", response_model=List[FacultyMember])
async def get_faculty_list(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db)
):
    """Get all faculty members with their class assignments"""
    try:
        faculty_role = db.query(Role).filter(Role.name == "faculty").first()
        if not faculty_role:
            return []
        
        # Query faculty members
        faculty_users = db.query(User).filter(User.roles.any(Role.id == faculty_role.id)).all()
        
        result = []
        for faculty in faculty_users:
            # Count classes taught by this faculty
            classes_count = db.query(func.count(Class.id)).filter(Class.faculty_id == faculty.id).scalar() or 0
            
            result.append(FacultyMember(
                faculty_id=faculty.id,
                username=faculty.username,
                email=faculty.email,
                classes_count=classes_count
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching faculty list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve faculty list"
        )

# ==================== STUDENT MANAGEMENT ====================

@router.get("/students", response_model=List[StudentOverview])
async def get_students_list(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db),
    search: str = ""
):
    """Get all students with their academic performance metrics"""
    try:
        # Get all students (users with attendance records)
        student_ids = db.query(func.distinct(AttendanceRecord.student_id)).all()
        student_ids = [s[0] for s in student_ids]
        
        if not student_ids:
            return []
        
        # Filter by search term if provided
        query = db.query(User).filter(User.id.in_(student_ids))
        if search:
            query = query.filter(
                (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
            )
        
        students = query.order_by(User.username).all()
        
        result = []
        for student in students:
            # Calculate attendance percentage
            total_attendance = db.query(func.count(AttendanceRecord.id)).filter(
                AttendanceRecord.student_id == student.id
            ).scalar() or 0
            
            present_count = db.query(func.count(AttendanceRecord.id)).filter(
                and_(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.status == 'PRESENT'
                )
            ).scalar() or 0
            
            attendance_pct = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Calculate average marks
            marks_avg = db.query(func.avg(MarksRecord.marks_obtained)).filter(
                MarksRecord.student_id == student.id
            ).scalar() or 0
            
            # Grade calculation based on percentage (marks_avg is already 0-100 scale)
            def calculate_grade(percentage):
                if percentage >= 90:
                    return "A+"
                elif percentage >= 80:
                    return "A"
                elif percentage >= 70:
                    return "B+"
                elif percentage >= 60:
                    return "B"
                elif percentage >= 50:
                    return "C"
                elif percentage >= 40:
                    return "D"
                else:
                    return "F"
            
            avg_grade = calculate_grade(float(marks_avg))
            
            # Extract enrollment year from created_at
            enrollment_year = student.created_at.year if student.created_at else 2024
            
            result.append(StudentOverview(
                student_id=student.id,
                username=student.username,
                email=student.email,
                enrollment_year=enrollment_year,
                attendance_percentage=round(attendance_pct, 2),
                average_marks=round(float(marks_avg), 2),
                average_grade=avg_grade
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student list"
        )

# ==================== ATTENDANCE OVERVIEW ====================

@router.get("/attendance-overview", response_model=List[ClassAttendanceStats])
async def get_attendance_overview(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db)
):
    """Get department-wide attendance statistics per class"""
    try:
        classes = db.query(Class).all()
        
        result = []
        for cls in classes:
            # Count total students in class
            total_students = db.query(func.count(func.distinct(AttendanceRecord.student_id))).filter(
                AttendanceRecord.class_id == cls.id
            ).scalar() or 0
            
            # Calculate average attendance for class
            present_count = db.query(func.count(AttendanceRecord.id)).filter(
                and_(
                    AttendanceRecord.class_id == cls.id,
                    AttendanceRecord.status == 'PRESENT'
                )
            ).scalar() or 0
            
            total_count = db.query(func.count(AttendanceRecord.id)).filter(
                AttendanceRecord.class_id == cls.id
            ).scalar() or 0
            
            avg_attendance = (present_count / total_count * 100) if total_count > 0 else 0
            
            result.append(ClassAttendanceStats(
                class_id=cls.id,
                class_name=cls.name,
                class_code=cls.code,
                total_students=total_students,
                average_attendance=round(avg_attendance, 2)
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting attendance overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attendance overview"
        )


# ==================== AUDIT LOGS ====================

@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def get_department_audit_logs(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get audit logs for department activities with activity filtering"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query audit logs from the specified date range, ordered by timestamp desc
        logs = db.query(AuditLog).join(User).filter(
            AuditLog.timestamp >= cutoff_date
        ).order_by(AuditLog.timestamp.desc()).limit(100).all()
        
        result = []
        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first()
            result.append(AuditLogEntry(
                timestamp=log.timestamp.isoformat() if log.timestamp else "",
                user_id=log.user_id or 0,
                username=user.username if user else "Unknown",
                action=log.action,
                resource=log.resource or "",
                resource_id=log.resource_id,
                status=log.status
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


# ==================== UNDERPERFORMING STUDENTS ====================

@router.get("/underperforming-students")
async def get_underperforming_students(
    current_user: User = Depends(get_hod_user),
    db: Session = Depends(get_db),
    attendance_threshold: float = 75.0,
    marks_threshold: float = 50.0
):
    """Get students who are below threshold for attendance or marks"""
    try:
        # Get all students with their metrics
        student_ids = db.query(func.distinct(AttendanceRecord.student_id)).all()
        student_ids = [s[0] for s in student_ids]
        
        if not student_ids:
            return {"underperforming_students": []}
        
        students = db.query(User).filter(User.id.in_(student_ids)).all()
        
        underperforming = []
        for student in students:
            # Calculate attendance
            total_attendance = db.query(func.count(AttendanceRecord.id)).filter(
                AttendanceRecord.student_id == student.id
            ).scalar() or 0
            
            present_count = db.query(func.count(AttendanceRecord.id)).filter(
                and_(
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.status == 'PRESENT'
                )
            ).scalar() or 0
            
            attendance_pct = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Calculate average marks
            marks_avg = db.query(func.avg(MarksRecord.marks_obtained)).filter(
                MarksRecord.student_id == student.id
            ).scalar() or 0
            
            # Check if underperforming
            is_low_attendance = attendance_pct < attendance_threshold
            is_low_marks = marks_avg < marks_threshold
            
            if is_low_attendance or is_low_marks:
                underperforming.append({
                    "student_id": student.id,
                    "username": student.username,
                    "email": student.email,
                    "attendance_percentage": round(attendance_pct, 2),
                    "average_marks": round(float(marks_avg), 2),
                    "reason": [
                        "Low attendance" if is_low_attendance else None,
                        "Low marks" if is_low_marks else None
                    ]
                })
        
        return {"underperforming_students": underperforming}
    
    except Exception as e:
        logger.error(f"Error getting underperforming students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve underperforming students"
        )

