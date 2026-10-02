import math
import requests
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import FileResponse


#config

THINGSBOARD_URL = "http://54.218.241.153:8080"

USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

LOW_BATTERY_THRESHOLD = 20  # battery percentage


DEVICES = {
    "Teammate 1": "c60b7080-bbb1-11f1-a5fd-d51fed9ef52b",
    "Teammate 2": "6c390ad0-bbad-11f1-a5fd-d51fed9ef52b",
    "My Phone": "41f53430-bba6-11f1-a5fd-d51fed9ef52b",
}


#thingsboard api

def login():
    """Log into ThingsBoard and return an authentication token."""

    url = f"{THINGSBOARD_URL}/api/auth/login"

    response = requests.post(
        url,
        json={
            "username": USERNAME,
            "password": PASSWORD,
        },
    )

    response.raise_for_status()

    return response.json()["token"]


def get_latest_telemetry(token, device_id):
    """Get the latest battery and GPS data for one device."""

    url = (
        f"{THINGSBOARD_URL}/api/plugins/telemetry/"
        f"DEVICE/{device_id}/values/timeseries"
    )

    response = requests.get(
        url,
        headers={
            "X-Authorization": f"Bearer {token}"
        },
        params={
            "keys": "batt,lat,lon"
        },
    )

    response.raise_for_status()

    return response.json()


#data processing

def extract_value(telemetry, key):
    """
    Extract the most recent value and timestamp from a
    ThingsBoard telemetry response.
    """

    values = telemetry.get(key, [])

    if not values:
        return None, None

    latest = values[0]

    return float(latest["value"]), latest["ts"]


def get_phone_data(token):
    """Retrieve and organize telemetry for all phones."""

    phones = {}

    for name, device_id in DEVICES.items():

        telemetry = get_latest_telemetry(token, device_id)

        battery, battery_ts = extract_value(telemetry, "batt")
        latitude, lat_ts = extract_value(telemetry, "lat")
        longitude, lon_ts = extract_value(telemetry, "lon")

        # Use the newest timestamp among the available values.
        timestamps = [
            ts for ts in [battery_ts, lat_ts, lon_ts]
            if ts is not None
        ]

        latest_ts = max(timestamps) if timestamps else None

        phones[name] = {
            "battery": battery,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": latest_ts,
        }

    return phones


#distance calculation

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates
    using the Haversine formula.

    Returns distance in kilometers.
    """

    EARTH_RADIUS_KM = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_KM * c


#telemetry status

def get_age_seconds(timestamp):
    """Return how many seconds old a telemetry timestamp is."""

    if timestamp is None:
        return None

    timestamp_seconds = timestamp / 1000

    now = datetime.now(timezone.utc).timestamp()

    return now - timestamp_seconds


def format_age(timestamp):
    """Create a human-readable telemetry age."""

    age = get_age_seconds(timestamp)

    if age is None:
        return "No data"

    if age < 60:
        return f"{int(age)} seconds ago"

    if age < 3600:
        return f"{int(age / 60)} minutes ago"

    if age < 86400:
        return f"{int(age / 3600)} hours ago"

    return f"{int(age / 86400)} days ago"


def is_live(timestamp):
    """
    Consider telemetry live if it was received within
    the last 60 seconds.
    """

    age = get_age_seconds(timestamp)

    return age is not None and age <= 60


#finding closest phone

def find_closest_teammate(phone_name, phones):
    """
    Find the closest other phone to the specified phone.
    """

    phone = phones[phone_name]

    if phone["latitude"] is None or phone["longitude"] is None:
        return None, None

    closest_name = None
    closest_distance = float("inf")

    for other_name, other_phone in phones.items():

        if other_name == phone_name:
            continue

        if (
            other_phone["latitude"] is None
            or other_phone["longitude"] is None
        ):
            continue

        distance = haversine_distance(
            phone["latitude"],
            phone["longitude"],
            other_phone["latitude"],
            other_phone["longitude"],
        )

        if distance < closest_distance:
            closest_distance = distance
            closest_name = other_name

    if closest_name is None:
        return None, None

    return closest_name, closest_distance


#display

def display_results(phones):

    print()
    print("=" * 60)
    print("              EE542 TEAM PHONE MONITOR")
    print("=" * 60)

    for name, phone in phones.items():

        battery = phone["battery"]
        lat = phone["latitude"]
        lon = phone["longitude"]
        timestamp = phone["timestamp"]

        status = "LIVE" if is_live(timestamp) else "STALE"

        print()
        print(f"{name}")
        print("-" * 40)

        if battery is not None:
            print(f"Battery:    {battery:.0f}%")
        else:
            print("Battery:    No data")

        if lat is not None and lon is not None:
            print(f"Location:   {lat:.6f}, {lon:.6f}")
        else:
            print("Location:   No data")

        print(f"Updated:    {format_age(timestamp)}")
        print(f"Status:     {status}")

    print()
    print("=" * 60)
    print("                 BATTERY ALERTS")
    print("=" * 60)

    low_battery_found = False

    for name, phone in phones.items():

        battery = phone["battery"]

        if battery is not None and battery < LOW_BATTERY_THRESHOLD:

            low_battery_found = True

            closest_name, distance = find_closest_teammate(
                name,
                phones
            )

            print()
            print(f"⚠️  {name} has LOW BATTERY: {battery:.0f}%")

            if closest_name is not None:
                print(f"    Closest teammate: {closest_name}")
                print(f"    Distance: {distance:.3f} km")
            else:
                print("    No teammate location available.")

    if not low_battery_found:
        print()
        print("No phones currently have low battery.")

    print()
    print("=" * 60)
    print()


#main 

def main():

    print("Connecting to ThingsBoard...")

    token = login()

    print("Connected successfully!")

    phones = get_phone_data(token)

    display_results(phones)


app = FastAPI()

@app.get("/")
def home():
    return FileResponse("templates/index.html")


@app.get("/api/status")
def get_status():
    token = login()
    phones = get_phone_data(token)

    alerts = []

    for name, phone in phones.items():
        battery = phone["battery"]

        if battery is not None and battery < LOW_BATTERY_THRESHOLD:
            closest_name, distance = find_closest_teammate(name, phones)

            alerts.append({
                "phone": name,
                "battery": battery,
                "closest": closest_name,
                "distance_km": distance,
            })

    return {
        "phones": phones,
        "alerts": alerts,
    }


if __name__ == "__main__":
    main()