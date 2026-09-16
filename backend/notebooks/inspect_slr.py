import urllib.request
import re

def inspect_slr(slr_num):
    url = f"http://www.openslr.org/resources/{slr_num}/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8')
        links = re.findall(r'href=["\'](http://openslr.magicdatatech.com/[^"\']+)["\']', html)
        if not links:
            links = re.findall(r'href=["\'](http://[^"\']+\.tar\.gz)["\']', html) + re.findall(r'href=["\'](http://[^"\']+\.zip)["\']', html)
        if not links:
            links = re.findall(r'href=["\']([^"\']+)["\']', html)
        print(f"SLR {slr_num} links:")
        for l in links:
            if "tar" in l or "zip" in l or "tgz" in l or "flac" in l or "wav" in l:
                print("  ", l)

inspect_slr(104)
print()
inspect_slr(103)
