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

def clamp(val):
    """Normalize a value to be strictly between 0 and 100."""
    return max(0, min(100, val))

AFFILIATE_MATRIX = {
    'aqi_risk': {'action': 'Action: Get a True HEPA Air Purifier', 'link': 'https://amzn.to/4aNom9H'},
    'mosquito_risk': {'action': 'Action: Install a UV Mosquito Killer Lamp', 'link': 'https://amzn.to/4rB3t8V'},
    'uv_risk': {'action': 'Action: Upgrade to Premium Dermatologist SPF', 'link': 'https://amzn.to/4s31z0r'},
    'heat_stress': {'action': 'Action: Get a Portable Smart Air Cooler', 'link': 'https://amzn.to/46JCtvF'},
    'dehydration_risk': {'action': 'Action: Invest in a Cold Press Slow Juicer', 'link': 'https://amzn.to/3OvHZM0'},
    'joint_risk': {'action': 'Action: Use a Shiatsu Knee & Leg Massager', 'link': 'https://amzn.to/3ZVFPI1'},
    'migraine_risk': {'action': 'Action: Try a Smart Eye Massager with Heat', 'link': 'https://amzn.to/4rEDJsc'},
    'respiratory_risk': {'action': 'Action: Get a Medical-Grade Humidifier', 'link': 'https://amzn.to/3OwcilH'},
    'pollen_risk': {'action': 'Action: Deploy a HEPA Robot Vacuum', 'link': 'https://amzn.to/4ccHgZV'},
    'skin_risk': {'action': 'Action: Install a Hard Water Shower Filter', 'link': 'https://amzn.to/4aPrKRk'}
}

def get_risk_metadata(score, metric_name):
    """Takes a 0-100 score and returns mapping dict for UI labels & affiliate hooks."""
    score = round(score)
    if score < 33:
        text, color, remedy = "Low", "text-emerald-400", None
    elif score < 66:
        text, color, remedy = "Medium", "text-yellow-400", None
    else:
        text, color = "High", "text-rose-400"
        remedy = AFFILIATE_MATRIX.get(metric_name)

    return {
        'value': score,
        'text': text,
        'color': color,
        'remedy': remedy
    }

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
    india_context['canonical_url'] = 'https://cityhealth360.in/docs/india.html'
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
            
        slug = state_name.lower().replace(" ", "-")
        state_context = {
            'state': state_name,
            'city_count': len(group_df),
            'date': today_date,
            'canonical_url': f'https://cityhealth360.in/docs/{slug}.html',
            **calculate_leaderboards(group_df)
        }
        state_html = state_template.render(state_context)
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

        slug = city_name.lower().replace(" ", "-")
        
        # --- 17-Point Algorithm Calculations ---
        # Raw vars (ensure pollen_level has a default of 0 and fallback for pressure)
        temp = row.get('temp', 25)
        min_temp = row.get('min_temp', temp)
        humidity = row.get('humidity', 50)
        wind = row.get('windspeed', 5) # Open meteo returns windspeed or wind
        uv = row.get('uv_index', 5)
        aqi = row.get('aqi', 50)
        pressure = row.get('pressure', 1013)
        precip = row.get('rain', 0)
        pollen_level = row.get('pollen_level', 0)
        
        # Core Risk Factors
        aqi_risk = clamp((aqi / 300) * 100)
        uv_risk = clamp((uv / 11) * 100)
        hi = temp + (0.33 * humidity) - (0.70 * wind) - 4
        heat_stress = clamp(((hi - 22) / 23) * 100)
        cold_stress = clamp(((18 - temp) / 15) * 100) if temp < 18 else 0
        pollen_risk = clamp((pollen_level / 5) * 100)
        humidity_discomfort = clamp((abs(humidity - 50) / 50) * 100)
        
        # Vector & Pain Metrics
        t_factor = clamp(100 - (abs(temp - 28) * 10))
        rain_boost = 100 if precip > 0 else 0
        mosquito_risk = clamp((0.5 * t_factor) + (0.3 * humidity) + (0.2 * rain_boost))
        
        p_drop = clamp((1013 - pressure) * 4)
        t_cold = clamp((20 - temp) * 2)
        joint_risk = clamp((0.6 * p_drop) + (0.2 * t_cold) + (0.2 * max(0, humidity - 50)))
        
        migraine_risk = clamp((0.5 * p_drop) + (0.3 * heat_stress) + (0.2 * uv_risk))
        
        # Lifestyle & Vulnerability Scores
        workout_disruption = clamp((0.4 * aqi_risk) + (0.3 * heat_stress) + (0.2 * uv_risk) + (0.1 * humidity_discomfort))
        skin_risk = clamp(((abs(humidity - 60) / 40) * 50) + ((abs(temp - 25) / 15) * 50))
        sleep_disruption = clamp((abs(min_temp - 21) * 10) + (aqi_risk * 0.2))
        elderly_risk = clamp((0.5 * aqi_risk) + (0.3 * heat_stress) + (0.2 * cold_stress))
        dehydration_risk = clamp((0.6 * heat_stress) + (0.4 * uv_risk))
        respiratory_risk = clamp((0.5 * aqi_risk) + (0.3 * humidity_discomfort) + (0.2 * cold_stress))
        
        # Master Indices
        composite_risk = clamp((0.20 * aqi_risk) + (0.15 * heat_stress) + (0.15 * mosquito_risk) + (0.10 * uv_risk) + (0.10 * joint_risk) + (0.10 * migraine_risk) + (0.10 * elderly_risk) + (0.10 * pollen_risk))
        city_health_score = clamp(100 - composite_risk)

        context = {
            'city': row.to_dict(),
            'metadata': city_meta,
            'date': today_date,
            'canonical_url': f'https://cityhealth360.in/docs/{slug}.html',
            'image_url': f"https://image.pollinations.ai/prompt/{city_name} city india scenic?width=1600&height=900&nologo=true",
            'news': fetch_city_news(city_name),
            
            # Master Score (Keeps raw number format)
            'city_health_score': round(city_health_score),
            
            # The 15 Sub-Metrics formatted as dicts
            'aqi_risk': get_risk_metadata(aqi_risk, 'aqi_risk'),
            'pollen_risk': get_risk_metadata(pollen_risk, 'pollen_risk'),
            'respiratory_risk': get_risk_metadata(respiratory_risk, 'respiratory_risk'),
            'humidity_discomfort': get_risk_metadata(humidity_discomfort, 'humidity_discomfort'),
            'cold_stress': get_risk_metadata(cold_stress, 'cold_stress'),
            'heat_stress': get_risk_metadata(heat_stress, 'heat_stress'),
            'uv_risk': get_risk_metadata(uv_risk, 'uv_risk'),
            'dehydration_risk': get_risk_metadata(dehydration_risk, 'dehydration_risk'),
            'workout_disruption': get_risk_metadata(workout_disruption, 'workout_disruption'),
            'sleep_disruption': get_risk_metadata(sleep_disruption, 'sleep_disruption'),
            'mosquito_risk': get_risk_metadata(mosquito_risk, 'mosquito_risk'),
            'joint_risk': get_risk_metadata(joint_risk, 'joint_risk'),
            'migraine_risk': get_risk_metadata(migraine_risk, 'migraine_risk'),
            'skin_risk': get_risk_metadata(skin_risk, 'skin_risk'),
            'elderly_risk': get_risk_metadata(elderly_risk, 'elderly_risk')
        }

        output_html = city_template.render(context)
        output_path = os.path.join(DOCS_DIR, f"{slug}.html")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        
        generated_count += 1

    print(f"Successfully generated {generated_count} city pages.")

    # --- Generate Sitemap ---
    base_url = "https://cityhealth360.in"
    urls = [f"{base_url}/"]
    
    for index, row in df.iterrows():
        city_slug = str(row['city']).lower().replace(" ", "-")
        urls.append(f"{base_url}/docs/{city_slug}.html")
        
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url in urls:
        xml_content.append(f"  <url>\n    <loc>{url}</loc>\n  </url>")
        
    xml_content.append('</urlset>')
    
    sitemap_path = os.path.join(DOCS_DIR, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_content))
    print(f"Generated Sitemap: {sitemap_path}")

    # --- 6. Generate 404 Error Page ---
    error_template = env.get_template('404.html')
    error_context = {
        'date': today_date,
        'title': '404 - City Not Found | City Health 360',
        'description': 'The hyper-localized health index you requested is off the radar.'
    }
    error_html = error_template.render(error_context)
    # Output to the root directory for GitHub Pages
    error_output_path = "404.html"
    with open(error_output_path, 'w', encoding='utf-8') as f:
        f.write(error_html)
    print(f"Generated 404 Page: {error_output_path}")

if __name__ == "__main__":
    generate_pages()
