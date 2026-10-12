import sqlite3
import math
from datetime import date, datetime, timedelta

DB_PATH = "foodrescue.db"

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor TEXT NOT NULL, food_type TEXT NOT NULL, quantity_kg REAL NOT NULL,
            expiry_date TEXT NOT NULL, city TEXT, lat REAL, lon REAL, notes TEXT,
            status TEXT NOT NULL DEFAULT 'Available', created_at TEXT NOT NULL
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS ngos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, needs TEXT NOT NULL, capacity_kg REAL NOT NULL,
            city TEXT, lat REAL, lon REAL, contact TEXT
        )""")

def add_donation(donor, food_type, quantity, expiry, city, lat, lon, notes):
    with connect() as con:
        con.execute("""INSERT INTO donations
        (donor, food_type, quantity_kg, expiry_date, city, lat, lon, notes, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (donor, food_type, quantity, expiry, city, lat, lon, notes, "Available", datetime.now().isoformat(timespec="seconds")))

def add_ngo(name, needs, capacity, city, lat, lon, contact):
    with connect() as con:
        con.execute("INSERT INTO ngos (name, needs, capacity_kg, city, lat, lon, contact) VALUES (?,?,?,?,?,?,?)",
                    (name, needs, capacity, city, lat, lon, contact))

def list_donations(status=None):
    with connect() as con:
        if status:
            rows = con.execute("SELECT * FROM donations WHERE status=? ORDER BY expiry_date ASC, id DESC", (status,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM donations ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def list_ngos():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM ngos ORDER BY name").fetchall()]

def distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 999.0
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1, math.sqrt(a)))

def match_donations(donation):
    matches = []
    today = date.today()
    try:
        days_left = (date.fromisoformat(donation["expiry_date"]) - today).days
    except Exception:
        days_left = 0
    for ngo in list_ngos():
        needs = [x.strip().lower() for x in ngo["needs"].split(",") if x.strip()]
        accepted = donation["food_type"].lower() in needs or "other" in needs
        if not accepted or ngo["capacity_kg"] <= 0:
            continue
        dist = distance_km(donation.get("lat"), donation.get("lon"), ngo.get("lat"), ngo.get("lon"))
        qty_fit = min(1.0, ngo["capacity_kg"] / max(donation["quantity_kg"], 0.1))
        urgency = 1.0 if days_left <= 0 else (0.85 if days_left == 1 else (0.65 if days_left == 2 else 0.4))
        proximity = max(0.0, 1.0 - min(dist, 100.0)/100.0)
        score = round(100*(0.45*urgency + 0.30*qty_fit + 0.25*proximity))
        reason = f"{'Urgent expiry' if days_left <= 1 else 'Expiry window considered'}; food type accepted; capacity fit {qty_fit*100:.0f}%"
        matches.append({**ngo, "distance_km": dist, "score": score, "reason": reason})
    return sorted(matches, key=lambda x: (-x["score"], x["distance_km"]))

def update_status(donation_id, status):
    with connect() as con:
        con.execute("UPDATE donations SET status=? WHERE id=?", (status, donation_id))

def impact_summary():
    with connect() as con:
        rows = con.execute("SELECT quantity_kg,status FROM donations").fetchall()
    return {
        "donations": len(rows),
        "available_kg": sum(float(r["quantity_kg"]) for r in rows if r["status"] == "Available"),
        "redistributed_kg": sum(float(r["quantity_kg"]) for r in rows if r["status"] == "Redistributed"),
        "open_items": sum(1 for r in rows if r["status"] == "Available")
    }

def seed_demo_data():
    with connect() as con:
        if con.execute("SELECT COUNT(*) FROM donations").fetchone()[0] == 0:
            demo_donations = [
                ("Sunrise Bakery", "Bakery", 12.0, (date.today()+timedelta(days=1)).isoformat(), "Warangal", 17.9689, 79.5941, "Packaged separately"),
                ("Green Basket Market", "Vegetables", 25.0, (date.today()+timedelta(days=2)).isoformat(), "Hanamkonda", 17.9920, 79.5400, "Fresh produce"),
                ("Community Caterer", "Cooked meals", 18.0, (date.today()).isoformat(), "Warangal", 17.9750, 79.6010, "Pickup promptly; check safe holding temperature")
            ]
            for d in demo_donations:
                con.execute("""INSERT INTO donations (donor,food_type,quantity_kg,expiry_date,city,lat,lon,notes,status,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", (*d, "Available", datetime.now().isoformat(timespec="seconds")))
        if con.execute("SELECT COUNT(*) FROM ngos").fetchone()[0] == 0:
            demo_ngos = [
                ("Helping Hands Community Kitchen", "Cooked meals, Vegetables, Bakery", 40.0, "Warangal", 17.9710, 79.5900, "demo-contact@example.org"),
                ("Hope Food Bank", "Bakery, Packaged food, Grains", 100.0, "Hanamkonda", 17.9910, 79.5450, "demo-contact@example.org"),
                ("Annapurna Support Centre", "Vegetables, Fruits, Dairy", 30.0, "Warangal", 17.9620, 79.6100, "demo-contact@example.org")
            ]
            for n in demo_ngos:
                con.execute("INSERT INTO ngos (name,needs,capacity_kg,city,lat,lon,contact) VALUES (?,?,?,?,?,?,?)", n)
