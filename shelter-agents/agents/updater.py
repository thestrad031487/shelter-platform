import requests
import random
import os
from datetime import datetime
from agents.generator import (
    DOG_BREEDS, CAT_BREEDS, NAMES_DOG, NAMES_CAT, generate_description
)

API_URL = os.getenv("API_URL", "http://shelter-api:8000")

def get_available_animals():
    response = requests.get(f"{API_URL}/animals?status=available")
    return response.json() if response.status_code == 200 else []

def get_shelters():
    response = requests.get(f"{API_URL}/shelters")
    return response.json() if response.status_code == 200 else []

def process_adoptions():
    animals = get_available_animals()
    if not animals:
        print("  No available animals to adopt.")
        return 0

    count = max(1, int(len(animals) * 0.1))
    selected = random.sample(animals, min(count, len(animals)))
    adopted = 0

    for animal in selected:
        response = requests.patch(
            f"{API_URL}/animals/{animal['id']}",
            json={"status": "adopted"}
        )
        if response.status_code == 200:
            requests.post(f"{API_URL}/events", json={
                "animal_id": animal["id"],
                "shelter_id": animal["shelter_id"],
                "event_type": "adopted",
                "notes": f"{animal['name']} was adopted."
            })
            print(f"  Adopted: {animal['name']} ({animal['breed']})")
            adopted += 1

    return adopted

def process_intakes(shelter_ids):
    count = random.randint(1, 3)
    added = 0

    for _ in range(count):
        shelter_id = random.choice(shelter_ids)
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

        print(f"  Generating description for new intake: {name} the {breed}...")
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
            "intake_date": datetime.utcnow().isoformat(),
            "description": description
        }

        response = requests.post(f"{API_URL}/animals", json=animal_data)
        if response.status_code == 200:
            created = response.json()
            animal_id = created.get("id")
            if animal_id:
                requests.post(f"{API_URL}/events", json={
                    "animal_id": animal_id,
                    "shelter_id": shelter_id,
                    "event_type": "intake",
                    "notes": f"{name} arrived at the shelter."
                })
            print(f"  Intake: {name} ({species}, {breed})")
            added += 1
        else:
            print(f"  Failed intake: {name} - {response.text}")

    return added

def run_update():
    print("=== Updater Agent ===")
    shelters = get_shelters()
    if not shelters:
        print("No shelters found. Run generator first.")
        return

    shelter_ids = [s["id"] for s in shelters]

    print("Processing adoptions...")
    adopted = process_adoptions()

    print("Processing new intakes...")
    added = process_intakes(shelter_ids)

    print(f"=== Update complete: {adopted} adopted, {added} new intakes ===")
