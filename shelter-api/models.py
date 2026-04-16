from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    current_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    animals = relationship("Animal", back_populates="shelter")
    events = relationship("Event", back_populates="shelter")

class Animal(Base):
    __tablename__ = "animals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shelter_id = Column(UUID(as_uuid=True), ForeignKey("shelters.id"), nullable=False)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    breed = Column(String, nullable=False)
    age_years = Column(Float, nullable=False)
    sex = Column(String, nullable=False)
    health_status = Column(String, default="healthy")
    status = Column(String, default="available")
    intake_date = Column(DateTime, default=datetime.utcnow)
    adopted_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    shelter = relationship("Shelter", back_populates="animals")
    events = relationship("Event", back_populates="animal")

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    shelter_id = Column(UUID(as_uuid=True), ForeignKey("shelters.id"), nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    animal = relationship("Animal", back_populates="events")
    shelter = relationship("Shelter", back_populates="events")
