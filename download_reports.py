import requests, os

os.makedirs("data/raw", exist_ok=True)

reports = {
    "Apple_2023":     "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
    "Tesla_2023":     "https://www.sec.gov/Archives/edgar/data/1318605/000095017023016685/tsla-20231231.htm",
    "Microsoft_2023": "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm",
    "Amazon_2023":    "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn-20231231.htm",
    "Google_2023":    "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm",
}

headers = {"User-Agent": "student-project youremail@example.com"}

for name, url in reports.items():
    print(f"Downloading {name}...")
    r = requests.get(url, headers=headers)
    with open(f"data/raw/{name}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"  Saved {name}.html")

print("All done!")

from langchain_community.document_loaders import BSHTMLLoader
loader = BSHTMLLoader("data/raw/Apple_2023.html")