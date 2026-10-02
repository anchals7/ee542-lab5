import requests

THINGSBOARD_URL = "http://54.218.241.153:8080"

DEVICES = {
    "Teammate 1": "c60b7080-bbb1-11f1-a5fd-d51fed9ef52b",
    "Teammate 2": "6c390ad0-bbad-11f1-a5fd-d51fed9ef52b",
    "My Phone": "41f53430-bba6-11f1-a5fd-d51fed9ef52b",
}

USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"


def login():
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


def main():
    print("Logging into ThingsBoard...")

    token = login()

    print("Login successful!\n")

    for name, device_id in DEVICES.items():
        print(f"--- {name} ---")

        telemetry = get_latest_telemetry(token, device_id)

        print(f"Battery:   {telemetry.get('batt')}")
        print(f"Latitude:  {telemetry.get('lat')}")
        print(f"Longitude: {telemetry.get('lon')}")
        print()


if __name__ == "__main__":
    main()