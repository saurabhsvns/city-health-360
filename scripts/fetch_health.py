import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from datetime import datetime
import pytz
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup requests session with retries and custom User-Agent
session = requests.Session()
session.headers.update({"User-Agent": "CityHealth360-Bot/1.0 (saurabh_jss169@yahoo.co.in)"})
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 429, 500, 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))
session.mount('http://', HTTPAdapter(max_retries=retries))


# Constants
CITIES = [
    # Metros & Tier 1
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},

    # North India
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
    {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Srinagar", "lat": 34.0837, "lon": 74.7973},
    {"name": "Jammu", "lat": 32.7266, "lon": 74.8570},
    {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723},
    {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
    {"name": "Jalandhar", "lat": 31.3260, "lon": 75.5762},
    {"name": "Dehradun", "lat": 30.6284, "lon": 78.0322},
    {"name": "Shimla", "lat": 31.1048, "lon": 77.1734},
    {"name": "Manali", "lat": 32.2396, "lon": 77.1887},
    {"name": "Gurgaon", "lat": 28.4595, "lon": 77.0266},
    {"name": "Noida", "lat": 28.5355, "lon": 77.3910},
    {"name": "Ghaziabad", "lat": 28.6692, "lon": 77.4538},
    {"name": "Faridabad", "lat": 28.4089, "lon": 77.3178},
    {"name": "Meerut", "lat": 28.9845, "lon": 77.7064},
    {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
    {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    {"name": "Prayagraj", "lat": 25.4358, "lon": 81.8463}, # Allahabad
    {"name": "Gorakhpur", "lat": 26.7606, "lon": 83.3732},
    {"name": "Bareilly", "lat": 28.3670, "lon": 79.4304},
    {"name": "Aligarh", "lat": 27.8974, "lon": 78.0880},
    {"name": "Moradabad", "lat": 28.8386, "lon": 78.7733},
    {"name": "Saharanpur", "lat": 29.9637, "lon": 77.5460},
    {"name": "Jhansi", "lat": 25.4484, "lon": 78.5685},

    # West India
    {"name": "Surat", "lat": 21.1702, "lon": 72.8311},
    {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812},
    {"name": "Rajkot", "lat": 22.3039, "lon": 70.8022},
    {"name": "Thane", "lat": 19.2183, "lon": 72.9781},
    {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
    {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
    {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433},
    {"name": "Solapur", "lat": 17.6599, "lon": 75.9064},
    {"name": "Kolhapur", "lat": 16.7050, "lon": 74.2433},
    {"name": "Goa", "lat": 15.2993, "lon": 74.1240},
    {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243},
    {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125},
    {"name": "Kota", "lat": 25.2138, "lon": 75.8648},
    {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119},
    {"name": "Ajmer", "lat": 26.4499, "lon": 74.6399},
    {"name": "Gwalior", "lat": 26.2183, "lon": 78.1828},
    {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
    {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
    {"name": "Jabalpur", "lat": 23.1815, "lon": 79.9864},
    {"name": "Ujjain", "lat": 23.1765, "lon": 75.7885},

    # South India
    {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
    {"name": "Guntur", "lat": 16.3067, "lon": 80.4365},
    {"name": "Nellore", "lat": 14.4426, "lon": 79.9865},
    {"name": "Kurnool", "lat": 15.8281, "lon": 78.0373},
    {"name": "Kakinada", "lat": 16.9891, "lon": 82.2475},
    {"name": "Tirupati", "lat": 13.6288, "lon": 79.4192},
    {"name": "Warangal", "lat": 17.9689, "lon": 79.5941},
    {"name": "Nizamabad", "lat": 18.6725, "lon": 78.0941},
    {"name": "Mysore", "lat": 12.2958, "lon": 76.6396},
    {"name": "Mangalore", "lat": 12.9141, "lon": 74.8560},
    {"name": "Hubli-Dharwad", "lat": 15.3647, "lon": 75.1240},
    {"name": "Belgaum", "lat": 15.8497, "lon": 74.4977},
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
    {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
    {"name": "Trichy", "lat": 10.7905, "lon": 78.7047}, # Tiruchirappalli
    {"name": "Salem", "lat": 11.6643, "lon": 78.1460},
    {"name": "Tirunelveli", "lat": 8.7139, "lon": 77.7567},
    {"name": "Vellore", "lat": 12.9165, "lon": 79.1325},
    {"name": "Erode", "lat": 11.3410, "lon": 77.7172},
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366},
    {"name": "Kozhikode", "lat": 11.2588, "lon": 75.7804}, # Calicut
    {"name": "Thrissur", "lat": 10.5276, "lon": 76.2144},
    {"name": "Kannur", "lat": 11.8745, "lon": 75.3704},

    # East & Northeast India
    {"name": "Patna", "lat": 25.5941, "lon": 85.1376},
    {"name": "Gaya", "lat": 24.7914, "lon": 85.0002},
    {"name": "Muzaffarpur", "lat": 26.1209, "lon": 85.3647},
    {"name": "Bhagalpur", "lat": 25.2425, "lon": 87.0117},
    {"name": "Ranchi", "lat": 23.3441, "lon": 85.3096},
    {"name": "Jamshedpur", "lat": 22.8046, "lon": 86.2029},
    {"name": "Dhanbad", "lat": 23.7957, "lon": 86.4304},
    {"name": "Bokaro", "lat": 23.6693, "lon": 86.1511},
    {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
    {"name": "Cuttack", "lat": 20.4625, "lon": 85.8828},
    {"name": "Rourkela", "lat": 22.2604, "lon": 84.8536},
    {"name": "Raipur", "lat": 21.2514, "lon": 81.6296},
    {"name": "Bhilai", "lat": 21.1938, "lon": 81.3509},
    {"name": "Guwahati", "lat": 26.1158, "lon": 91.7086},
    {"name": "Agartala", "lat": 23.8315, "lon": 91.2868},
    {"name": "Shillong", "lat": 25.5788, "lon": 91.8933},
    {"name": "Imphal", "lat": 24.8170, "lon": 93.9368},
    {"name": "Aizawl", "lat": 23.7271, "lon": 92.7176},
    {"name": "Kohima", "lat": 25.6701, "lon": 94.1077},
    {"name": "Gangtok", "lat": 27.3314, "lon": 88.6138},
    {"name": "Siliguri", "lat": 26.7271, "lon": 88.3953},
    {"name": "Durgapur", "lat": 23.5204, "lon": 87.3119},
    {"name": "Asansol", "lat": 23.6739, "lon": 86.9524},
    
    # Others
    {"name": "Pondicherry", "lat": 11.9139, "lon": 79.8145},
    {"name": "Port Blair", "lat": 11.6234, "lon": 92.7265},

    # Additional Cities to reach 100+
    {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642},
    {"name": "Rishikesh", "lat": 30.0869, "lon": 78.2676},
    {"name": "Nainital", "lat": 29.3919, "lon": 79.4542},
    {"name": "Mussoorie", "lat": 30.4599, "lon": 78.0664},
    {"name": "Dharamshala", "lat": 32.2190, "lon": 76.3234},
    {"name": "Dalhousie", "lat": 32.5387, "lon": 75.9710},
    {"name": "Patiala", "lat": 30.3398, "lon": 76.3869},
    {"name": "Bhatinda", "lat": 30.2110, "lon": 74.9455},
    {"name": "Rohtak", "lat": 28.8955, "lon": 76.6066},
    {"name": "Panipat", "lat": 29.3909, "lon": 76.9635},
    {"name": "Mathura", "lat": 27.4924, "lon": 77.6737},
    {"name": "Vrindavan", "lat": 27.5823, "lon": 77.7027},
    {"name": "Ayodhya", "lat": 26.7922, "lon": 82.1998},
    {"name": "Ratlam", "lat": 23.3315, "lon": 75.0367},
    {"name": "Sagar", "lat": 23.8388, "lon": 78.7378},
    {"name": "Satna", "lat": 24.6005, "lon": 80.8322},
    {"name": "Akola", "lat": 20.7002, "lon": 77.0082},
    {"name": "Amravati", "lat": 20.9374, "lon": 77.7796},
    {"name": "Latur", "lat": 18.4088, "lon": 76.5604},
    {"name": "Nanded", "lat": 19.1383, "lon": 77.3091},
    {"name": "Gulbarga", "lat": 17.3297, "lon": 76.8343}, # Kalaburagi
    {"name": "Bidar", "lat": 17.9104, "lon": 77.5199},
    {"name": "Hospet", "lat": 15.2689, "lon": 76.3909},
    {"name": "Tirupur", "lat": 11.1085, "lon": 77.3411},
    {"name": "Alappuzha", "lat": 9.4981, "lon": 76.3388}, # Alleppey
    {"name": "Munnar", "lat": 10.0889, "lon": 77.0595},
    {"name": "Silchar", "lat": 24.8333, "lon": 92.7789},
    {"name": "Dibrugarh", "lat": 27.4728, "lon": 94.9120},
]

CSV_PATH = os.path.join("data", "city_health.csv")
OS_PATH_DATA = "data"

def fetch_weather_bulk(chunk):
    """Fetch weather data for a chunk of cities."""
    lats = ",".join([str(city["lat"]) for city in chunk])
    lons = ",".join([str(city["lon"]) for city in chunk])
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lats,
        "longitude": lons,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "surface_pressure", "dew_point_2m"],
        "daily": ["uv_index_max", "wind_gusts_10m_max"],
        "timezone": "Asia/Kolkata",
        "forecast_days": 1
    }
    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching weather data in bulk: {e}")
        return None

def fetch_aqi_bulk(chunk):
    """Fetch AQI data for a chunk of cities."""
    lats = ",".join([str(city["lat"]) for city in chunk])
    lons = ",".join([str(city["lon"]) for city in chunk])
    
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lats,
        "longitude": lons,
        "current": ["us_aqi", "pm10", "pm2_5"],
        "timezone": "Asia/Kolkata"
    }
    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching AQI data in bulk: {e}")
        return None

def calculate_mosquito_risk(temp, humidity, rain):
    """
    Mosquito Risk (0-10):
    High Risk: Temp 25-30°C AND Humidity > 60% AND Rain > 0mm.
    """
    score = 0
    if 25 <= temp <= 30:
        score += 4
    if humidity > 60:
        score += 3
    if rain > 0:
        score += 3
    return score

def calculate_arthritis_risk(pressure, humidity, temp):
    """
    Arthritis Index (0-10):
    Triggers: Rapid Pressure Drop (<1008 hPa) OR High Humidity (>80%) + Low Temp (<20°C).
    """
    score = 0
    if pressure < 1008:
        score += 5
    if humidity > 80 and temp < 20:
        score += 5
    # Cap at 10
    return min(score, 10)

def calculate_migraine_risk(uv, temp, pressure):
    """
    Migraine Trigger (0-10):
    Triggers: High Glare (UV > 6) OR High Heat (>35°C) OR Low Pressure (<1000 hPa - assuming standard low).
    """
    score = 0
    if uv > 6:
        score += 4
    if temp > 35:
        score += 3
    if pressure < 1000:
        score += 3
    return min(score, 10)

def calculate_frizz_risk(dew_point):
    """
    Frizz Forecast (Binary 0/1):
    Bad Hair Day: Dew Point > 16°C (Tropical/Frizzy) OR Dew Point < 0°C (Static).
    """
    if dew_point > 16 or dew_point < 0:
        return 1
    return 0

def main():
    if not os.path.exists(OS_PATH_DATA):
        os.makedirs(OS_PATH_DATA)
    
    city_data_list = []
    chunk_size = 33

    for i in range(0, len(CITIES), chunk_size):
        chunk = CITIES[i:i + chunk_size]
        logging.info(f"Processing cities chunk {i // chunk_size + 1}...")

        weather_res = fetch_weather_bulk(chunk)
        aqi_res = fetch_aqi_bulk(chunk)

        if not weather_res or not aqi_res:
            logging.warning("Skipping chunk due to data fetch error.")
            continue
        
        # Open-Meteo returns a list of objects if multiple coordinates are passed,
        # or a single object if only 1 coordinate is passed (last chunk could be 1 element under certain conditions)
        if isinstance(weather_res, dict):
             weather_res = [weather_res]
        if isinstance(aqi_res, dict):
             aqi_res = [aqi_res]

        for idx, city in enumerate(chunk):
            name = city["name"]
            lat = city["lat"]
            lon = city["lon"]

            try:
                # Type hints to appease the linter (we guarantee lists above)
                weather: dict = weather_res[idx] # type: ignore
                aqi_data: dict = aqi_res[idx] # type: ignore

                current_weather = weather.get("current", {})
                daily_weather = weather.get("daily", {})
                current_aqi = aqi_data.get("current", {})

                temp = current_weather.get("temperature_2m", 0)
                humidity = current_weather.get("relative_humidity_2m", 0)
                rain = current_weather.get("rain", 0)
                pressure = current_weather.get("surface_pressure", 1013)
                dew_point = current_weather.get("dew_point_2m", 0)
                
                uv_index = 0
                if "uv_index_max" in daily_weather and daily_weather["uv_index_max"]:
                     uv_index = daily_weather["uv_index_max"][0]

                aqi = current_aqi.get("us_aqi", 0)
                pm10 = current_aqi.get("pm10", 0)
                pm2_5 = current_aqi.get("pm2_5", 0)

                wind_gusts = 0
                if "wind_gusts_10m_max" in daily_weather and daily_weather["wind_gusts_10m_max"]:
                     wind_gusts = daily_weather["wind_gusts_10m_max"][0]

                mosquito_risk = calculate_mosquito_risk(temp, humidity, rain)
                arthritis_risk = calculate_arthritis_risk(pressure, humidity, temp)
                migraine_risk = calculate_migraine_risk(uv_index, temp, pressure)
                frizz_risk = calculate_frizz_risk(dew_point)

                city_data_list.append({
                    "city": name,
                    "latitude": lat,
                    "longitude": lon,
                    "temp": temp,
                    "humidity": humidity,
                    "rain": rain,
                    "pressure": pressure,
                    "uv_index": uv_index,
                    "wind_gusts": wind_gusts,
                    "aqi": aqi,
                    "pm10": pm10,
                    "pm2_5": pm2_5,
                    "mosquito_risk": mosquito_risk,
                    "arthritis_risk": arthritis_risk,
                    "migraine_risk": migraine_risk,
                    "frizz_risk": frizz_risk,
                    "updated_at": datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
                })

            except Exception as e:
                logging.error(f"Error processing data for {name}: {e}")
                continue
        
        # Be polite to the API between chunks
        if i + chunk_size < len(CITIES):
            logging.info("Sleeping for 3 seconds before next chunk...")
            time.sleep(3)

    # Create DataFrame and save to CSV
    if city_data_list:
        df = pd.DataFrame(city_data_list)
        df.to_csv(CSV_PATH, index=False)
        logging.info(f"Successfully saved data for {len(city_data_list)} cities to {CSV_PATH}")
    else:
        logging.warning("No data collected.")

if __name__ == "__main__":
    main()
