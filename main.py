from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os
import models, schemas, database
from database import get_db, engine

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MSL Engagement Management System")

# CORS configuration from environment variables
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AUTHENTICATION ====================

@app.post("/api/login", response_model=schemas.LoginResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Mock login - validates username and role"""
    valid_roles = ["BL", "BM", "MSL", "SBUH/BH", "MSL Manager", "HOD"]
    
    if login_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    return {
        "username": login_data.username,
        "role": login_data.role,
        "message": "Login successful"
    }

# ==================== DOCTORS ====================

@app.get("/api/doctors", response_model=List[schemas.Doctor])
def get_doctors(
    priority_only: bool = Query(False, description="Filter priority doctors only"),
    db: Session = Depends(get_db)
):
    """Get all doctors, optionally filtered by priority"""
    query = db.query(models.Doctor)
    if priority_only:
        query = query.filter(models.Doctor.is_priority_doctor == True)
    doctors = query.order_by(
        models.Doctor.is_priority_doctor.desc(),
        models.Doctor.name
    ).all()
    return doctors

@app.post("/api/doctors", response_model=schemas.Doctor)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    """Create a new doctor"""
    db_doctor = models.Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

@app.get("/api/doctors/{doctor_id}", response_model=schemas.Doctor)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Get a specific doctor by ID"""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.post("/api/doctors/{doctor_id}/duplicate", response_model=schemas.Doctor)
def duplicate_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Duplicate a doctor"""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Create a duplicate with "(Copy)" suffix
    new_doctor = models.Doctor(
        name=f"{doctor.name} (Copy)",
        therapy_area=doctor.therapy_area,
        is_priority_doctor=doctor.is_priority_doctor
    )
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor

@app.delete("/api/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Delete a doctor"""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    db.delete(doctor)
    db.commit()
    return {"message": "Doctor deleted successfully"}

# ==================== REQUESTS ====================

@app.post("/api/requests", response_model=schemas.Request)
def create_request(request: schemas.RequestCreate, db: Session = Depends(get_db)):
    """Create a new MSL engagement request"""
    # Verify doctor exists
    doctor = db.query(models.Doctor).filter(models.Doctor.id == request.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    db_request = models.Request(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/api/requests", response_model=List[schemas.RequestSummary])
def get_requests(
    requested_by: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get requests with optional filters"""
    query = db.query(
        models.Request,
        models.Doctor.name.label("doctor_name")
    ).join(models.Doctor, models.Request.doctor_id == models.Doctor.id)
    
    if requested_by:
        query = query.filter(models.Request.requested_by == requested_by)
    if status:
        query = query.filter(models.Request.status == status)
    
    # Role-based filtering
    if role in ["BL", "BM"]:
        query = query.filter(models.Request.requested_by_role == role)
    
    results = query.order_by(models.Request.created_at.desc()).all()
    
    request_summaries = []
    for result in results:
        request, doctor_name = result
        summary = schemas.RequestSummary(
            id=request.id,
            doctor_id=request.doctor_id,
            requested_by=request.requested_by,
            requested_by_role=request.requested_by_role,
            therapy_area=request.therapy_area,
            objective=request.objective,
            expected_outcome=request.expected_outcome,
            priority=request.priority,
            status=request.status,
            created_at=request.created_at,
            doctor_name=doctor_name
        )
        request_summaries.append(summary)
    
    return request_summaries

@app.get("/api/requests/{request_id}", response_model=schemas.Request)
def get_request(request_id: int, db: Session = Depends(get_db)):
    """Get a specific request with all details"""
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@app.put("/api/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update request status"""
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = status
    db.commit()
    return {"message": "Status updated successfully"}

# ==================== DOCTOR INTERACTIONS ====================

@app.post("/api/doctor-interactions", response_model=schemas.DoctorInteraction)
def create_doctor_interaction(
    interaction: schemas.DoctorInteractionCreate,
    db: Session = Depends(get_db)
):
    """Log a doctor interaction"""
    # Verify request exists
    request = db.query(models.Request).filter(models.Request.id == interaction.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db_interaction = models.DoctorInteraction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@app.get("/api/requests/{request_id}/interactions", response_model=List[schemas.DoctorInteraction])
def get_doctor_interactions(request_id: int, db: Session = Depends(get_db)):
    """Get all doctor interactions for a request"""
    interactions = db.query(models.DoctorInteraction).filter(
        models.DoctorInteraction.request_id == request_id
    ).order_by(models.DoctorInteraction.visit_date.desc()).all()
    return interactions

# ==================== OFFICE ACTIVITIES ====================

@app.post("/api/office-activities", response_model=schemas.OfficeActivity)
def create_office_activity(
    activity: schemas.OfficeActivityCreate,
    db: Session = Depends(get_db)
):
    """Log an office activity"""
    # Verify request exists
    request = db.query(models.Request).filter(models.Request.id == activity.request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db_activity = models.OfficeActivity(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@app.get("/api/requests/{request_id}/activities", response_model=List[schemas.OfficeActivity])
def get_office_activities(request_id: int, db: Session = Depends(get_db)):
    """Get all office activities for a request"""
    activities = db.query(models.OfficeActivity).filter(
        models.OfficeActivity.request_id == request_id
    ).order_by(models.OfficeActivity.activity_date.desc()).all()
    return activities

# ==================== SUMMARY VIEW ====================

@app.get("/api/requests/{request_id}/logs", response_model=List[schemas.ActivityLog])
def get_request_logs(request_id: int, db: Session = Depends(get_db)):
    """Get all activity logs (interactions + office activities) for a request, sorted by date"""
    # Verify request exists
    request = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    logs = []
    
    # Get doctor interactions
    interactions = db.query(models.DoctorInteraction).filter(
        models.DoctorInteraction.request_id == request_id
    ).all()
    
    for interaction in interactions:
        logs.append(schemas.ActivityLog(
            id=interaction.id,
            type="doctor_interaction",
            date=interaction.visit_date,
            title=f"Doctor Visit: {interaction.doctor_name}",
            details=interaction.summary,
            created_at=interaction.created_at
        ))
    
    # Get office activities
    activities = db.query(models.OfficeActivity).filter(
        models.OfficeActivity.request_id == request_id
    ).all()
    
    for activity in activities:
        logs.append(schemas.ActivityLog(
            id=activity.id,
            type="office_activity",
            date=activity.activity_date,
            title=f"Office Activity: {activity.activity_category}",
            details=activity.summary,
            created_at=activity.created_at
        ))
    
    # Sort by date (latest first)
    logs.sort(key=lambda x: x.date, reverse=True)
    
    return logs

# ==================== SEED DATA ====================

@app.post("/api/seed-doctors")
def seed_doctors(db: Session = Depends(get_db)):
    """Seed comprehensive fake doctors data"""
    fake_doctors = [
        # Priority Doctors - Cardiology
        {"name": "Dr. Rajesh Kumar", "therapy_area": "Cardiology", "is_priority_doctor": True},
        {"name": "Dr. Sunita Gupta", "therapy_area": "Cardiology", "is_priority_doctor": True},
        {"name": "Dr. Arun Mehta", "therapy_area": "Cardiology", "is_priority_doctor": True},
        
        # Priority Doctors - Oncology
        {"name": "Dr. Priya Sharma", "therapy_area": "Oncology", "is_priority_doctor": True},
        {"name": "Dr. Vikram Iyer", "therapy_area": "Oncology", "is_priority_doctor": True},
        {"name": "Dr. Neha Joshi", "therapy_area": "Oncology", "is_priority_doctor": True},
        
        # Priority Doctors - Neurology
        {"name": "Dr. Sanjay Verma", "therapy_area": "Neurology", "is_priority_doctor": True},
        {"name": "Dr. Meera Krishnan", "therapy_area": "Neurology", "is_priority_doctor": True},
        
        # Priority Doctors - Other Specialties
        {"name": "Dr. Anil Deshmukh", "therapy_area": "Diabetology", "is_priority_doctor": True},
        {"name": "Dr. Kavita Rao", "therapy_area": "Endocrinology", "is_priority_doctor": True},
        {"name": "Dr. Ramesh Shetty", "therapy_area": "Nephrology", "is_priority_doctor": True},
        {"name": "Dr. Fatima Khan", "therapy_area": "Gastroenterology", "is_priority_doctor": True},
        
        # Regular Doctors - Cardiology
        {"name": "Dr. Amit Patel", "therapy_area": "Cardiology", "is_priority_doctor": False},
        {"name": "Dr. Vikram Singh", "therapy_area": "Cardiology", "is_priority_doctor": False},
        {"name": "Dr. Suresh Nair", "therapy_area": "Cardiology", "is_priority_doctor": False},
        {"name": "Dr. Pooja Shah", "therapy_area": "Cardiology", "is_priority_doctor": False},
        
        # Regular Doctors - Oncology
        {"name": "Dr. Ananya Reddy", "therapy_area": "Oncology", "is_priority_doctor": False},
        {"name": "Dr. Rahul Gandhi", "therapy_area": "Oncology", "is_priority_doctor": False},
        {"name": "Dr. Shalini Menon", "therapy_area": "Oncology", "is_priority_doctor": False},
        {"name": "Dr. Karthik Subramanian", "therapy_area": "Oncology", "is_priority_doctor": False},
        
        # Regular Doctors - Neurology
        {"name": "Dr. Deepak Chopra", "therapy_area": "Neurology", "is_priority_doctor": False},
        {"name": "Dr. Lakshmi Narayan", "therapy_area": "Neurology", "is_priority_doctor": False},
        {"name": "Dr. Prakash Joshi", "therapy_area": "Neurology", "is_priority_doctor": False},
        
        # Regular Doctors - Other Specialties
        {"name": "Dr. Manish Agarwal", "therapy_area": "Diabetology", "is_priority_doctor": False},
        {"name": "Dr. Sneha Kulkarni", "therapy_area": "Diabetology", "is_priority_doctor": False},
        {"name": "Dr. Rajiv Malhotra", "therapy_area": "Endocrinology", "is_priority_doctor": False},
        {"name": "Dr. Anjali Bhatt", "therapy_area": "Endocrinology", "is_priority_doctor": False},
        {"name": "Dr. Gopal Krishnan", "therapy_area": "Nephrology", "is_priority_doctor": False},
        {"name": "Dr. Divya Sharma", "therapy_area": "Nephrology", "is_priority_doctor": False},
        {"name": "Dr. Mohan Das", "therapy_area": "Gastroenterology", "is_priority_doctor": False},
        {"name": "Dr. Priyanka Sen", "therapy_area": "Gastroenterology", "is_priority_doctor": False},
        {"name": "Dr. Thomas Mathew", "therapy_area": "Pulmonology", "is_priority_doctor": False},
        {"name": "Dr. Rebecca D'Souza", "therapy_area": "Pulmonology", "is_priority_doctor": False},
        {"name": "Dr. Joseph Francis", "therapy_area": "Rheumatology", "is_priority_doctor": False},
        {"name": "Dr. Nandini Iyer", "therapy_area": "Rheumatology", "is_priority_doctor": False},
        {"name": "Dr. Harish Rawat", "therapy_area": "Hematology", "is_priority_doctor": False},
        {"name": "Dr. Sangeeta Mishra", "therapy_area": "Hematology", "is_priority_doctor": False},
        {"name": "Dr. Abhishek Tiwari", "therapy_area": "Infectious Disease", "is_priority_doctor": False},
        {"name": "Dr. Ritu Choudhary", "therapy_area": "Infectious Disease", "is_priority_doctor": False},
        {"name": "Dr. Venkatesh Prasad", "therapy_area": "Critical Care", "is_priority_doctor": False},
        {"name": "Dr. Swati Pandey", "therapy_area": "Critical Care", "is_priority_doctor": False},
        {"name": "Dr. Nikhil Bansal", "therapy_area": "Emergency Medicine", "is_priority_doctor": False},
        {"name": "Dr. Tanvi Agarwal", "therapy_area": "Emergency Medicine", "is_priority_doctor": False},
    ]
    
    added_count = 0
    for doc_data in fake_doctors:
        existing = db.query(models.Doctor).filter(models.Doctor.name == doc_data["name"]).first()
        if not existing:
            doctor = models.Doctor(**doc_data)
            db.add(doctor)
            added_count += 1
    
    db.commit()
    return {"message": f"{added_count} doctors seeded successfully", "total": len(fake_doctors)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)