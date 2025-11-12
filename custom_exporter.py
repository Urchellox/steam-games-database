"""
custom_exporter.py
Custom exporter for Dashboard 3 — External APIs
Update interval: 20 seconds
Requires: prometheus_client, requests
"""

from prometheus_client import start_http_server, Gauge, Info, Counter
import requests
import time
import datetime

# --- Info / metadata ---
exporter_info = Info('custom_exporter_info', 'Information about the custom exporter')

# --- Gauges (>=10) ---
# Weather (Open-Meteo)
g_weather_temp_c = Gauge('weather_temperature_celsius', 'Current temperature', ['city', 'country'])
g_weather_wind_kmh = Gauge('weather_windspeed_kmh', 'Current wind speed', ['city', 'country'])
g_weather_code = Gauge('weather_code', 'Weather code (Open-Meteo)', ['city', 'country'])

# Crypto (CoinGecko)
g_crypto_btc_usd = Gauge('crypto_btc_usd', 'Bitcoin price USD')
g_crypto_eth_usd = Gauge('crypto_eth_usd', 'Ethereum price USD')

# FX rates (exchangerate.host)
g_fx_usd_kzt = Gauge('fx_usd_kzt', 'USD -> KZT exchange rate')
g_fx_eur_kzt = Gauge('fx_eur_kzt', 'EUR -> KZT exchange rate')

# GitHub activity (commits to prometheus/prometheus in last 24h)
g_github_prometheus_commits_24h = Gauge('github_prometheus_commits_24h', 'Commits in last 24h for prometheus/prometheus')

# Air quality (best-effort; if API missing -> set -1)
g_air_pm25 = Gauge('external_air_pm25', 'PM2.5 (µg/m3) - external provider (or -1 on fail)', ['city'])

# Simulated or derived metric (to reach >=10)
g_simulated_active_users = Gauge('simulated_active_users', 'Simulated active users (synthetic)')

# General upstream status (0/1)
g_exporter_up = Gauge('custom_exporter_up', 'Custom exporter overall up (1) / partial failure (0)')

# A simple counter example
c_requests_total = Counter('custom_exporter_requests_total', 'Total external requests made by exporter')

# --- Helpers / API fetchers ---
def fetch_open_meteo():
    """
    Open-Meteo current_weather for Astana (coordinates).
    """
    try:
        c_requests_total.inc()
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': 51.1694,
            'longitude': 71.4491,
            'current_weather': 'true',
            'timezone': 'Asia/Almaty'
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data.get('current_weather', {})
        if current:
            # temperature (°C), windspeed (m/s or km/h depending on API; Open-Meteo gives m/s normally)
            temp = current.get('temperature')
            windspeed = current.get('windspeed')
            wcode = current.get('weathercode')

            # convert windspeed to km/h if given in m/s (heuristic: if value < 60 assume m/s -> km/h)
            try:
                ws_val = float(windspeed) if windspeed is not None else 0.0
                if ws_val < 60:
                    ws_kmh = ws_val * 3.6
                else:
                    ws_kmh = ws_val
            except Exception:
                ws_kmh = 0.0

            g_weather_temp_c.labels(city='Astana', country='Kazakhstan').set(float(temp))
            g_weather_wind_kmh.labels(city='Astana', country='Kazakhstan').set(ws_kmh)
            g_weather_code.labels(city='Astana', country='Kazakhstan').set(int(wcode) if wcode is not None else 0)
            return True
        return False
    except Exception:
        return False

def fetch_coingecko():
    """
    CoinGecko simple price for bitcoin and ethereum in USD.
    """
    try:
        c_requests_total.inc()
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum',
            'vs_currencies': 'usd'
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        btc = j.get('bitcoin', {}).get('usd')
        eth = j.get('ethereum', {}).get('usd')
        if btc is not None:
            g_crypto_btc_usd.set(float(btc))
        if eth is not None:
            g_crypto_eth_usd.set(float(eth))
        return True
    except Exception:
        return False

def fetch_exchangerate():
    """
    exchangerate.host for latest USD->KZT and EUR->KZT
    """
    ok = True
    try:
        c_requests_total.inc()
        # USD -> KZT
        r1 = requests.get("https://api.exchangerate.host/latest", params={'base': 'USD', 'symbols': 'KZT'}, timeout=10)
        r1.raise_for_status()
        j1 = r1.json()
        usd_kzt = j1.get('rates', {}).get('KZT')
        if usd_kzt is not None:
            g_fx_usd_kzt.set(float(usd_kzt))
    except Exception:
        ok = False

    try:
        c_requests_total.inc()
        r2 = requests.get("https://api.exchangerate.host/latest", params={'base': 'EUR', 'symbols': 'KZT'}, timeout=10)
        r2.raise_for_status()
        j2 = r2.json()
        eur_kzt = j2.get('rates', {}).get('KZT')
        if eur_kzt is not None:
            g_fx_eur_kzt.set(float(eur_kzt))
    except Exception:
        ok = False

    return ok

def fetch_github_commits_last_24h():
    """
    Count commits to prometheus/prometheus during last 24 hours (best-effort, unauthenticated).
    """
    try:
        c_requests_total.inc()
        since = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat() + 'Z'
        url = "https://api.github.com/repos/prometheus/prometheus/commits"
        params = {'since': since, 'per_page': 100}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        commits = r.json()
        # commits is a list (or dict with message on error)
        if isinstance(commits, list):
            g_github_prometheus_commits_24h.set(len(commits))
            return True
        else:
            return False
    except Exception:
        return False

def fetch_air_quality():
    """
    Best-effort PM2.5 using Open-Meteo / placeholder (some APIs require keys).
    If cannot fetch, set -1.
    """
    try:
        c_requests_total.inc()
        # Open-Meteo has an air_quality endpoint (air_quality=true returns arrays) — try simplified request
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {
            'latitude': 51.1694,
            'longitude': 71.4491,
            'hourly': 'pm2_5',
            'timezone': 'Asia/Almaty'
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        j = r.json()
        # try to extract latest hourly pm2_5
        hourly = j.get('hourly', {})
        pm2_list = hourly.get('pm2_5', [])
        if pm2_list:
            # take last known
            val = pm2_list[-1]
            g_air_pm25.labels(city='Astana').set(float(val))
            return True
        else:
            g_air_pm25.labels(city='Astana').set(-1)
            return False
    except Exception:
        g_air_pm25.labels(city='Astana').set(-1)
        return False

# --- Main loop ---
def collect_all():
    success = True
    # individually fetch — don't fail whole run if one API fails
    if not fetch_open_meteo():
        success = False
    if not fetch_coingecko():
        success = False
    if not fetch_exchangerate():
        success = False
    if not fetch_github_commits_last_24h():
        success = False
    if not fetch_air_quality():
        # non-critical
        success = False

    # simulated metric (simple sinusoidish or time-based synthetic)
    try:
        # simulated active users: fluctuates with time of day (local seconds)
        sec = int(time.time()) % 3600
        simulated = 50 + (sec % 60)  # simple varying number 50..109
        g_simulated_active_users.set(simulated)
    except Exception:
        pass

    g_exporter_up.set(1 if success else 0)
    return success

if __name__ == '__main__':
    exporter_info.info({
        'version': '1.0',
        'author': 'Student',
        'sources': 'open-meteo,coingecko,exchangerate.host,github,air-quality-open-meteo'
    })

    # Start HTTP server on port 8000
    start_http_server(8000)
    print("Custom exporter started on :8000 — collecting every 20s")

    # Collect loop every 20 seconds
    INTERVAL = 20
    try:
        while True:
            start = time.time()
            try:
                collect_all()
            except Exception as e:
                # keep running; mark exporter_up = 0
                g_exporter_up.set(0)
                print("Collector error:", e)
            # sleep remaining until next tick
            elapsed = time.time() - start
            to_sleep = max(0, INTERVAL - elapsed)
            time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("Exporter stopped by user")
