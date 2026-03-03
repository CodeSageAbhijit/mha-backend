"""
SQLAlchemy ORM Models for SQLite
Replaces MongoDB document schemas with relational tables
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, ForeignKey, Table, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database.database import Base
from datetime import datetime
from enum import Enum as PyEnum

# Association tables for many-to-many relationships
patient_psychiatrist_association = Table(
    'patient_psychiatrist_association',
    Base.metadata,
    Column('patient_id', String, ForeignKey('patients.id')),
    Column('psychiatrist_id', String, ForeignKey('psychiatrists.id'))
)

patient_counselor_association = Table(
    'patient_counselor_association',
    Base.metadata,
    Column('patient_id', String, ForeignKey('patients.id')),
    Column('counselor_id', String, ForeignKey('counselors.id'))
)

# User Models
class User(Base):
    """Base User Model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, index=True, nullable=True)  # Index but not unique (legacy data may have duplicates)
    email = Column(String, index=True, nullable=True)     # Index but not unique (legacy data may have duplicates)
    password = Column(String)
    phoneNumber = Column(String)
    firstName = Column(String)
    lastName = Column(String)
    gender = Column(String)
    role = Column(String, index=True)
    termsAccepted = Column(Boolean, default=False)
    isActive = Column(Boolean, default=True)
    profilePhoto = Column(String, nullable=True)
    refreshToken = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lastLogin = Column(DateTime, nullable=True)


class Patient(Base):
    """Patient Model"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    patientId = Column(String, unique=True, index=True)
    dateOfBirth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    addressLine = Column(String, nullable=True)
    maritalStatus = Column(String, nullable=True)
    bloodGroup = Column(String, nullable=True)
    language = Column(Text, nullable=True)  # Stored as JSON text
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postalCode = Column(String, nullable=True)
    disease = Column(String, nullable=True)
    diagnosis = Column(String, nullable=True)
    emergencyContact = Column(String, nullable=True)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctors = relationship("Psychiatrist", secondary=patient_psychiatrist_association, back_populates="patients")
    counselors = relationship("Counselor", secondary=patient_counselor_association, back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    assessments = relationship("Assessment", back_populates="patient")
    chats = relationship("Chat", back_populates="patient")
    todos = relationship("Todo", back_populates="patient")


class Psychiatrist(Base):
    """Psychiatrist Model"""
    __tablename__ = "psychiatrists"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    doctorId = Column(String, unique=True, index=True)
    specialization = Column(String, nullable=True)
    licenseNumber = Column(String, nullable=True)  # Allow duplicates/nulls from legacy data
    experience = Column(Integer)
    qualifications = Column(Text, nullable=True)  # Stored as JSON text
    bio = Column(Text, nullable=True)
    consultationFee = Column(Float, default=0)
    isAvailable = Column(Boolean, default=True)
    hospital = Column(String, nullable=True)
    department = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = relationship("Patient", secondary=patient_psychiatrist_association, back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")
    availability = relationship("PsychiatristAvailability", back_populates="doctor")


class Counselor(Base):
    """Counselor Model"""
    __tablename__ = "counselors"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    counselorId = Column(String, unique=True, index=True)
    specialization = Column(String, nullable=True)
    licenseNumber = Column(String, nullable=True)  # Allow duplicates/nulls from legacy data
    experience = Column(Integer)
    qualifications = Column(Text, nullable=True)  # Stored as JSON text
    bio = Column(Text, nullable=True)
    consultationFee = Column(Float, default=0)
    isAvailable = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = relationship("Patient", secondary=patient_counselor_association, back_populates="counselors")
    appointments = relationship("Appointment", back_populates="counselor")
    availability = relationship("CounselorAvailability", back_populates="counselor")


class Mentor(Base):
    """Mentor Model"""
    __tablename__ = "mentors"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    mentorId = Column(String, unique=True, index=True)
    expertise = Column(JSON, default=list)
    experience = Column(Integer)
    bio = Column(Text, nullable=True)
    consultationFee = Column(Float, default=0)
    isAvailable = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BusinessCoach(Base):
    """Business Coach Model"""
    __tablename__ = "business_coaches"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    coachId = Column(String, unique=True, index=True)
    expertise = Column(JSON, default=list)
    experience = Column(Integer)
    bio = Column(Text, nullable=True)
    consultationFee = Column(Float, default=0)
    isAvailable = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Buddy(Base):
    """Buddy Model"""
    __tablename__ = "buddies"
    
    id = Column(String, primary_key=True)
    userId = Column(String, ForeignKey('users.id'))
    buddyId = Column(String, unique=True, index=True)
    bio = Column(Text, nullable=True)
    interests = Column(JSON, default=list)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Admin(Base):
    """Admin User Model"""
    __tablename__ = "admin"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phoneNumber = Column(String)
    firstName = Column(String)
    lastName = Column(String)
    role = Column(String, default="admin")
    permissions = Column(JSON, default=list)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lastLogin = Column(DateTime, nullable=True)


# Appointment Models
class Appointment(Base):
    """Appointment Model"""
    __tablename__ = "appointments"
    
    id = Column(String, primary_key=True)
    appointmentId = Column(String, unique=True, index=True)
    patientId = Column(String, ForeignKey('patients.id'))
    doctorId = Column(String, ForeignKey('psychiatrists.id'), nullable=True)
    counselorId = Column(String, ForeignKey('counselors.id'), nullable=True)
    appointmentDate = Column(Date)
    appointmentTime = Column(String)
    duration = Column(Integer, default=30)  # minutes
    reason = Column(Text)
    status = Column(String, default="pending")  # pending, confirmed, completed, cancelled
    notes = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Psychiatrist", back_populates="appointments")
    counselor = relationship("Counselor", back_populates="appointments")


class PsychiatristAvailability(Base):
    """Psychiatrist Availability Model"""
    __tablename__ = "psychiatrist_availability"
    
    id = Column(String, primary_key=True)
    doctorId = Column(String, ForeignKey('psychiatrists.id'))
    dayOfWeek = Column(String)  # Monday, Tuesday, etc.
    startTime = Column(String)
    endTime = Column(String)
    isAvailable = Column(Boolean, default=True)
    
    # Relationships
    doctor = relationship("Psychiatrist", back_populates="availability")


class CounselorAvailability(Base):
    """Counselor Availability Model"""
    __tablename__ = "counselor_availability"
    
    id = Column(String, primary_key=True)
    counselorId = Column(String, ForeignKey('counselors.id'))
    dayOfWeek = Column(String)
    startTime = Column(String)
    endTime = Column(String)
    isAvailable = Column(Boolean, default=True)
    
    # Relationships
    counselor = relationship("Counselor", back_populates="availability")


# Assessment Models
class Assessment(Base):
    """Assessment Model"""
    __tablename__ = "assessments"
    
    id = Column(String, primary_key=True)
    assessmentId = Column(String, unique=True, index=True)
    patientId = Column(String, ForeignKey('patients.id'))
    assessmentType = Column(String)  # PHQ-9, GAD-7, etc.
    questions = Column(JSON)
    responses = Column(JSON)
    score = Column(Float)
    result = Column(String)
    severity = Column(String)  # mild, moderate, severe
    recommendations = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="assessments")


# Chat Models
class Chat(Base):
    """Chat Message Model"""
    __tablename__ = "chats"
    
    id = Column(String, primary_key=True)
    chatId = Column(String, unique=True, index=True)
    patientId = Column(String, ForeignKey('patients.id'))
    senderId = Column(String)
    receiverId = Column(String)
    message = Column(Text)
    messageType = Column(String, default="text")  # text, image, file, etc.
    attachmentUrl = Column(String, nullable=True)
    isRead = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="chats")


class Room(Base):
    """Chat Room Model"""
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True)
    roomId = Column(String, unique=True, index=True)
    roomName = Column(String)
    participants = Column(JSON)  # List of user IDs
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# TODO Models
class Todo(Base):
    """TODO Model"""
    __tablename__ = "todos"
    
    id = Column(String, primary_key=True)
    todoId = Column(String, unique=True, index=True)
    userId = Column(String)
    patientId = Column(String, ForeignKey('patients.id'))
    title = Column(String)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium")  # low, medium, high, urgent
    status = Column(String, default="todo")  # todo, in_progress, completed, archived
    dueDate = Column(Date, nullable=True)
    assigneeId = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="todos")


# OTP Models
class OTP(Base):
    """OTP Model for login verification"""
    __tablename__ = "otps"
    
    id = Column(String, primary_key=True)
    username = Column(String, index=True)
    role = Column(String)
    userId = Column(String)
    otp = Column(String)
    email = Column(String)
    isUsed = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    expiresAt = Column(DateTime)


# Payment Models
class Payment(Base):
    """Payment Model"""
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True)
    paymentId = Column(String, unique=True, index=True)
    patientId = Column(String)
    amount = Column(Float)
    currency = Column(String, default="INR")
    status = Column(String, default="pending")  # pending, completed, failed
    paymentMethod = Column(String)  # card, upi, wallet
    transactionId = Column(String, unique=True)
    description = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Call Models
class Call(Base):
    """Call/Meeting Model"""
    __tablename__ = "calls"
    
    id = Column(String, primary_key=True)
    callId = Column(String, unique=True, index=True)
    callerId = Column(String)
    receiverId = Column(String)
    callType = Column(String)  # audio, video
    status = Column(String, default="initiated")  # initiated, ringing, connected, ended
    startTime = Column(DateTime, nullable=True)
    endTime = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Prescription Models
class Prescription(Base):
    """Prescription Model"""
    __tablename__ = "prescriptions"
    
    id = Column(String, primary_key=True)
    prescriptionId = Column(String, unique=True, index=True)
    patientId = Column(String)
    doctorId = Column(String)
    medicines = Column(JSON)  # List of medicines
    dosage = Column(JSON)  # Dosage instructions
    duration = Column(String)
    notes = Column(Text, nullable=True)
    status = Column(String, default="active")
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Review Models
class Review(Base):
    """Review Model"""
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True)
    reviewId = Column(String, unique=True, index=True)
    patientId = Column(String)
    professionalId = Column(String)
    professionalType = Column(String)  # psychiatrist, counselor, mentor
    rating = Column(Integer)  # 1-5
    comment = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)


# Self-Talk Models
class SelfTalk(Base):
    """Self-Talk/Journal Model"""
    __tablename__ = "self_talk"
    
    id = Column(String, primary_key=True)
    talkId = Column(String, unique=True, index=True)
    patientId = Column(String)
    content = Column(Text)
    mood = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    createdAt = Column(DateTime, default=datetime.utcnow)


# Wallet Models
class Wallet(Base):
    """Wallet Model"""
    __tablename__ = "wallet"
    
    id = Column(String, primary_key=True)
    userId = Column(String, unique=True, index=True)
    balance = Column(Float, default=0)
    totalDeposited = Column(Float, default=0)
    totalUsed = Column(Float, default=0)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
