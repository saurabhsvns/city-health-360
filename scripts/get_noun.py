import urllib.request
import base64

url = "https://static.thenounproject.com/png/cloudy-night-icon-1695453-512.png"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    data = urllib.request.urlopen(req).read()
    b64 = base64.b64encode(data).decode('utf-8')
    print("SIZE:", len(b64))
    if len(b64) < 50000:
        with open("b64_icon.txt", "w") as f:
            f.write(b64)
        print("Written to b64_icon.txt")
except Exception as e:
    print(e)
