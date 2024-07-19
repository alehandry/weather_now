from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# Конфигурация Open-Meteo API
API_URL = "https://api.open-meteo.com/v1/forecast"
SEARCH_URL = "https://geocoding-api.open-meteo.com/v1/search"


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    hourly_weather_data = None
    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            lat, lon = get_coordinates(city)
            if lat and lon:
                hourly_weather_data = fetch_hourly_weather(lat, lon)
                if hourly_weather_data and len(hourly_weather_data['time']) > 0:
                    # Получение временной зоны из данных
                    timezone = hourly_weather_data.get('timezone', 'UTC')
                    tz = pytz.timezone(timezone)

                    # Определение текущего времени в этой временной зоне
                    now = datetime.now(tz)

                    # Преобразование строковых временных меток в объекты datetime с учетом временной зоны
                    times_with_tz = [datetime.fromisoformat(t).replace(tzinfo=tz) for t in hourly_weather_data['time']]

                    # Поиск ближайшего времени в данных
                    closest_time = min(times_with_tz, key=lambda t: abs(t - now))
                    index = times_with_tz.index(closest_time)

                    weather_data = {
                        'temperature': hourly_weather_data['temperature_2m'][index] if len(
                            hourly_weather_data['temperature_2m']) > 0 else 'N/A',
                        'relative_humidity': hourly_weather_data['relative_humidity_2m'][index] if len(
                            hourly_weather_data['relative_humidity_2m']) > 0 else 'N/A',
                        'pressure': hourly_weather_data['pressure_msl'][index] if len(
                            hourly_weather_data['pressure_msl']) > 0 else 'N/A',
                        'windspeed': hourly_weather_data['wind_speed_10m'][index] if len(
                            hourly_weather_data['wind_speed_10m']) > 0 else 'N/A'
                    }
                print(f"Weather Data: {weather_data}")  # Debug print
                print(f"Hourly Weather Data: {hourly_weather_data}")  # Debug print
    return render_template('index.html', weather_data=weather_data, hourly_weather_data=hourly_weather_data)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    response = requests.get(SEARCH_URL, params={'name': query, 'count': 5})
    data = response.json()
    results = [
        {
            'name': result['name'],
            'latitude': result['latitude'],
            'longitude': result['longitude']
        }
        for result in data.get('results', [])
    ]
    return jsonify(results)


def get_coordinates(city):
    response = requests.get(SEARCH_URL, params={'name': city, 'count': 1})
    data = response.json()
    if data['results']:
        result = data['results'][0]
        return result['latitude'], result['longitude']
    return None, None


def fetch_hourly_weather(lat, lon):
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m',
        'timezone': 'auto'
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    if 'hourly' in data:
        hourly = data['hourly']
        return {
            'timezone': data.get('timezone', 'UTC'),
            'time': hourly.get('time', []),
            'temperature_2m': hourly.get('temperature_2m', []),
            'relative_humidity_2m': hourly.get('relative_humidity_2m', []),
            'pressure_msl': hourly.get('pressure_msl', []),
            'wind_speed_10m': hourly.get('wind_speed_10m', [])
        }
    else:
        return {}


if __name__ == '__main__':
    app.run(debug=True)
