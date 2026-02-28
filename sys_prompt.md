# OVERVIEW: PROGRAMMATIC SEO "INTENT PAGES" ARCHITECTURE
Act as a Senior Python Developer and Technical SEO Expert. We are expanding our static site generator (`cityhealth360.in`) to create highly targeted, long-tail SEO "Intent Pages". 

To protect our crawl budget and avoid "thin content" penalties, we will ONLY generate these intent pages for our Top 20 major cities. 

# THE 10 INTENT TYPES:
1. AQI Today (`{slug}-aqi-today.html`)
2. Best Time to Go Outside (`{slug}-best-time-outside.html`)
3. Kids Safety Today (`{slug}-kids-safety.html`)
4. Pollen Today (`{slug}-pollen-today.html`)
5. Heat Stroke Risk (`{slug}-heat-stroke-risk.html`)
6. Elderly Risk (`{slug}-elderly-risk.html`)
7. Sleep Forecast (`{slug}-sleep-forecast.html`)
8. Skin & Hair Impact (`{slug}-skin-hair-impact.html`)
9. Ranking Page (`{slug}-health-ranking.html`)
10. City Comparison (e.g., `{slug}-vs-delhi-air-quality.html`)

# DESIGN REQUIREMENTS FOR EVERY INTENT PAGE:
✅ 400+ words minimum (mixing static boilerplate with dynamic data)
✅ Primary keyword in `<title>` and `<h1>`
✅ Secondary keywords in `<h2>`
✅ JSON-LD FAQ Schema dynamically injected
✅ Internal links to: City dashboard, Ranking page, and Related metrics
✅ Clear "Last updated" timestamp
✅ Actionable advice (Resident vs. Traveler specific)
✅ Affiliate links integrated into the advice

---

# STEP 1: PYTHON ROUTING & DATA INJECTION (`scripts/build_site.py`)

1. Define the target list at the top of the file:
`TOP_20_CITIES = ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'varanasi', 'ghaziabad']`

2. Inside your main city loop, after generating the master `city.html`, check if the city is in `TOP_20_CITIES`.
3. If true, generate a dynamic SEO dictionary for each of the 10 intents. Example for "Kids Safety":
```python
intent_data = {
    "intent_slug": f"{city['slug']}-kids-safety",
    "title": f"Is it safe for kids to play outside in {city['name']} today? | Live Index",
    "h1": f"Kids Outdoor Safety & Health Index in {city['name']} Today",
    "h2_1": f"Current Air Quality & Weather Risks for Children in {city['name']}",
    "h2_2": f"Pediatric Health Recommendations & Preventative Gear",
    "faq": [
        {"q": f"What is the safest time for kids to play outside in {city['name']} today?", "a": f"Based on today's AQI and UV forecast, the safest window is between 4 PM and 6 PM when the heat stress drops below 30%."},
        {"q": f"Should my child wear a mask to school in {city['name']} today?", "a": f"With a current AQI risk score of {aqi_risk}, it is highly recommended that children wear an N95 mask during their commute."}
    ]
}
# Render `intent_base.html` passing `intent_data`, `city`, and the 17 metrics.

STEP 2: BUILD THE MASTER TEMPLATE (templates/intent_base.html)
Create a new Jinja2 template that satisfies all SEO requirements.

{% extends "layout.html" %}
{% block head %}
<script type="application/ld+json">
{
  "@context": "[https://schema.org](https://schema.org)",
  "@type": "FAQPage",
  "mainEntity": [
    {% for item in intent_data.faq %}
    {
      "@type": "Question",
      "name": "{{ item.q }}",
      "acceptedAnswer": { "@type": "Answer", "text": "{{ item.a }}" }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
</script>
<title>{{ intent_data.title }}</title>
{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto px-4 py-8">
  <div class="text-sm text-gray-400 mb-4">
    <a href="/" class="hover:text-blue-400">Home</a> > 
    <a href="/{{ city.slug }}.html" class="hover:text-blue-400">{{ city.name }} Dashboard</a> > 
    <span class="text-gray-200">{{ intent_data.h1 }}</span>
  </div>
  <p class="text-xs text-green-400 mb-6 font-mono">⏱️ Last Updated: {{ current_timestamp }} | Live Data</p>

  <article class="prose prose-invert max-w-none">
    <h1 class="text-3xl font-bold text-white mb-4">{{ intent_data.h1 }}</h1>
    
    <p class="leading-relaxed text-gray-300">
      Residents and travelers in <b>{{ city.name }}</b> must navigate rapidly changing environmental conditions. Today's proprietary City Health Score for {{ city.name }} is <b>{{ city_health_score }}/100</b>. This comprehensive report translates raw meteorological data—including a current AQI Risk of {{ aqi_risk }}, a Heat Stress level of {{ heat_stress }}, and a Mosquito Risk score of {{ mosquito_risk }}—into actionable safety guidelines. Because environmental threats vary drastically by the hour, relying on a standard weather forecast is no longer sufficient for preventative health.
    </p>

    <h2 class="text-2xl font-bold text-white mt-8 mb-4">{{ intent_data.h2_1 }}</h2>
    <p class="leading-relaxed text-gray-300">
      When evaluating the current outdoor conditions in {{ city.name }}, our algorithm analyzes 17 multi-variable threats. For example, the current UV Risk is marked at <b>{{ uv_risk }}</b>. Prolonged exposure without adequate protection in this region can trigger dermatological issues and severe dehydration. Furthermore, the localized Humidity Discomfort sits at <b>{{ humidity_discomfort }}</b>, which directly correlates with the physical strain index for outdoor workers, athletes, and the elderly. Tracking these specific metrics allows you to find the optimal windows for outdoor activity.
    </p>

    <h2 class="text-2xl font-bold text-white mt-8 mb-4">{{ intent_data.h2_2 }}</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
      <div class="bg-gray-800 p-5 rounded-lg border border-gray-700">
        <h3 class="font-bold text-blue-400 mb-2">🏠 Local Resident Action</h3>
        <p class="text-sm text-gray-300 mb-4">Based on today's {{ city.name }} metrics, immediate home mitigation is advised. Seal environments against particulate matter.</p>
        <a href="[https://amzn.to/YOUR_LINK](https://amzn.to/YOUR_LINK)" target="_blank" class="block text-center bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded">Shop High-Efficiency Purifiers ↗</a>
      </div>
      <div class="bg-gray-800 p-5 rounded-lg border border-gray-700">
        <h3 class="font-bold text-orange-400 mb-2">✈️ Traveler Packing Alert</h3>
        <p class="text-sm text-gray-300 mb-4">If you are arriving in {{ city.name }} today, do not land without adequate preventative gear in your carry-on.</p>
        <a href="[https://amzn.to/YOUR_LINK](https://amzn.to/YOUR_LINK)" target="_blank" class="block text-center bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 rounded">Pack N95 Travel Masks ↗</a>
      </div>
    </div>

    <h2 class="text-2xl font-bold text-white mt-8 mb-4">Frequently Asked Questions</h2>
    <div class="space-y-4">
      {% for item in intent_data.faq %}
      <div class="bg-gray-900 p-4 rounded-lg border border-gray-800">
        <h3 class="font-bold text-gray-100 mb-2">{{ item.q }}</h3>
        <p class="text-gray-400 text-sm">{{ item.a }}</p>
      </div>
      {% endfor %}
    </div>
  </article>

  <div class="border-t border-gray-700 pt-8 mt-10">
    <h3 class="text-lg font-bold text-white mb-4">Explore More {{ city.name }} Health Intelligence</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      <a href="/{{ city.slug }}.html" class="text-sm text-blue-400 hover:underline">⬅️ Main {{ city.name }} Dashboard</a>
      <a href="/india.html" class="text-sm text-blue-400 hover:underline">🏆 National City Rankings</a>
      <a href="/{{ city.slug }}-aqi-today.html" class="text-sm text-blue-400 hover:underline">💨 {{ city.name }} Live AQI</a>
      <a href="/{{ city.slug }}-best-time-outside.html" class="text-sm text-blue-400 hover:underline">⏱️ Safe Outdoor Windows</a>
    </div>
  </div>
</div>
{% endblock %}

STEP 3: UPDATE THE MASTER DASHBOARD (templates/city.html)

{% if city.slug in ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'varanasi', 'ghaziabad'] %}
<div class="mt-10 pt-8 border-t border-gray-700">
  <h2 class="text-xl font-bold text-white mb-4">🔍 Deep Dive Reports for {{ city.name }}</h2>
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
    <a href="/{{ city.slug }}-aqi-today.html" class="text-sm text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 p-3 rounded-lg border border-gray-700 text-center transition">Live AQI Radar</a>
    <a href="/{{ city.slug }}-kids-safety.html" class="text-sm text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 p-3 rounded-lg border border-gray-700 text-center transition">Kids Safety Index</a>
    <a href="/{{ city.slug }}-best-time-outside.html" class="text-sm text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 p-3 rounded-lg border border-gray-700 text-center transition">Safe Outdoor Windows</a>
    <a href="/{{ city.slug }}-elderly-risk.html" class="text-sm text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 p-3 rounded-lg border border-gray-700 text-center transition">Elderly Risk</a>
    <a href="/{{ city.slug }}-sleep-forecast.html" class="text-sm text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 p-3 rounded-lg border border-gray-700 text-center transition">Sleep Forecast</a>
  </div>
</div>
{% endif %}