import feedparser
import urllib.parse
from datetime import datetime

def fetch_city_news(city_name):
    """
    Fetches top 3 health/pollution related news for a given city from Google News RSS.
    """
    try:
        # Construct query: "{City} AND (health OR hospital OR pollution OR dengue OR air quality)"
        query = f'{city_name} AND (health OR hospital OR pollution OR dengue OR "air quality")'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        # Parse feed with timeout (handled by socket default usually, but feedparser is robust)
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:3]: # Limit to top 3
            # Format date if possible, else use raw
            published = entry.get('published', '')
            try:
                # Example format: "Tue, 18 Feb 2026 07:00:00 GMT"
                dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z")
                published = dt.strftime("%d %b %Y")
            except:
                pass # Keep original string if parsing fails
                
            news_items.append({
                'title': entry.title,
                'link': entry.link,
                'published': published,
                'source': entry.source.title if 'source' in entry else 'Google News'
            })
            
        return news_items
    except Exception as e:
        print(f"Error fetching news for {city_name}: {e}")
        return []

if __name__ == "__main__":
    # Test run
    city = "Delhi"
    news = fetch_city_news(city)
    print(f"News for {city}:")
    for item in news:
        print(f"- {item['title']} ({item['published']})")
