import pandas as pd
import json
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pytz
from news_fetcher import fetch_city_news

# Configuration
DATA_DIR = 'data'
DOCS_DIR = 'docs'
DOCS_DATA_DIR = os.path.join(DOCS_DIR, 'data')
TEMPLATES_DIR = 'templates'
CSV_PATH = os.path.join(DATA_DIR, 'city_health.csv')
JSON_PATH = os.path.join(DATA_DIR, 'city_metadata.json')

def load_data():
    """Load CSV and JSON data."""
    try:
        df = pd.read_csv(CSV_PATH)
        with open(JSON_PATH, 'r') as f:
            metadata = json.load(f)
        return df, metadata
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None

def calculate_leaderboards(df):
    """Calculates top polluted, safest, and highest mosquito risk cities from a dataframe."""
    return {
        'top_polluted': df.nlargest(5, 'aqi')[['city', 'state', 'aqi']].to_dict(orient='records'),
        'top_safest': df.nsmallest(5, 'aqi')[['city', 'state', 'aqi']].to_dict(orient='records'),
        'top_dengue': df.nlargest(5, 'mosquito_risk')[['city', 'state', 'mosquito_risk']].to_dict(orient='records')
    }

def generate_pages():
    """Generate HTML pages for each city, the national map, and state silos."""
    df, metadata = load_data()
    if df is None or metadata is None:
        return

    # Setup Jinja2 Environment
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    city_template = env.get_template('city.html')
    india_template = env.get_template('india.html')
    state_template = env.get_template('state.html')

    # Ensure output directories exist
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)

    ist = pytz.timezone('Asia/Kolkata')
    today_date = datetime.now(ist).strftime("%b %d, %I:%M %p")

    # --- 1. Export JSON for Maps ---
    # The Leaflet maps will fetch this exact JSON
    json_output_path = os.path.join(DOCS_DATA_DIR, 'latest_scores.json')
    df.to_json(json_output_path, orient='records')
    print(f"Generated Map JSON: {json_output_path}")

    # --- 2. Generate National Dashboard (india.html) ---
    india_context = calculate_leaderboards(df)
    india_context['date'] = today_date
    india_html = india_template.render(india_context)
    india_output_path = os.path.join(DOCS_DIR, "india.html")
    with open(india_output_path, 'w', encoding='utf-8') as f:
        f.write(india_html)
    print(f"Generated: {india_output_path}")

    # --- 3. Generate State Silos (<state>.html) ---
    # Group by state and generate a page for each
    grouped = df.groupby('state')
    state_count = 0
    for state_name, group_df in grouped:
        if state_name == "Unknown":
            continue # Skip unmapped cities if any
            
        state_context = {
            'state': state_name,
            'city_count': len(group_df),
            'date': today_date,
            **calculate_leaderboards(group_df)
        }
        state_html = state_template.render(state_context)
        
        slug = state_name.lower().replace(" ", "-")
        state_output_path = os.path.join(DOCS_DIR, f"{slug}.html")
        with open(state_output_path, 'w', encoding='utf-8') as f:
            f.write(state_html)
        
        state_count += 1
    print(f"Successfully generated {state_count} State Silo pages.")

    # --- 4. Generate Individual City Dashboards ---
    generated_count = 0
    for index, row in df.iterrows():
        city_name = row['city']
        
        # Get metadata or fallback explicitly once
        if city_name in metadata:
            city_meta = metadata[city_name]
        else:
            city_meta = {
                "description": f"Detailed health and environment report for {city_name}, India.",
                "hospitals": ["Local District Hospital", "City General Hospital"], 
                "safe_areas": ["City Center", "Main Market Area"],
                "green_zones": ["Local City Park", "Gandhi Maidan"],
                "travel_tip": "Stay hydrated and check local news for latest safety updates."
            }

        context = {
            'city': row.to_dict(),
            'metadata': city_meta,
            'date': today_date,
            'image_url': f"https://image.pollinations.ai/prompt/{city_name} city india scenic?width=1600&height=900&nologo=true",
            'news': fetch_city_news(city_name),
            'verdict': {
                'is_safe': row['aqi'] <= 200 and row['mosquito_risk'] <= 7 and row['temp'] < 40
            },
            'pack_mask': row['aqi'] > 150,
            'pack_sunscreen': row['uv_index'] > 6,
            'pack_repellent': row['mosquito_risk'] > 5,
            'pack_umbrella': row['rain'] > 0
        }

        output_html = city_template.render(context)
        slug = city_name.lower().replace(" ", "-")
        output_path = os.path.join(DOCS_DIR, f"{slug}.html")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        
        generated_count += 1

    print(f"Successfully generated {generated_count} city pages.")

if __name__ == "__main__":
    generate_pages()
