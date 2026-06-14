import sqlite3, os

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/financials.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS financials (
    id INTEGER PRIMARY KEY,
    company TEXT,
    year INTEGER,
    revenue_billion REAL,
    net_income_billion REAL,
    eps REAL
)
""")

conn.executemany("INSERT INTO financials VALUES (?,?,?,?,?,?)", [
    (1,  "Apple",     2023, 383.3, 97.0,  6.13),
    (2,  "Microsoft", 2023, 211.9, 72.4,  9.72),
    (3,  "Google",    2023, 307.4, 73.8,  5.80),
    (4,  "Amazon",    2023, 574.8, 30.4,  2.90),
    (5,  "Tesla",     2023, 96.8,  15.0,  3.53),
    (6,  "Meta",      2023, 134.9, 39.1,  14.87),
    (7,  "Nvidia",    2023, 60.9,  29.8,  11.93),
    (8,  "Samsung",   2023, 200.7, 13.1,  1.76),
    (9,  "Netflix",   2023, 33.7,  5.4,   12.03),
])

conn.commit()
conn.close()
print("Database created!")
print("Companies:", ["Apple","Microsoft","Google","Amazon","Tesla","Meta","Nvidia","Samsung","Netflix"])
