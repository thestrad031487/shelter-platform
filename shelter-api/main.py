from fastapi import FastAPI, Depends, HTTPException
from datetime import timedelta
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

# --- Enhanced Metrics ---

@app.get("/metrics/trends")
def get_trends(db: Session = Depends(get_db)):
    from sqlalchemy import cast, Date, func
    thirty_days = datetime.utcnow() - timedelta(days=30)
    intakes = db.query(
        cast(Event.timestamp, Date).label("date"),
        func.count(Event.id).label("count")
    ).filter(
        Event.event_type == "intake",
        Event.timestamp >= thirty_days
    ).group_by(cast(Event.timestamp, Date)).all()

    adoptions = db.query(
        cast(Event.timestamp, Date).label("date"),
        func.count(Event.id).label("count")
    ).filter(
        Event.event_type == "adopted",
        Event.timestamp >= thirty_days
    ).group_by(cast(Event.timestamp, Date)).all()

    return {
        "intakes": [{"date": str(r.date), "count": r.count} for r in intakes],
        "adoptions": [{"date": str(r.date), "count": r.count} for r in adoptions]
    }

@app.get("/metrics/species")
def get_species(db: Session = Depends(get_db)):
    results = db.query(
        Animal.species,
        Animal.status,
        func.count(Animal.id).label("count")
    ).group_by(Animal.species, Animal.status).all()

    breakdown = {}
    for r in results:
        if r.species not in breakdown:
            breakdown[r.species] = {}
        breakdown[r.species][r.status] = r.count

    return breakdown

@app.get("/metrics/by-shelter")
def get_by_shelter(db: Session = Depends(get_db)):
    shelters = db.query(Shelter).all()
    result = []
    for s in shelters:
        total = db.query(Animal).filter(Animal.shelter_id == s.id).count()
        adopted = db.query(Animal).filter(
            Animal.shelter_id == s.id,
            Animal.status == "adopted"
        ).count()
        available = db.query(Animal).filter(
            Animal.shelter_id == s.id,
            Animal.status == "available"
        ).count()
        rate = round((adopted / total * 100), 1) if total > 0 else 0
        result.append({
            "shelter": s.name,
            "city": s.city,
            "state": s.state,
            "total": total,
            "adopted": adopted,
            "available": available,
            "adoption_rate": rate
        })
    return result

@app.get("/metrics/summary")
def get_summary(db: Session = Depends(get_db)):
    import json, os
    path = "/tmp/shelter_summary.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"summary": None, "generated_at": None}

@app.post("/metrics/summary")
def post_summary(data: dict, db: Session = Depends(get_db)):
    import json
    path = "/tmp/shelter_summary.json"
    payload = {
        "summary": data.get("summary"),
        "generated_at": datetime.utcnow().isoformat()
    }
    with open(path, "w") as f:
        json.dump(payload, f)
    return payload
