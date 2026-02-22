import pandas as pd
import os

CSV_PATH = os.path.join("data", "city_health.csv")

# Mapping of all 132 cities in our list to their states
CITY_TO_STATE = {
    # Metros & Tier 1
    "Delhi": "Delhi", "Mumbai": "Maharashtra", "Bangalore": "Karnataka", "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu", "Kolkata": "West Bengal", "Pune": "Maharashtra", "Ahmedabad": "Gujarat",
    # North India
    "Jaipur": "Rajasthan", "Lucknow": "Uttar Pradesh", "Kanpur": "Uttar Pradesh", "Chandigarh": "Chandigarh",
    "Srinagar": "Jammu and Kashmir", "Jammu": "Jammu and Kashmir", "Amritsar": "Punjab", "Ludhiana": "Punjab",
    "Jalandhar": "Punjab", "Dehradun": "Uttarakhand", "Shimla": "Himachal Pradesh", "Manali": "Himachal Pradesh",
    "Gurgaon": "Haryana", "Noida": "Uttar Pradesh", "Ghaziabad": "Uttar Pradesh", "Faridabad": "Haryana",
    "Meerut": "Uttar Pradesh", "Agra": "Uttar Pradesh", "Varanasi": "Uttar Pradesh", "Prayagraj": "Uttar Pradesh",
    "Gorakhpur": "Uttar Pradesh", "Bareilly": "Uttar Pradesh", "Aligarh": "Uttar Pradesh", "Moradabad": "Uttar Pradesh",
    "Saharanpur": "Uttar Pradesh", "Jhansi": "Uttar Pradesh",
    # West India
    "Surat": "Gujarat", "Vadodara": "Gujarat", "Rajkot": "Gujarat", "Thane": "Maharashtra",
    "Nagpur": "Maharashtra", "Nashik": "Maharashtra", "Aurangabad": "Maharashtra", "Solapur": "Maharashtra",
    "Kolhapur": "Maharashtra", "Goa": "Goa", "Jodhpur": "Rajasthan", "Udaipur": "Rajasthan",
    "Kota": "Rajasthan", "Bikaner": "Rajasthan", "Ajmer": "Rajasthan", "Gwalior": "Madhya Pradesh",
    "Indore": "Madhya Pradesh", "Bhopal": "Madhya Pradesh", "Jabalpur": "Madhya Pradesh", "Ujjain": "Madhya Pradesh",
    # South India
    "Visakhapatnam": "Andhra Pradesh", "Vijayawada": "Andhra Pradesh", "Guntur": "Andhra Pradesh", "Nellore": "Andhra Pradesh",
    "Kurnool": "Andhra Pradesh", "Kakinada": "Andhra Pradesh", "Tirupati": "Andhra Pradesh", "Warangal": "Telangana",
    "Nizamabad": "Telangana", "Mysore": "Karnataka", "Mangalore": "Karnataka", "Hubli-Dharwad": "Karnataka",
    "Belgaum": "Karnataka", "Coimbatore": "Tamil Nadu", "Madurai": "Tamil Nadu", "Trichy": "Tamil Nadu",
    "Salem": "Tamil Nadu", "Tirunelveli": "Tamil Nadu", "Vellore": "Tamil Nadu", "Erode": "Tamil Nadu",
    "Kochi": "Kerala", "Thiruvananthapuram": "Kerala", "Kozhikode": "Kerala", "Thrissur": "Kerala",
    "Kannur": "Kerala",
    # East & Northeast India
    "Patna": "Bihar", "Gaya": "Bihar", "Muzaffarpur": "Bihar", "Bhagalpur": "Bihar",
    "Ranchi": "Jharkhand", "Jamshedpur": "Jharkhand", "Dhanbad": "Jharkhand", "Bokaro": "Jharkhand",
    "Bhubaneswar": "Odisha", "Cuttack": "Odisha", "Rourkela": "Odisha", "Raipur": "Chhattisgarh",
    "Bhilai": "Chhattisgarh", "Guwahati": "Assam", "Agartala": "Tripura", "Shillong": "Meghalaya",
    "Imphal": "Manipur", "Aizawl": "Mizoram", "Kohima": "Nagaland", "Gangtok": "Sikkim",
    "Siliguri": "West Bengal", "Durgapur": "West Bengal", "Asansol": "West Bengal",
    # Others
    "Pondicherry": "Puducherry", "Port Blair": "Andaman and Nicobar Islands",
    "Haridwar": "Uttarakhand", "Rishikesh": "Uttarakhand", "Nainital": "Uttarakhand", "Mussoorie": "Uttarakhand",
    "Dharamshala": "Himachal Pradesh", "Dalhousie": "Himachal Pradesh", "Patiala": "Punjab", "Bhatinda": "Punjab",
    "Rohtak": "Haryana", "Panipat": "Haryana", "Mathura": "Uttar Pradesh", "Vrindavan": "Uttar Pradesh",
    "Ayodhya": "Uttar Pradesh", "Ratlam": "Madhya Pradesh", "Sagar": "Madhya Pradesh", "Satna": "Madhya Pradesh",
    "Akola": "Maharashtra", "Amravati": "Maharashtra", "Latur": "Maharashtra", "Nanded": "Maharashtra",
    "Gulbarga": "Karnataka", "Bidar": "Karnataka", "Hospet": "Karnataka", "Tirupur": "Tamil Nadu",
    "Alappuzha": "Kerala", "Munnar": "Kerala", "Silchar": "Assam", "Dibrugarh": "Assam"
}

def inject_states():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    df = pd.read_csv(CSV_PATH)
    
    # Check if state column already exists to avoid duplication
    if 'state' not in df.columns:
        df['state'] = df['city'].apply(lambda x: CITY_TO_STATE.get(x, "Unknown"))
        
        # Move 'state' to be right after 'city' (which is usually the 0th index)
        cols = list(df.columns)
        if 'city' in cols and 'state' in cols:
             # remove state from current position
             cols.remove('state')
             # insert it after city
             city_index = cols.index('city')
             cols.insert(city_index + 1, 'state')
             df = df[cols]
             
        df.to_csv(CSV_PATH, index=False)
        print(f"Successfully injected state data for {len(df)} rows.")
    else:
        print("'state' column already exists.")

if __name__ == "__main__":
    inject_states()
