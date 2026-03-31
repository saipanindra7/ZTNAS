"""
ZTNAS Student Routes - Marks, Attendance, Fees
Endpoints for students to view their academic data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import List, Optional
from config.database import get_db
from app.models import User, AttendanceRecord, MarksRecord, StudentFees, Class
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/student", tags=["Student"])

# ==================== DEPENDENCIES ====================

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    from utils.security import verify_access_token
    
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

# ==================== ATTENDANCE ENDPOINTS ====================

@router.get("/attendance")
async def get_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get attendance records for current student (last N days)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = db.query(
            AttendanceRecord.id,
            Class.name.label("class_name"),
            AttendanceRecord.attendance_date,
            AttendanceRecord.status,
            AttendanceRecord.remarks
        ).join(
            Class, AttendanceRecord.class_id == Class.id
        ).filter(
            AttendanceRecord.student_id == current_user.id,
            AttendanceRecord.attendance_date >= cutoff_date
        ).order_by(
            AttendanceRecord.attendance_date.desc()
        ).all()
        
        return [
            {
                "id": r.id,
                "class_name": r.class_name,
                "attendance_date": r.attendance_date.isoformat() if r.attendance_date else None,
                "status": r.status,
                "remarks": r.remarks
            }
            for r in records
        ]
    
    except Exception as e:
        logger.error(f"Error fetching attendance: {e}")
        raise HTTPException(status_code=500, detail="Error fetching attendance records")

@router.get("/attendance/summary")
async def get_attendance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance summary for current student"""
    try:
        total_classes = db.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.student_id == current_user.id
        ).scalar() or 0
        
        present_count = db.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.student_id == current_user.id,
            AttendanceRecord.status == "PRESENT"
        ).scalar() or 0
        
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        return {
            "total_classes": total_classes,
            "present_count": present_count,
            "attendance_percentage": round(attendance_percentage, 2)
        }
    
    except Exception as e:
        logger.error(f"Error calculating attendance: {e}")
        return {"total_classes": 0, "present_count": 0, "attendance_percentage": 0}

# ==================== MARKS ENDPOINTS ====================

@router.get("/marks")
async def get_marks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all marks for current student"""
    try:
        records = db.query(
            MarksRecord.id,
            Class.name.label("class_name"),
            MarksRecord.exam_type,
            MarksRecord.marks_obtained,
            MarksRecord.total_marks,
            MarksRecord.grade
        ).join(
            Class, MarksRecord.class_id == Class.id
        ).filter(
            MarksRecord.student_id == current_user.id
        ).order_by(
            Class.name, MarksRecord.exam_type
        ).all()
        
        return [
            {
                "id": r.id,
                "class_name": r.class_name,
                "exam_type": r.exam_type,
                "marks_obtained": float(r.marks_obtained),
                "total_marks": float(r.total_marks),
                "grade": r.grade
            }
            for r in records
        ]
    
    except Exception as e:
        logger.error(f"Error fetching marks: {e}")
        raise HTTPException(status_code=500, detail="Error fetching marks records")

@router.get("/marks/summary")
async def get_marks_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get marks summary for current student"""
    try:
        result = db.query(
            func.avg(MarksRecord.marks_obtained).label("average_marks"),
            func.max(MarksRecord.marks_obtained).label("highest_marks"),
            func.min(MarksRecord.marks_obtained).label("lowest_marks"),
            func.count(MarksRecord.id).label("total_exams")
        ).filter(
            MarksRecord.student_id == current_user.id
        ).first()
        
        if not result or not result.average_marks:
            return {
                "average_marks": 0,
                "highest_marks": 0,
                "lowest_marks": 0,
                "total_exams": 0,
                "average_grade": "N/A"
            }
        
        avg = float(result.average_marks)
        
        # Calculate grade from average
        if avg >= 90: grade = "A+"
        elif avg >= 85: grade = "A"
        elif avg >= 80: grade = "B+"
        elif avg >= 75: grade = "B"
        elif avg >= 70: grade = "C"
        elif avg >= 60: grade = "D"
        else: grade = "F"
        
        return {
            "average_marks": round(avg, 2),
            "highest_marks": float(result.highest_marks) if result.highest_marks else 0,
            "lowest_marks": float(result.lowest_marks) if result.lowest_marks else 0,
            "total_exams": result.total_exams,
            "average_grade": grade
        }
    
    except Exception as e:
        logger.error(f"Error calculating marks summary: {e}")
        return {
            "average_marks": 0,
            "highest_marks": 0,
            "lowest_marks": 0,
            "total_exams": 0,
            "average_grade": "N/A"
        }

# ==================== FEES ENDPOINTS ====================

@router.get("/fees")
async def get_fees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all fee records for current student"""
    try:
        records = db.query(StudentFees).filter(
            StudentFees.student_id == current_user.id
        ).order_by(
            StudentFees.academic_year.desc(), StudentFees.semester.desc()
        ).all()
        
        return [
            {
                "id": r.id,
                "academic_year": r.academic_year,
                "semester": r.semester,
                "total_fee": float(r.total_fee),
                "paid_amount": float(r.paid_amount),
                "fee_status": r.fee_status,
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "payment_date": r.payment_date.isoformat() if r.payment_date else None
            }
            for r in records
        ]
    
    except Exception as e:
        logger.error(f"Error fetching fees: {e}")
        raise HTTPException(status_code=500, detail="Error fetching fee records")

@router.get("/fees/summary")
async def get_fees_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get fee summary for current student"""
    try:
        result = db.query(
            func.sum(StudentFees.total_fee).label("total_fee"),
            func.sum(StudentFees.paid_amount).label("paid_fee")
        ).filter(
            StudentFees.student_id == current_user.id
        ).first()
        
        if not result or not result.total_fee:
            return {
                "total_fee": 0,
                "paid_fee": 0,
                "pending_fee": 0,
                "fee_status": "NO_RECORDS"
            }
        
        total = float(result.total_fee)
        paid = float(result.paid_fee) if result.paid_fee else 0
        pending = total - paid
        
        if pending > 0:
            fee_status = "PENDING"
        elif paid == total:
            fee_status = "PAID"
        else:
            fee_status = "PARTIAL"
        
        return {
            "total_fee": total,
            "paid_fee": paid,
            "pending_fee": pending,
            "fee_status": fee_status
        }
    
    except Exception as e:
        logger.error(f"Error calculating fee summary: {e}")
        return {
            "total_fee": 0,
            "paid_fee": 0,
            "pending_fee": 0,
            "fee_status": "ERROR"
        }

# ==================== STUDENT DASHBOARD SUMMARY ====================

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete dashboard summary for student"""
    try:
        # Get attendance
        att_result = db.query(
            func.count(AttendanceRecord.id).label("total"),
            func.sum(case((AttendanceRecord.status == "PRESENT", 1), else_=0)).label("present")
        ).filter(
            AttendanceRecord.student_id == current_user.id
        ).first()
        
        att_total = att_result.total if att_result else 0
        att_present = att_result.present if att_result else 0
        att_percentage = (att_present / att_total * 100) if att_total > 0 else 0
        
        # Get marks
        marks_result = db.query(
            func.avg(MarksRecord.marks_obtained)
        ).filter(
            MarksRecord.student_id == current_user.id
        ).scalar()
        
        avg_marks = float(marks_result) if marks_result else 0
        
        if avg_marks >= 90: avg_grade = "A+"
        elif avg_marks >= 85: avg_grade = "A"
        elif avg_marks >= 80: avg_grade = "B+"
        elif avg_marks >= 75: avg_grade = "B"
        else: avg_grade = "C"
        
        # Get fees
        fees_result = db.query(
            func.sum(StudentFees.total_fee),
            func.sum(StudentFees.paid_amount)
        ).filter(
            StudentFees.student_id == current_user.id
        ).first()
        
        total_fee = float(fees_result[0]) if fees_result and fees_result[0] else 0
        paid_fee = float(fees_result[1]) if fees_result and fees_result[1] else 0
        pending_fee = total_fee - paid_fee
        
        return {
            "attendance_percentage": round(att_percentage, 2),
            "average_grade": avg_grade,
            "total_marks": round(avg_marks, 2),
            "total_fee": total_fee,
            "paid_fee": paid_fee,
            "pending_fee": pending_fee,
            "fee_status": "PENDING" if pending_fee > 0 else "PAID"
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return {
            "attendance_percentage": 0,
            "average_grade": "N/A",
            "total_marks": 0,
            "total_fee": 0,
            "paid_fee": 0,
            "pending_fee": 0,
            "fee_status": "ERROR"
        }
