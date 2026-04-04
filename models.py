from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    therapy_area = Column(String(255), nullable=True)
    is_priority_doctor = Column(Boolean, default=False)
    
    # Relationship
    requests = relationship("Request", back_populates="doctor")

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    requested_by = Column(String(100), nullable=False)
    requested_by_role = Column(String(50), nullable=False)
    therapy_area = Column(String(255), nullable=True)
    objective = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    priority = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    user_classification = Column(String(50), default="potential")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    doctor = relationship("Doctor", back_populates="requests")
    doctor_interactions = relationship("DoctorInteraction", back_populates="request", cascade="all, delete-orphan")
    office_activities = relationship("OfficeActivity", back_populates="request", cascade="all, delete-orphan")

class DoctorInteraction(Base):
    __tablename__ = "doctor_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    doctor_name = Column(String(255), nullable=False)
    visit_date = Column(Date, nullable=False)
    topics_discussed = Column(Text, nullable=True)
    scientific_depth = Column(String(100), nullable=True)
    engagement_quality_interest = Column(String(50), nullable=True)
    engagement_quality_participation = Column(String(50), nullable=True)
    engagement_quality_objection = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    request = relationship("Request", back_populates="doctor_interactions")

class OfficeActivity(Base):
    __tablename__ = "office_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    activity_date = Column(Date, nullable=False)
    activity_category = Column(String(100), nullable=False)
    summary = Column(Text, nullable=True)
    linked_outputs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    request = relationship("Request", back_populates="office_activities")