# FoodRescue AI — Food Waste Management & Redistribution Agent

A local Streamlit prototype aligned with **SDG 2: Zero Hunger**. It helps record surplus food, store NGO/community-kitchen partners, and rank possible donation matches.

## Requirements
- Windows 10/11
- Python 3.10 or newer (make sure Python is added to PATH)
- Internet connection for first-time package installation

## Run on Windows (Command Prompt)
1. Extract `FoodRescue_AI.zip` to a folder you can find, such as Desktop.
2. Open the extracted `FoodRescue_AI` folder.
3. Click the address bar in File Explorer, type `cmd`, and press Enter.
4. In the Command Prompt window, run:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

5. If Streamlit asks for an email address, press Enter.
6. Open the local URL it prints, usually http://localhost:8501.

## First use
- Click **Load demo data** in the sidebar.
- Visit **Dashboard** to inspect sample offers.
- Visit **Redistribution matches** and choose a donation.
- Use **Add food donation** and **NGO directory** to enter your own data.

## Data storage
A local `foodrescue.db` SQLite database is created automatically in the folder where you run the app. Keep the database file to retain records. Back it up before moving or deleting it.

## What the matching agent does
It filters NGOs by accepted food categories and ranks candidates using expiry urgency (45%), capacity fit (30%), and estimated straight-line distance (25%). It is an explainable heuristic, **not a trained ML model** and not a live route planner.

## Safety and scope
This is a learning/demo prototype. It does not contact NGOs, verify food safety, or arrange pickups. Confirm recipient availability, legal requirements, allergen details, food handling, temperature control, and transport before redistribution. Demo contact details are placeholders.
