import pandas as pd
import json
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
import pytz
from news_fetcher import fetch_city_news

# Configuration
DATA_DIR = 'data'
DOCS_DIR = 'docs'
DOCS_DATA_DIR = os.path.join(DOCS_DIR, 'data')
TEMPLATES_DIR = 'templates'
CSV_PATH = os.path.join(DATA_DIR, 'city_health.csv')
JSON_PATH = os.path.join(DATA_DIR, 'city_metadata.json')

# Define Top 20 Cities for SEO Intent Expansion
TOP_20_CITIES = ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'varanasi', 'ghaziabad']

def clamp(val):
    """Normalize a value to be strictly between 0 and 100."""
    return max(0, min(100, val))

AFFILIATE_MATRIX = {
    'aqi_risk': {'action': 'Get a True HEPA Air Purifier', 'link': 'https://amzn.to/4aNom9H'},
    'mosquito_risk': {'action': 'Install a UV Mosquito Killer Lamp', 'link': 'https://amzn.to/4rB3t8V'},
    'uv_risk': {'action': 'Upgrade to Premium Dermatologist SPF', 'link': 'https://amzn.to/4s31z0r'},
    'heat_stress': {'action': 'Get a Portable Smart Air Cooler', 'link': 'https://amzn.to/46JCtvF'},
    'dehydration_risk': {'action': 'Invest in a Cold Press Slow Juicer', 'link': 'https://amzn.to/3OvHZM0'},
    'joint_risk': {'action': 'Use a Shiatsu Knee & Leg Massager', 'link': 'https://amzn.to/3ZVFPI1'},
    'migraine_risk': {'action': 'Try a Smart Eye Massager with Heat', 'link': 'https://amzn.to/4rEDJsc'},
    'respiratory_risk': {'action': 'Get a Medical-Grade Humidifier', 'link': 'https://amzn.to/3OwcilH'},
    'allergen_risk': {'action': 'Deploy a HEPA Robot Vacuum', 'link': 'https://amzn.to/4ccHgZV'},
    'skin_risk': {'action': 'Install a Hard Water Shower Filter', 'link': 'https://amzn.to/4aPrKRk'}
}

def get_risk_metadata(score, metric_name):
    """Takes a 0-100 score and returns mapping dict for UI labels & affiliate hooks."""
    score = round(score)
    remedy = AFFILIATE_MATRIX.get(metric_name)
    
    if score < 33:
        text, color = "Low", "text-emerald-400"
    elif score < 66:
        text, color = "Medium", "text-yellow-400"
    else:
        text, color = "High", "text-rose-400"

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

def extract_daily_max(hourly_time, hourly_aqi):
    """Takes hourly Open-Meteo arrays and returns exactly 15 daily maxs (7 past, today, 7 future)."""
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    
    target_dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(-7, 8)]
    daily_stats = {}
    
    for t_str, aqi in zip(hourly_time, hourly_aqi):
        day = t_str.split("T")[0]
        if aqi is None or day not in target_dates:
            continue
        if day not in daily_stats:
            daily_stats[day] = aqi
        else:
            daily_stats[day] = max(daily_stats[day], aqi)
            
    final_aqis = []
    last_valid = 50 # safe default 
    
    # Fill array and forward-fill any missing days (especially at the end of the forecast)
    for d in target_dates:
        if d in daily_stats:
            last_valid = daily_stats[d]
            final_aqis.append(last_valid)
        else:
            final_aqis.append(last_valid)

    return target_dates, final_aqis

def fetch_with_retries(session, url, params, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            res = session.get(url, params=params, timeout=15)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"API Error on attempt {attempt+1}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return {"error": "Max retries exceeded"}

def fetch_all_aqi_timelines(df):
    """Bulk fetch hourly AQI for 15 days for all cities."""
    print("Fetching 15-day AQI timelines from Open-Meteo...")
    import requests
    import time
    timelines = {}
    chunk_size = 35
    session = requests.Session()
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        lats = ",".join(chunk['latitude'].astype(str))
        lons = ",".join(chunk['longitude'].astype(str))
        cities = chunk['city'].tolist()
        
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {
            "latitude": lats,
            "longitude": lons,
            "hourly": "us_aqi",
            "timezone": "Asia/Kolkata",
            "past_days": 8,
            "forecast_days": 7
        }
        
        try:
            data = fetch_with_retries(session, url, params)
            if isinstance(data, dict):
                if "error" in data:
                    print(f"API Error (AQI): {data}")
                    continue
                data = [data]
                
            for idx, city_data in enumerate(data):
                if 'hourly' in city_data and 'us_aqi' in city_data['hourly']:
                    dates, max_aqis = extract_daily_max(
                        city_data['hourly']['time'],
                        city_data['hourly']['us_aqi']
                    )
                    timelines[cities[idx]] = {"dates": dates, "aqis": max_aqis, "max_temps": [], "min_temps": []}
                    
        except Exception as e:
            print(f"Error fetching AQI timelines chunk: {e}")
        time.sleep(1)

    print("Fetching 15-day Temperature timelines from Open-Meteo...")
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        lats = ",".join(chunk['latitude'].astype(str))
        lons = ",".join(chunk['longitude'].astype(str))
        cities = chunk['city'].tolist()
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lats,
            "longitude": lons,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "Asia/Kolkata",
            "past_days": 8,
            "forecast_days": 7
        }
        
        try:
            data = fetch_with_retries(session, url, params)
            if isinstance(data, dict):
                if "error" in data:
                    print(f"API Error (Temp): {data}")
                    continue
                data = [data]
                
            for idx, city_data in enumerate(data):
                if 'daily' in city_data and 'temperature_2m_max' in city_data['daily']:
                    # Ensure alignment of dates with the AQI array (they should perfectly match)
                    if cities[idx] in timelines:
                        # Sometimes Open-Meteo returns nulls at the end of the forecast if it doesn't go far enough
                        # We need to fill them or fallback to the previous day
                        max_temps = city_data['daily']['temperature_2m_max']
                        min_temps = city_data['daily']['temperature_2m_min']
                        
                        # Forward fill any None values
                        last_max = 25
                        last_min = 20
                        
                        filled_max_temps = []
                        filled_min_temps = []
                        for max_t in max_temps:
                            if max_t is not None:
                                last_max = max_t
                            filled_max_temps.append(last_max)
                            
                        for min_t in min_temps:
                            if min_t is not None:
                                last_min = min_t
                            filled_min_temps.append(last_min)
                            
                        timelines[cities[idx]]["max_temps"] = filled_max_temps
                        timelines[cities[idx]]["min_temps"] = filled_min_temps

        except Exception as e:
            print(f"Error fetching Temp timelines chunk: {e}")
        time.sleep(1)
        
    return timelines

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
    intent_template = env.get_template('intent_base.html')

    # Ensure output directories exist
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)

    ist = pytz.timezone('Asia/Kolkata')
    today_date = datetime.now(ist).strftime("%b %d, %I:%M %p")

    # Fetch 15-day API timelines for Charts
    print("Pre-fetching Chart.js visual data...")
    timelines = fetch_all_aqi_timelines(df)

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
    base_url = "https://cityhealth360.in"
    urls = [f"{base_url}/"]
    
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
        pm10 = row.get('pm10', 0)
        pm10 = float(pm10) if pd.notna(pm10) else 0.0
        pm2_5 = row.get('pm2_5', 0)
        pm2_5 = float(pm2_5) if pd.notna(pm2_5) else 0.0
        wind_gusts = row.get('wind_gusts', 0)
        wind_gusts = float(wind_gusts) if pd.notna(wind_gusts) else 0.0
        
        # Proxy Allergen Calculation
        # PM10 is the primary driver of physical dust allergies in India. Wind acts as a multiplier.
        pm10_base = min((pm10 / 100) * 50, 50) # Cap at 50
        wind_multiplier = min((wind_gusts / 40) * 30, 30) # High winds spread dust (Cap at 30)
        pm25_base = min((pm2_5 / 100) * 20, 20) # General irritation (Cap at 20)
        
        allergen_risk = min(pm10_base + wind_multiplier + pm25_base, 100)
        # Core Risk Factors
        aqi_risk = clamp((aqi / 300) * 100)
        uv_risk = clamp((uv / 11) * 100)
        hi = temp + (0.33 * humidity) - (0.70 * wind) - 4
        heat_stress = clamp(((hi - 22) / 23) * 100)
        cold_stress = clamp(((18 - temp) / 15) * 100) if temp < 18 else 0
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
        composite_risk = clamp((0.20 * aqi_risk) + (0.15 * heat_stress) + (0.15 * mosquito_risk) + (0.10 * uv_risk) + (0.10 * joint_risk) + (0.10 * migraine_risk) + (0.10 * elderly_risk) + (0.10 * allergen_risk))
        city_health_score = clamp(100 - composite_risk)

        # Retrieve Timeline Data
        city_timeline = timelines.get(city_name, {"dates": [], "aqis": [], "max_temps": [], "min_temps": []})
        future_aqis = city_timeline["aqis"][8:] if len(city_timeline["aqis"]) > 8 else []
        show_future_forecast_warning = any(a > 150 for a in future_aqis)

        city_dict = row.to_dict()
        city_dict['slug'] = slug

        context = {
            'city': city_dict,
            'metadata': city_meta,
            'date': today_date,
            'canonical_url': f'https://cityhealth360.in/docs/{slug}.html',
            'image_url': f"https://image.pollinations.ai/prompt/{city_name} city india scenic?width=1600&height=900&nologo=true",
            'news': fetch_city_news(city_name),
            
            # Chart.js Arrays
            'timeline_dates': json.dumps(city_timeline["dates"]),
            'timeline_aqi': json.dumps(city_timeline["aqis"]),
            'timeline_max_temp': json.dumps(city_timeline.get("max_temps", [])),
            'timeline_min_temp': json.dumps(city_timeline.get("min_temps", [])),
            'show_future_forecast_warning': show_future_forecast_warning,
            
            # Master Score (Keeps raw number format)
            'city_health_score': round(city_health_score),
            
            # The 15 Sub-Metrics formatted as dicts
            'aqi_risk': get_risk_metadata(aqi_risk, 'aqi_risk'),
            'allergen_risk': get_risk_metadata(allergen_risk, 'allergen_risk'),
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
            
        # --- 5. Generate 10 SEO Intent Pages (Top 20 Cities Only) ---
        if slug in TOP_20_CITIES:
            # Reusable helper to generate standard format based on topic
            def build_intent_data(slug_suffix, title_prefix, h1_topic, topic_risk_measure, advisory_q, advisory_a, extra_q=None, extra_a=None, extra_info=None):
                faq = [{"q": advisory_q, "a": advisory_a}]
                if extra_q and extra_a:
                    faq.append({"q": extra_q, "a": extra_a})
                    
                return {
                    "intent_slug": f"{slug}-{slug_suffix}",
                    "title": f"{title_prefix} in {city_name} today? | Live Index",
                    "h1": f"{h1_topic} Index in {city_name} Today",
                    "h2_1": f"Current {h1_topic} Risks in {city_name}",
                    "h2_2": f"Health Recommendations & Preventative Gear",
                    "topic_risk_measure": topic_risk_measure,
                    "faq": faq,
                    "extra_info": extra_info
                }

            today_max_temp = temp
            today_min_temp = min_temp
            if len(city_timeline["max_temps"]) > 7:
                today_max_temp = round(city_timeline["max_temps"][7])
            if len(city_timeline["min_temps"]) > 7:
                today_min_temp = round(city_timeline["min_temps"][7])
                
            intents = [
                build_intent_data(
                    "aqi-today", "Is the AQI safe", "Air Quality (AQI)", get_risk_metadata(aqi_risk, 'aqi_risk'),
                    f"Is it safe to go outside in {city_name} with current AQI?", f"The current AQI risk score is {round(aqi_risk)}/100. If above 50, sensitive groups should limit exertion.",
                    f"Do I need an air purifier in {city_name} today?", f"Yes, especially if proper ventilation is lacking and AQI exceeds 100.",
                    extra_info={"label": "Actual Live AQI Level", "value": f"{round(aqi)}"}
                ),
                build_intent_data(
                    "best-time-outside", "When is the best time to go outside", "Safe Outdoor Windows", get_risk_metadata(humidity_discomfort, 'humidity_discomfort'),
                    f"What is the safest time for outdoor activities in {city_name} today?", f"Avoid peak UV and heat hours between 11 AM and 4 PM. Early morning or late evening is optimal.",
                    extra_info={"label": "Today's Temperature Range", "value": f"{today_min_temp}°C - {today_max_temp}°C"}
                ),
                build_intent_data(
                    "kids-safety", "Is it safe for kids to play outside", "Kids Outdoor Safety", get_risk_metadata(aqi_risk, 'aqi_risk'),
                    f"What is the safest time for kids to play outside in {city_name} today?", f"Based on today's forecast, the safest window avoids peak sun and smog, typically before 9 AM or after 5 PM.",
                    f"Should my child wear a mask to school in {city_name} today?", f"With a current AQI risk score of {round(aqi_risk)}, if it is elevated, an N95 mask is highly recommended during their commute."
                ),
                build_intent_data(
                    "allergen-dust-risk", "Live Dust & Allergen Index", "Airborne Dust & Allergen Forecast", get_risk_metadata(allergen_risk, 'allergen_risk'),
                    f"Are allergy levels high in {city_name} today?", f"Based on current PM10 dust levels and wind dispersion, the localized allergen risk score is {round(allergen_risk)}/100.",
                    f"What is causing allergies in {city_name} right now?", f"In {city_name}, primary airborne triggers are coarse particulate matter (PM10) driven by wind gusts of {round(wind_gusts)} km/h, rather than traditional tree pollen."
                ),
                build_intent_data(
                    "heat-stroke-risk", "Is there a heat stroke risk", "Heat Stroke Risk", get_risk_metadata(heat_stress, 'heat_stress'),
                    f"What is the heat stroke risk in {city_name} today?", f"The heat stress score is {round(heat_stress)}/100. Values over 60 signify severe risk to outdoor workers.",
                    extra_info={"label": "Today's Temperature Range", "value": f"{today_min_temp}°C - {today_max_temp}°C"}
                ),
                build_intent_data(
                    "elderly-risk", "Is it safe for the elderly", "Elderly Health Risk", get_risk_metadata(elderly_risk, 'elderly_risk'),
                    f"What precautions should seniors take in {city_name} today?", f"Seniors face a combined risk score of {round(elderly_risk)}/100. Stay indoors in climate-controlled environments if the score is elevated."
                ),
                build_intent_data(
                    "sleep-forecast", "Will I sleep well", "Sleep Disruption Forecast", get_risk_metadata(sleep_disruption, 'sleep_disruption'),
                    f"Why is it hard to sleep in {city_name} tonight?", f"The sleep disruption index is {round(sleep_disruption)}/100, driven by temperature fluctuations and indoor air stagnation."
                ),
                build_intent_data(
                    "skin-hair-impact", "How will weather affect my skin", "Skin & Hair Impact", get_risk_metadata(skin_risk, 'skin_risk'),
                    f"Do I need sunscreen in {city_name} today?", f"The skin risk index stands at {round(skin_risk)}/100. Apply SPF 50+ when UV risk is high.",
                    f"How to protect hair from humidity in {city_name}?", f"Humidity discomfort is {round(humidity_discomfort)}/100. Use anti-frizz serums and avoid prolonged exposure."
                ),
                build_intent_data(
                    "health-ranking", "Is this a healthy city", "City Health Ranking", get_risk_metadata(city_health_score, 'city_health_score'),
                    f"Where does {city_name} rank in health?", f"The master health score is {round(city_health_score)}/100 compared to other Indian metros.",
                    f"How does {city_name} compare to national averages?", f"Review the National Overview dashboard to see live rankings."
                )
            ]
            
            if slug != 'delhi':
                intents.append(build_intent_data(
                    "vs-delhi-air-quality", f"Is {city_name} air quality worse than Delhi", "Comparison vs Delhi", get_risk_metadata(aqi_risk, 'aqi_risk'),
                    f"How does {city_name} AQI compare to Delhi today?", f"{city_name} has a live AQI index risk of {round(aqi_risk)}/100. Delhi historically maintains higher toxicity, but local industrial factors vary."
                ))
            
            for intent in intents:
                intent_context = context.copy()
                intent_context["intent_data"] = intent
                
                # Render and save the intent page
                intent_html = intent_template.render(intent_context)
                intent_output_path = os.path.join(DOCS_DIR, f"{intent['intent_slug']}.html")
                with open(intent_output_path, 'w', encoding='utf-8') as f:
                    f.write(intent_html)
                
                urls.append(f"{base_url}/docs/{intent['intent_slug']}.html")
        
        generated_count += 1

    print(f"Successfully generated {generated_count} city pages (plus 10 unique intent pages for each of the Top 20).")

    # --- Generate Interactive Tools Page ---
    interactive_template = env.get_template('interactive_tools.html')
    interactive_context = {
        'date': today_date,
        'title': 'Interactive Health Diagnostics | City Health 360',
        'description': 'Test your respiratory endurance with the 30-Second Lung Capacity Challenge and scan local environmental threats instantly with the Neighborhood Threat Radar. Maintain environmental health in your city with City Health 360.',
        'canonical_url': f"{base_url}/docs/interactive-tools.html"
    }
    interactive_html = interactive_template.render(interactive_context)
    interactive_out = os.path.join(DOCS_DIR, 'interactive-tools.html')
    with open(interactive_out, 'w', encoding='utf-8') as f:
        f.write(interactive_html)
    urls.append(f"{base_url}/docs/interactive-tools.html")
    print(f"Generated: {interactive_out}")

    # --- Generate Interactive Tools Spoke Pages ---
    spoke_pages = [
        ('reflex-test.html', 'reflex-test.html', 'Heat Fatigue Reflex Test | Check Cognitive Processing Speed', 'Test your cognitive speed against the human average (250ms).'),
        ('lung-capacity.html', 'lung-capacity.html', '30-Second Lung Capacity Test | AQI & Respiratory Health Check', 'Test your baseline respiratory endurance right now.'),
        ('local-radar.html', 'local-radar.html', 'Neighborhood Pollution Radar | Scan Local Industrial Threats', 'Scan your immediate 5km radius for hidden pollution emitters.')
    ]

    for template_name, out_name, title, desc in spoke_pages:
        spoke_template = env.get_template(template_name)
        spoke_context = {
            'date': today_date,
            'title': title,
            'description': desc,
            'canonical_url': f"{base_url}/docs/{out_name}"
        }
        spoke_html = spoke_template.render(spoke_context)
        spoke_out = os.path.join(DOCS_DIR, out_name)
        with open(spoke_out, 'w', encoding='utf-8') as f:
            f.write(spoke_html)
        urls.append(f"{base_url}/docs/{out_name}")
        print(f"Generated: {spoke_out}")

    # --- Generate Sitemap ---
        
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
