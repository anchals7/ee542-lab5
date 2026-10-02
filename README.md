# EE 542 Lab 5 — Custom Phone Monitoring Program

## Overview

Our custom program is a **team phone monitoring dashboard** built on top of the ThingsBoard IoT data collected from our three phones.

The goal is to take the raw data from multiple phones and turn it into useful information about the team's current status.

### Data Flow

```text
Phone 1 ──┐
Phone 2 ──┼──> OwnTracks ──> ThingsBoard (AWS) ──> Python Backend ──> Web Dashboard
Phone 3 ──┘
```

Each phone sends telemetry such as:

* Battery level
* Latitude
* Longitude
* Timestamp

ThingsBoard stores this telemetry, and our Python program retrieves the latest values through the ThingsBoard REST API.

---

## What Our Program Does

The dashboard currently provides four main functions.

### 1. Displays all phones

The dashboard displays the latest location of all three phones on an interactive map using **Leaflet** and OpenStreetMap.

Each phone has its own marker on the map.

### 2. Monitors battery levels

The dashboard displays the current battery percentage for each phone.

For example:

```text
Teammate 1 — 64%
Teammate 2 — 40%
My Phone   — 89%
```

We use a **20% battery threshold** to identify low-battery phones.

### 3. Detects stale telemetry

Every telemetry record contains a timestamp.

The Python backend uses this timestamp to determine whether a phone's data is recent.

The dashboard therefore indicates whether each phone is currently:

```text
LIVE
```

or

```text
STALE
```

This helps distinguish between a phone that is actively reporting and a phone whose last known data is old.

### 4. Finds the closest teammate

This is the main custom feature of our program.

When a phone's battery falls below the 20% threshold, the program compares that phone's GPS coordinates with the coordinates of the other phones.

It calculates the geographic distance between the phones and identifies the closest teammate.

The dashboard can then display something like:

```text
Low Battery Alert

My Phone: 15%

Closest teammate:
Teammate 2

Distance:
0.16 km
```

This demonstrates how data from **multiple IoT devices can be combined to generate useful information**, rather than simply displaying the raw telemetry.

---

## Software Components

### Backend

We use **Python** with FastAPI.

The backend:

1. Logs into ThingsBoard.
2. Retrieves the latest telemetry for each phone.
3. Processes battery, location, and timestamp data.
4. Calculates distances between phones.
5. Determines low-battery alerts.
6. Provides the processed information through `/api/status`.

### Frontend

The frontend uses:

* HTML
* CSS
* JavaScript
* Leaflet
* OpenStreetMap

The page periodically requests the latest information from the Python backend and updates the phone cards and map.

---

## Example API Output

The backend produces data similar to:

```json
{
  "phones": {
    "Teammate 1": {
      "battery": 64,
      "latitude": 34.020338,
      "longitude": -118.286087
    },
    "Teammate 2": {
      "battery": 40,
      "latitude": 34.020239,
      "longitude": -118.286062
    },
    "My Phone": {
      "battery": 89,
      "latitude": 34.0227493,
      "longitude": -118.2805673
    }
  },
  "alerts": []
}
```

The frontend uses this information to update the dashboard.

---

## Why We Built It This Way

The purpose of the custom program is to demonstrate an additional processing layer on top of the IoT platform.

Instead of simply:

```text
Phone → ThingsBoard → Map
```

we have:

```text
Phone data
    ↓
ThingsBoard
    ↓
Python processing
    ↓
Multi-phone analysis
    ↓
Useful alerts and information
    ↓
Interactive dashboard
```

This allows us to combine information from multiple devices and create application-level logic based on that data.

## Current Status

The current implementation successfully:

* Retrieves telemetry from all three phones.
* Displays battery levels.
* Displays GPS locations.
* Shows phone locations on a map.
* Detects live/stale telemetry.
* Detects low-battery conditions.
* Calculates the closest teammate for a low-battery phone.
* Displays alerts through the web dashboard.

The program is designed so that additional sensor data from OwnTracks could be further incorporated.
