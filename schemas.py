from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# Doctor Schemas
class DoctorBase(BaseModel):
    name: str
    therapy_area: Optional[str] = None
    is_priority_doctor: bool = False

class DoctorCreate(DoctorBase):
    pass

class Doctor(DoctorBase):
    id: int
    
    class Config:
        from_attributes = True

# Doctor Interaction Schemas
class DoctorInteractionBase(BaseModel):
    doctor_name: str
    visit_date: date
    topics_discussed: Optional[str] = None
    scientific_depth: Optional[str] = None
    engagement_quality_interest: Optional[str] = None
    engagement_quality_participation: Optional[str] = None
    engagement_quality_objection: Optional[str] = None
    summary: Optional[str] = None

class DoctorInteractionCreate(DoctorInteractionBase):
    request_id: int

class DoctorInteraction(DoctorInteractionBase):
    id: int
    request_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Office Activity Schemas
class OfficeActivityBase(BaseModel):
    activity_date: date
    activity_category: str
    summary: Optional[str] = None
    linked_outputs: Optional[str] = None

class OfficeActivityCreate(OfficeActivityBase):
    request_id: int

class OfficeActivity(OfficeActivityBase):
    id: int
    request_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Request Schemas
class RequestBase(BaseModel):
    doctor_id: int
    therapy_area: Optional[str] = None
    objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    user_classification: Optional[str] = "potential"

class RequestCreate(RequestBase):
    requested_by: str
    requested_by_role: str

class Request(RequestBase):
    id: int
    requested_by: str
    requested_by_role: str
    created_at: datetime
    doctor: Optional[Doctor] = None
    doctor_interactions: List[DoctorInteraction] = []
    office_activities: List[OfficeActivity] = []
    
    class Config:
        from_attributes = True

class RequestSummary(BaseModel):
    id: int
    doctor_id: int
    requested_by: str
    requested_by_role: str
    therapy_area: Optional[str] = None
    objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: Optional[str] = None
    user_classification: str
    created_at: datetime
    doctor_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Login Schemas
class LoginRequest(BaseModel):
    username: str
    password: str
    role: str
    empid: str

class LoginResponse(BaseModel):
    username: str
    password: str
    role: str
    empid: str
    message: str

# Activity Log Response
class ActivityLog(BaseModel):
    id: int
    type: str  # "doctor_interaction" or "office_activity"
    date: date
    title: str
    details: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True