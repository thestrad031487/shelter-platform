import sys
from agents.generator import seed_shelters, seed_animals
from agents.updater import run_update
from agents.narrator import run_narrator

def run_generator():
    print("=== Shelter Generator Agent ===")
    shelter_ids = seed_shelters()
    if not shelter_ids:
        print("No shelters created. Exiting.")
        sys.exit(1)
    seed_animals(shelter_ids)
    print("=== Generation complete ===")

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if command == "generate":
        run_generator()
    elif command == "update":
        run_update()
    elif command == "narrate":
        run_narrator()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
