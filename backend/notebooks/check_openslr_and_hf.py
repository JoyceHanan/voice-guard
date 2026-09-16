import urllib.request
import json

print("Checking OpenSLR SLR104 (Hindi)...")
try:
    url_hi = "http://www.openslr.org/resources/104/"
    req = urllib.request.Request(url_hi, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        print("OpenSLR 104 accessible! Length:", len(html))
except Exception as e:
    print("OpenSLR 104 error:", e)

print("\nChecking OpenSLR SLR103 (Telugu)...")
try:
    url_te = "http://www.openslr.org/resources/103/"
    req = urllib.request.Request(url_te, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        print("OpenSLR 103 accessible! Length:", len(html))
except Exception as e:
    print("OpenSLR 103 error:", e)
