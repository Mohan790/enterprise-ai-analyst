import requests, os

os.makedirs("data/raw", exist_ok=True)

companies = {
    "Tesla_2023":    "https://en.wikipedia.org/wiki/Tesla,_Inc.",
    "Netflix_2023":  "https://en.wikipedia.org/wiki/Netflix",
    "Meta_2023":     "https://en.wikipedia.org/wiki/Meta_Platforms",
    "Nvidia_2023":   "https://en.wikipedia.org/wiki/Nvidia",
    "Samsung_2023":  "https://en.wikipedia.org/wiki/Samsung",
}

headers = {"User-Agent": "Mozilla/5.0 student@example.com"}

for name, url in companies.items():
    print(f"Downloading {name}...")
    r = requests.get(url, headers=headers)
    print(f"  Size: {len(r.text)} characters")
    with open(f"data/raw/{name}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"  Saved!")

print("All done!")
