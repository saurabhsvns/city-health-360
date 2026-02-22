import json
import pandas as pd
import os

# Paths
DATA_DIR = 'data'
CSV_PATH = os.path.join(DATA_DIR, 'city_health.csv')
JSON_PATH = os.path.join(DATA_DIR, 'city_metadata.json')

def expand_metadata():
    # 1. Load existing data
    try:
        df = pd.read_csv(CSV_PATH)
        all_cities = df['city'].unique().tolist()
        
        with open(JSON_PATH, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # 2. Identify missing cities
    missing_cities = [city for city in all_cities if city not in metadata]
    print(f"Found {len(missing_cities)} cities missing metadata.")

    # 3. Generate placeholder data for missing cities
    for city in missing_cities:
        metadata[city] = {
            "description": f"Detailed health and environment report for {city}, India. Famous for its local culture and landmarks.",
            "hospitals": [
                f"District Hospital {city}",
                f"{city} General Hospital",
                "City Medical Centre"
            ],
            "safe_areas": [
                "City Center",
                "Main Market Area",
                "Civil Lines"
            ],
            "green_zones": [
                f"{city} Park",
                "Gandhi Maidan",
                "Nehru Garden"
            ],
            "travel_tip": "Stay hydrated and carry a mask if AQI is high. Check local news for latest updates."
        }
        print(f"Added metadata for: {city}")

    # 4. Save updated metadata
    try:
        with open(JSON_PATH, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"Successfully expanded metadata to {len(metadata)} cities!")
    except Exception as e:
        print(f"Error saving metadata: {e}")

if __name__ == "__main__":
    expand_metadata()
