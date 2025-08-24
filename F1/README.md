# F1 Cog

A Discord bot cog that provides comprehensive Formula 1 data and statistics using the [OpenF1 API](https://openf1.org/).

## Features

This cog provides access to real-time and historical Formula 1 data including:

- 🏎️ **Driver Information** - Get detailed info about F1 drivers
- 🏁 **Session Data** - View race sessions, qualifying, and practice sessions
- ⏱️ **Lap Times** - Access lap data and statistics
- 🌤️ **Weather Data** - Track conditions during races
- 📊 **Car Telemetry** - High-speed telemetry data
- 📻 **Team Radio** - Access team radio communications
- 📈 **Statistics** - Best laps, averages, and performance metrics

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `f1` | Show F1 overview with upcoming sessions and session keys | `f1` |
| `f1driver` | Get information about a specific F1 driver | `f1driver <driver_number>` |
| `f1drivers` | Get all drivers for a session | `f1drivers [session_key]` |
| `f1sessions` | Get F1 sessions for a year | `f1sessions [year]` |
| `f1laps` | Get lap data for a session | `f1laps <session_key> [driver_number]` |
| `f1weather` | Get weather data for a meeting | `f1weather [meeting_key]` |
| `f1telemetry` | Get car telemetry data | `f1telemetry <session_key> <driver_number> [speed_threshold]` |
| `f1radio` | Get team radio messages | `f1radio <session_key> [driver_number]` |

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Load the cog in your Discord bot:
   ```python
   await bot.load_extension("F1")
   ```

## Usage Examples

### Get F1 overview and session keys
```
f1
```
Shows upcoming and recent F1 sessions with their session keys, making it easy to use other commands

### Get driver information
```
f1driver 1
```
Shows information about Max Verstappen (driver #1)

### Get all drivers for the latest session
```
f1drivers latest
```
Shows all drivers grouped by team for the current/latest session

### Get lap data for a specific session
```
f1laps 9159 55
```
Shows lap data for session 9159, filtered for driver #55 (Carlos Sainz)

### Get weather data
```
f1weather latest
```
Shows current weather conditions for the latest meeting

### Get high-speed telemetry
```
f1telemetry 9159 55 320
```
Shows telemetry data for driver #55 in session 9159 at speeds ≥320 km/h

### Get team radio messages
```
f1radio 9159 55
```
Shows team radio messages for session 9159, filtered for driver #55

## API Information

This cog uses the [OpenF1 API](https://openf1.org/), which provides:

- **Historical data**: Freely accessible, no authentication required
- **Real-time data**: Requires paid account (apply via their form)
- **Data formats**: JSON and CSV
- **Update frequency**: ~3 seconds after live events
- **Query timeout**: 10 seconds

## Data Sources

The OpenF1 API provides data from various sources:
- Car telemetry (speed, RPM, gear, throttle, brake, DRS)
- Driver information and team details
- Lap times and session results
- Weather conditions
- Team radio communications
- Pit stop data
- Position data and intervals

## Notes

- Use `latest` for `session_key` or `meeting_key` to get current data
- Speed threshold for telemetry defaults to 300 km/h
- All data comes from the OpenF1 API
- The API has a 10-second query timeout - break large queries into smaller ones if needed

## Credits

- Data provided by [OpenF1 API](https://openf1.org/)
- OpenF1 is an unofficial project not associated with Formula 1 companies
- F1, FORMULA ONE, FORMULA 1, FIA FORMULA ONE WORLD CHAMPIONSHIP, GRAND PRIX and related marks are trade marks of Formula One Licensing B.V. 