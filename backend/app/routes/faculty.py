"""
ZTNAS Faculty Routes - Marking Attendance and Grades
Endpoints for faculty to manage their classes, mark attendance, and enter grades
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import logging

from config.database import get_db
from app.models import User, Class, AttendanceRecord, MarksRecord, AuditLog
from utils.security import verify_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/faculty", tags=["Faculty"])

# ==================== SCHEMAS ====================

class AttendanceRecordInput(BaseModel):
    student_id: int
    status: str  # PRESENT, ABSENT, LEAVE, LATE
    remarks: Optional[str] = None

class AttendanceSubmission(BaseModel):
    class_id: int
    attendance_date: str  # YYYY-MM-DD
    records: List[AttendanceRecordInput]

class MarksRecordInput(BaseModel):
    student_id: int
    marks_obtained: float
    total_marks: float = 100.0

class MarksSubmission(BaseModel):
    class_id: int
    exam_type: str  # mid_term, final, quiz_1, quiz_2, assign1, assign2
    records: List[MarksRecordInput]

class ClassDetail(BaseModel):
    id: int
    name: str
    code: str
    department: str
    semester: int
    student_count: int

class StudentDetail(BaseModel):
    student_id: int
    username: str
    email: str
    attendance_percentage: float
    average_marks: float
    average_grade: str

class DashboardSummary(BaseModel):
    classes_count: int
    students_count: int
    total_attendance_records: int
    average_attendance_percentage: float

# ==================== DEPENDENCIES ====================

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Extract and validate JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

def get_faculty_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
) -> User:
    """Get current faculty user"""
    try:
        current_user = get_current_user(authorization=authorization, db=db)
        
        # Check faculty role
        faculty_roles = [role.name.lower() for role in current_user.roles]
        if "faculty" not in faculty_roles:
            raise HTTPException(status_code=403, detail="Only faculty can access this endpoint")
        
        return current_user
    except HTTPException:
        raise

# ==================== CLASS ENDPOINTS ====================

@router.get("/my-classes", response_model=List[ClassDetail])
async def get_my_classes(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get all classes assigned to current faculty"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Query classes for this faculty
        classes = db.query(Class).filter(Class.faculty_id == current_user.id).all()
        
        result = []
        for cls in classes:
            # Count enrolled students (distinct students with any attendance record)
            student_count = db.query(AttendanceRecord.student_id)\
                .distinct()\
                .filter(AttendanceRecord.class_id == cls.id)\
                .count()
            
            result.append(ClassDetail(
                id=cls.id,
                name=cls.name,
                code=cls.code,
                department=cls.department or "N/A",
                semester=cls.semester,
                student_count=student_count
            ))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching faculty classes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch classes")

@router.get("/classes/{class_id}/students", response_model=List[StudentDetail])
async def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get all students in a specific class"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Verify faculty owns this class
        cls = db.query(Class).filter(
            Class.id == class_id,
            Class.faculty_id == current_user.id
        ).first()
        
        if not cls:
            raise HTTPException(status_code=403, detail="You don't have access to this class")
        
        # Get distinct students from attendance records
        attendance_records = db.query(AttendanceRecord.student_id)\
            .distinct()\
            .filter(AttendanceRecord.class_id == class_id)\
            .all()
        
        student_ids = [record[0] for record in attendance_records]
        
        result = []
        for student_id in student_ids:
            # Get user info
            user = db.query(User).filter(User.id == student_id).first()
            if not user:
                continue
            
            # Calculate attendance percentage
            total_attendance = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.class_id == class_id
            ).count()
            
            present_count = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.class_id == class_id,
                AttendanceRecord.status == "PRESENT"
            ).count()
            
            attendance_pct = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Calculate average marks and grade
            marks_records = db.query(MarksRecord).filter(
                MarksRecord.student_id == student_id,
                MarksRecord.class_id == class_id
            ).all()
            
            if marks_records:
                avg_marks = sum(m.marks_obtained for m in marks_records) / len(marks_records)
                # Simple grading
                if avg_marks >= 90: grade = "A+"
                elif avg_marks >= 85: grade = "A"
                elif avg_marks >= 80: grade = "B+"
                elif avg_marks >= 75: grade = "B"
                elif avg_marks >= 70: grade = "C"
                else: grade = "D"
            else:
                avg_marks = 0
                grade = "N/A"
            
            result.append(StudentDetail(
                student_id=student_id,
                username=user.username,
                email=user.email,
                attendance_percentage=round(attendance_pct, 2),
                average_marks=round(avg_marks, 2),
                average_grade=grade
            ))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching class students: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch students")

# ==================== ATTENDANCE ENDPOINTS ====================

@router.post("/attendance/mark", status_code=201)
async def mark_attendance(
    attendance: AttendanceSubmission,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Mark attendance for a class on a specific date"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Verify faculty owns this class
        cls = db.query(Class).filter(
            Class.id == attendance.class_id,
            Class.faculty_id == current_user.id
        ).first()
        
        if not cls:
            raise HTTPException(status_code=403, detail="You don't have permission to mark attendance for this class")
        
        # Parse date
        try:
            att_date = datetime.strptime(attendance.attendance_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Insert attendance records
        success_count = 0
        for record in attendance.records:
            try:
                # Check if record already exists
                existing = db.query(AttendanceRecord).filter(
                    AttendanceRecord.student_id == record.student_id,
                    AttendanceRecord.class_id == attendance.class_id,
                    AttendanceRecord.attendance_date >= datetime(att_date.year, att_date.month, att_date.day),
                    AttendanceRecord.attendance_date < datetime(att_date.year, att_date.month, att_date.day) + timedelta(days=1)
                ).first()
                
                if existing:
                    # Update existing
                    existing.status = record.status
                    existing.remarks = record.remarks
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    att_record = AttendanceRecord(
                        student_id=record.student_id,
                        class_id=attendance.class_id,
                        attendance_date=att_date,
                        status=record.status,
                        remarks=record.remarks or None,
                        marked_by=current_user.id
                    )
                    db.add(att_record)
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error marking attendance for student {record.student_id}: {e}")
        
        db.commit()
        
        # Log action
        audit = AuditLog(
            user_id=current_user.id,
            action="MARK_ATTENDANCE",
            resource="classes",
            resource_id=attendance.class_id,
            status="success",
            details=f"Marked attendance for {success_count} students on {attendance.attendance_date}"
        )
        db.add(audit)
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully marked attendance for {success_count} students",
            "records_created": success_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_attendance: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark attendance")

@router.get("/attendance/{class_id}", response_model=dict)
async def get_attendance_history(
    class_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get attendance history for a class"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Verify faculty owns this class
        cls = db.query(Class).filter(
            Class.id == class_id,
            Class.faculty_id == current_user.id
        ).first()
        
        if not cls:
            raise HTTPException(status_code=403, detail="You don't have access to this class")
        
        # Get attendance records from last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.class_id == class_id,
            AttendanceRecord.attendance_date >= cutoff_date
        ).order_by(AttendanceRecord.attendance_date.desc()).all()
        
        # Group by date
        by_date = {}
        for record in records:
            date_str = record.attendance_date.strftime("%Y-%m-%d")
            if date_str not in by_date:
                by_date[date_str] = []
            
            by_date[date_str].append({
                "student_id": record.student_id,
                "status": record.status,
                "remarks": record.remarks
            })
        
        return {
            "class_id": class_id,
            "class_name": cls.name,
            "days": days,
            "records_count": len(records),
            "attendance_by_date": by_date
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attendance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance history")

# ==================== MARKS ENDPOINTS ====================

def calculate_grade(obtained: float, total: float) -> str:
    """Calculate letter grade from marks"""
    if total == 0:
        return "N/A"
    percentage = (obtained / total) * 100
    if percentage >= 90: return "A+"
    elif percentage >= 85: return "A"
    elif percentage >= 80: return "B+"
    elif percentage >= 75: return "B"
    elif percentage >= 70: return "C"
    elif percentage >= 60: return "D"
    else: return "F"

@router.post("/marks/enter", status_code=201)
async def enter_marks(
    marks: MarksSubmission,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Enter marks for students in a specific exam"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Verify faculty owns this class
        cls = db.query(Class).filter(
            Class.id == marks.class_id,
            Class.faculty_id == current_user.id
        ).first()
        
        if not cls:
            raise HTTPException(status_code=403, detail="You don't have permission to enter marks for this class")
        
        # Insert marks records
        success_count = 0
        for record in marks.records:
            try:
                grade = calculate_grade(record.marks_obtained, record.total_marks)
                percentage = (record.marks_obtained / record.total_marks * 100) if record.total_marks > 0 else 0
                
                # Check if marks already exist
                existing = db.query(MarksRecord).filter(
                    MarksRecord.student_id == record.student_id,
                    MarksRecord.class_id == marks.class_id,
                    MarksRecord.exam_type == marks.exam_type
                ).first()
                
                if existing:
                    # Update existing
                    existing.marks_obtained = record.marks_obtained
                    existing.total_marks = record.total_marks
                    existing.percentage = percentage
                    existing.grade = grade
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    marks_record = MarksRecord(
                        student_id=record.student_id,
                        class_id=marks.class_id,
                        exam_type=marks.exam_type,
                        marks_obtained=record.marks_obtained,
                        total_marks=record.total_marks,
                        percentage=percentage,
                        grade=grade
                    )
                    db.add(marks_record)
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error entering marks for student {record.student_id}: {e}")
        
        db.commit()
        
        # Log action
        audit = AuditLog(
            user_id=current_user.id,
            action="ENTER_MARKS",
            resource="marks",
            resource_id=marks.class_id,
            status="success",
            details=f"Entered {marks.exam_type} marks for {success_count} students"
        )
        db.add(audit)
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully entered marks for {success_count} students",
            "exam_type": marks.exam_type,
            "records_created": success_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enter_marks: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to enter marks")

@router.get("/marks/{class_id}", response_model=dict)
async def get_marks_history(
    class_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get all marks entered for a class"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Verify faculty owns this class
        cls = db.query(Class).filter(
            Class.id == class_id,
            Class.faculty_id == current_user.id
        ).first()
        
        if not cls:
            raise HTTPException(status_code=403, detail="You don't have access to this class")
        
        # Get all marks records for this class
        marks_records = db.query(MarksRecord).filter(
            MarksRecord.class_id == class_id
        ).all()
        
        # Group by exam type
        by_exam = {}
        for record in marks_records:
            if record.exam_type not in by_exam:
                by_exam[record.exam_type] = []
            
            by_exam[record.exam_type].append({
                "student_id": record.student_id,
                "marks_obtained": record.marks_obtained,
                "total_marks": record.total_marks,
                "percentage": record.percentage,
                "grade": record.grade
            })
        
        return {
            "class_id": class_id,
            "class_name": cls.name,
            "total_records": len(marks_records),
            "marks_by_exam": by_exam
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting marks history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch marks history")

# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/dashboard", response_model=DashboardSummary)
async def get_faculty_dashboard(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get faculty dashboard summary"""
    try:
        current_user = get_faculty_user(db=db, authorization=authorization)
        
        # Count classes
        classes_count = db.query(Class).filter(Class.faculty_id == current_user.id).count()
        
        # Count unique students across all classes
        students_count = db.query(AttendanceRecord.student_id)\
            .join(Class, AttendanceRecord.class_id == Class.id)\
            .filter(Class.faculty_id == current_user.id)\
            .distinct()\
            .count()
        
        # Count total attendance records
        total_attendance_records = db.query(AttendanceRecord)\
            .join(Class, AttendanceRecord.class_id == Class.id)\
            .filter(Class.faculty_id == current_user.id)\
            .count()
        
        # Calculate average attendance percentage
        attendance_stats = db.query(AttendanceRecord)\
            .join(Class, AttendanceRecord.class_id == Class.id)\
            .filter(Class.faculty_id == current_user.id).all()
        
        if attendance_stats:
            present_count = sum(1 for a in attendance_stats if a.status == "PRESENT")
            avg_attendance = (present_count / len(attendance_stats) * 100) if attendance_stats else 0
        else:
            avg_attendance = 0
        
        return DashboardSummary(
            classes_count=classes_count,
            students_count=students_count,
            total_attendance_records=total_attendance_records,
            average_attendance_percentage=round(avg_attendance, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting faculty dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")
