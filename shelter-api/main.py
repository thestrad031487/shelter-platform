from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, engine, Base
from models import Shelter, Animal, Event
from datetime import datetime
import uuid

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shelter Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Shelters ---

@app.get("/shelters")
def get_shelters(db: Session = Depends(get_db)):
    return db.query(Shelter).all()

@app.get("/shelters/{shelter_id}")
def get_shelter(shelter_id: str, db: Session = Depends(get_db)):
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    return shelter

@app.post("/shelters")
def create_shelter(data: dict, db: Session = Depends(get_db)):
    shelter = Shelter(**data)
    db.add(shelter)
    db.commit()
    db.refresh(shelter)
    return shelter

# --- Animals ---

@app.get("/animals")
def get_animals(shelter_id: str = None, status: str = None, db: Session = Depends(get_db)):
    query = db.query(Animal)
    if shelter_id:
        query = query.filter(Animal.shelter_id == shelter_id)
    if status:
        query = query.filter(Animal.status == status)
    return query.all()

@app.get("/animals/{animal_id}")
def get_animal(animal_id: str, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal

@app.post("/animals")
def create_animal(data: dict, db: Session = Depends(get_db)):
    animal = Animal(**data)
    db.add(animal)
    db.commit()
    db.refresh(animal)
    shelter = db.query(Shelter).filter(Shelter.id == animal.shelter_id).first()
    if shelter:
        shelter.current_count += 1
        db.commit()
    return animal

@app.patch("/animals/{animal_id}")
def update_animal(animal_id: str, data: dict, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    old_status = animal.status
    for key, value in data.items():
        setattr(animal, key, value)
    if data.get("status") == "adopted" and old_status != "adopted":
        animal.adopted_date = datetime.utcnow()
        shelter = db.query(Shelter).filter(Shelter.id == animal.shelter_id).first()
        if shelter:
            shelter.current_count = max(0, shelter.current_count - 1)
    db.commit()
    db.refresh(animal)
    return animal

# --- Events ---

@app.get("/events")
def get_events(shelter_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Event)
    if shelter_id:
        query = query.filter(Event.shelter_id == shelter_id)
    return query.order_by(Event.timestamp.desc()).limit(50).all()

@app.post("/events")
def create_event(data: dict, db: Session = Depends(get_db)):
    event = Event(**data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# --- Metrics ---

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_animals = db.query(Animal).count()
    adopted = db.query(Animal).filter(Animal.status == "adopted").count()
    available = db.query(Animal).filter(Animal.status == "available").count()
    pending = db.query(Animal).filter(Animal.status == "pending").count()
    shelters = db.query(Shelter).all()
    adoption_rate = round((adopted / total_animals * 100), 1) if total_animals > 0 else 0
    capacity_utilization = []
    for s in shelters:
        capacity_utilization.append({
            "shelter": s.name,
            "current": s.current_count,
            "capacity": s.capacity,
            "utilization": round((s.current_count / s.capacity * 100), 1) if s.capacity > 0 else 0
        })
    return {
        "total_animals": total_animals,
        "adopted": adopted,
        "available": available,
        "pending": pending,
        "adoption_rate": adoption_rate,
        "capacity_utilization": capacity_utilization
    }

@app.get("/health")
def health():
    return {"status": "ok"}
