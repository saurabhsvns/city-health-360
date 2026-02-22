# City Health 360 - Environmental Intelligence

A programmatic SEO (pSEO) web ecosystem that dynamically calculates health, weather, and environmental indices for 132 Indian cities. It combines live Open-Meteo feeds with custom logic to determine travel safety, mosquito risks, hair frizz indices, and more.

## Architecture
- **Data Intake:** `fetch_health.py` pulls current forecasts and applies health logic.
- **Site Generation:** `build_site.py` combines CSV data with Jinja2 templates.
- **Frontend Ecosystem:**
  - `docs/index.html` - The National Dashboard (SPA)
  - `docs/india.html` - The Leaflet Map View of India
  - `docs/<state>.html` - SEO State-Level Silos
  - `docs/<city>.html` - 132 detailed City Health Reports

## Quick Start
To regenerate the site data and templates locally:
1. Initialize the Python virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. Refresh Live Environmental Data (optional, limits apply):
   ```bash
   python scripts/fetch_health.py
   ```
3. Generate the Static Site:
   ```bash
   python scripts/build_site.py
   ```
4. Serve the Site locally to view:
   ```bash
   python -m http.server
   # Then visit http://localhost:8000
   ```
   *Note: Because navigation relies on relative paths, always run the server from the root directory.*

## Deployment
This project is pre-configured to be deployed for free on **GitHub Pages**. Simply push this repository to a GitHub `main` branch and configure Pages to serve directly from the Root `/` directory.

## Acknowledgements
Designed with Tailwind CSS and Alpine.js. Built completely static to ensure lightning-fast performance and infinite scale.
