import requests
import random
import os
from datetime import datetime, timedelta

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
API_URL = os.getenv("API_URL", "http://shelter-api:8000")

SHELTERS = [
    {"name": "Lakeside Animal Shelter", "city": "Austin", "state": "TX", "capacity": 40},
    {"name": "Maplewood Pet Rescue", "city": "Portland", "state": "OR", "capacity": 35},
    {"name": "Riverside Humane Society", "city": "Denver", "state": "CO", "capacity": 50},
    {"name": "Sunnyvale Animal Care", "city": "Phoenix", "state": "AZ", "capacity": 30},
    {"name": "Northbrook Pet Haven", "city": "Nashville", "state": "TN", "capacity": 45},
]

DOG_BREEDS = [
    "Labrador Retriever", "Golden Retriever", "German Shepherd",
    "Beagle", "Bulldog", "Poodle", "Rottweiler", "Boxer",
    "Dachshund", "Shih Tzu", "Siberian Husky", "Border Collie"
]

CAT_BREEDS = [
    "Domestic Shorthair", "Domestic Longhair", "Siamese",
    "Maine Coon", "Persian", "Ragdoll", "Bengal",
    "Scottish Fold", "Sphynx", "American Shorthair"
]

NAMES_DOG = [
    "Buddy", "Max", "Charlie", "Cooper", "Bear", "Duke", "Rocky",
    "Daisy", "Luna", "Bella", "Molly", "Sadie", "Stella", "Rosie"
]

NAMES_CAT = [
    "Whiskers", "Shadow", "Mittens", "Oliver", "Simba", "Leo",
    "Luna", "Nala", "Cleo", "Mochi", "Jasper", "Willow", "Pepper"
]

def generate_description(name, species, breed, age, sex, health_status):
    prompt = (
        f"Write a warm, 2-3 sentence adoption profile for a shelter {species} named {name}. "
        f"They are a {age:.1f} year old {sex} {breed} in {health_status} condition. "
        f"Make it friendly and encouraging to potential adopters. No bullet points, just prose."
    )
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "mistral",
                "messages": [
                    {"role": "system", "content": "You write short, warm animal adoption profiles for a shelter website."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=60
        )
        return response.json()["message"]["content"].strip()
    except Exception as e:
        return f"{name} is a wonderful {breed} looking for a loving home."

def seed_shelters():
    print("Seeding shelters...")
    shelter_ids = []
    for s in SHELTERS:
        response = requests.post(f"{API_URL}/shelters", json=s)
        if response.status_code == 200:
            shelter_ids.append(response.json()["id"])
            print(f"  Created shelter: {s['name']}")
        else:
            print(f"  Failed to create shelter: {s['name']} - {response.text}")
    return shelter_ids

def seed_animals(shelter_ids, animals_per_shelter=8):
    print("Seeding animals...")
    for shelter_id in shelter_ids:
        for _ in range(animals_per_shelter):
            species = random.choice(["dog", "cat"])
            if species == "dog":
                breed = random.choice(DOG_BREEDS)
                name = random.choice(NAMES_DOG)
            else:
                breed = random.choice(CAT_BREEDS)
                name = random.choice(NAMES_CAT)

            age = round(random.uniform(0.5, 12.0), 1)
            sex = random.choice(["male", "female"])
            health_status = random.choices(
                ["healthy", "recovering", "injured"],
                weights=[80, 15, 5]
            )[0]
            intake_date = datetime.utcnow() - timedelta(days=random.randint(1, 90))

            print(f"  Generating description for {name} the {breed}...")
            description = generate_description(name, species, breed, age, sex, health_status)

            animal_data = {
                "shelter_id": shelter_id,
                "name": name,
                "species": species,
                "breed": breed,
                "age_years": age,
                "sex": sex,
                "health_status": health_status,
                "status": "available",
                "intake_date": intake_date.isoformat(),
                "description": description
            }

            response = requests.post(f"{API_URL}/animals", json=animal_data)
            if response.status_code == 200:
                print(f"    Created: {name} ({species})")
            else:
                print(f"    Failed: {name} - {response.text}")
