from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    SUPPLIER = "supplier"
    DEMANDER = "demander"

class CooperationType(enum.Enum):
    IN_PERSON = "in_person"
    PROJECT_BASED = "project_based"
    PART_TIME = "part_time"

class WorkStyle(enum.Enum):
    FASHION = "fashion"
    ADVERTISING = "advertising"
    RELIGIOUS = "religious"
    CHILDREN = "children"
    SPORTS = "sports"
    ARTISTIC = "artistic"
    OUTDOOR = "outdoor"
    STUDIO = "studio"

class RequestStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False)
    demander_profile = relationship("Demander", back_populates="user", uselist=False)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # اطلاعات پایه
    full_name = Column(String(200), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    phone_number = Column(String(20))
    instagram_id = Column(String(100))
    
    # مشخصات ظاهری
    height = Column(Integer)  # cm
    weight = Column(Integer)  # kg
    hair_color = Column(String(50))
    eye_color = Column(String(50))
    skin_color = Column(String(50))
    top_size = Column(Integer)
    bottom_size = Column(Integer)
    special_features = Column(Text)
    
    # اطلاعات همکاری
    pricing_data = Column(JSON)  # Dict containing pricing information for different types
    # Example pricing_data structure:
    # {
    #     "hourly": 250,          # 250 هزار تومان
    #     "daily": 1200,          # 1,200 هزار تومان (1.2M)
    #     "per_cloth": 150,
    #     "category_based": {     # قیمت به ازای سبک
    #         "fashion": 300,
    #         "advertising": 400
    # }
    city = Column(String(100))
    area = Column(String(100))
    cooperation_types = Column(JSON)  # List of types
    work_styles = Column(JSON)  # List of styles
    
    # سابقه و توضیحات
    brand_experience = Column(Text)
    additional_notes = Column(Text)
    
    # عکس‌ها
    portfolio_photos = Column(JSON)  # List of photo URLs
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="supplier_profile")
    requests_received = relationship("Request", back_populates="supplier", foreign_keys="Request.supplier_id")

class Demander(Base):
    __tablename__ = "demanders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # اطلاعات پایه
    full_name = Column(String(200))
    company_name = Column(String(200))
    phone_number = Column(String(20))
    instagram_id = Column(String(100))
    additional_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="demander_profile")
    requests_sent = relationship("Request", back_populates="demander", foreign_keys="Request.demander_id")

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True)
    demander_id = Column(Integer, ForeignKey("demanders.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    message = Column(Text)
    response_message = Column(Text)
    demander_phone = Column(String(20))  # Store demander's phone for easy access
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    demander = relationship("Demander", back_populates="requests_sent")
    supplier = relationship("Supplier", back_populates="requests_received")
