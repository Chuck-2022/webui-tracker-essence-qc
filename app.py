from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from database import *
from common import *
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import json
from math import radians, sin, cos, sqrt, atan2
import folium
from geopy.geocoders import Nominatim
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time

app = Flask(__name__)
app.secret_key = '&^DTNmD2jHJ^e3^h5zgFgpJ@uvAx!U7pC%*hZjEQ$^&Ag9yY`k'

# Route-planner cache: key → {map_json, error_message, stations, timestamp}
_route_cache = {}
_ROUTE_CACHE_TTL = 600  # seconds (10 minutes)


def _route_cache_key(start_address, end_address, threshold):
    return f"{start_address.lower().strip()}|{end_address.lower().strip()}|{threshold}"


def _route_cache_get(key):
    entry = _route_cache.get(key)
    if entry and (time.time() - entry['ts']) < _ROUTE_CACHE_TTL:
        return entry['map_json'], entry['error_message'], entry['stations']
    return None


def _route_cache_set(key, map_json, error_message, stations):
    _route_cache[key] = {
        'map_json': map_json,
        'error_message': error_message,
        'stations': stations,
        'ts': time.time()
    }

# Initialize database
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    banner_search = request.args.get('banner', '')
    address_search = request.args.get('address', '')
    postal_search = request.args.get('code_postal', '')
    websites = get_all_station()

    sort_by = request.args.get('sort_by', '')
    sort_dir = request.args.get('sort_dir', 'asc')

    selected_stations = [w for w in websites if w[7]]
    filtered_stations = [w for w in websites if not w[7]]

    if banner_search or address_search or postal_search:
        banner_term = banner_search.lower()
        address_term = address_search.lower()
        postal_term = postal_search.lower()

        filtered_stations = [
            w for w in filtered_stations
            if (not banner_search or banner_term in (w[1] or '').lower())
            and (not address_search or address_term in (w[2] or '').lower())
            and (not postal_search or postal_term in (w[5] or '').lower())
        ]

    sort_mapping = {
        'banner': 1,
        'address': 2,
        'prix_regulier': 3,
        'prix_super': 4,
        'code_postal': 5,
    }
    if sort_by in sort_mapping:
        idx = sort_mapping[sort_by]
        reverse = sort_dir == 'desc'
        selected_stations.sort(key=lambda w: (w[idx] or '').lower(), reverse=reverse)
        filtered_stations.sort(key=lambda w: (w[idx] or '').lower(), reverse=reverse)

    if request.method == 'POST':
        address = request.form.get('address')

        if address:
            data = {
                'banner': '',
                'address': address,
                'prix_regulier': '',
                'prix_super': '',
                'code_postal': '',
                'gmap': ''
            }
            add_website(data)
            flash('Station added successfully!', 'success')
        else:
            flash('Address is required!', 'error')

        return redirect(url_for('index'))

    return render_template(
        'index.html',
        selected_stations=selected_stations,
        filtered_stations=filtered_stations,
        banner_search=banner_search,
        address_search=address_search,
        postal_search=postal_search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        has_filters=bool(banner_search or address_search or postal_search)
    )

def update_all_data(from_site=False):
    try:
        print('\nUpdating data...', end=' ')
        fetch_data()
        # Reset route cache since data has changed
        global _route_cache
        _route_cache = {}
        df = pd.read_excel('./data/data.xlsx')
        # Assume columns are 'banner', 'address', 'prix_regulier', 'prix_super', 'code_postal', 'gmap'
        for index, row in df.iterrows():
            # Handle missing latitude and longitude columns
            latitude = None
            longitude = None
            try:
                latitude = row['Latitude'] if 'Latitude' in df.columns else None
                longitude = row['Longitude'] if 'Longitude' in df.columns else None
            except:
                pass
            
            data = {
                'banner': row['Bannière'],
                'address': row['Adresse'],
                'prix_regulier': row['Prix Régulier'],
                'prix_super': row['Prix Super'],
                'code_postal': row['Code Postal'],
                'gmap': create_gmap_link(str(row['Adresse'])),
                'selected': False,
                'latitude': latitude,
                'longitude': longitude
            }
            existing = get_station_by_address(data['address'])
            if existing:
                update_website_data(data, existing[0])
            else:
                add_website(data)
        print('Data updated successfully!')
        if from_site:
            flash('Data updated successfully!', 'success')
    except Exception as e:
        print('Error update_all_data', e)
        if from_site:
            flash(f'Error updating data: {str(e)}', 'error')
@app.route('/update', methods=['POST'])
def update():
    update_all_data(True)
    return redirect(url_for('index'))

@app.route('/delete/<int:website_id>')
def delete(website_id):
    delete_website(website_id)
    flash('Website deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle/<int:website_id>')
def toggle(website_id):
    toggle_selected(website_id)
    return redirect(url_for('index'))  # Redirects without search parameter


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth in kilometers"""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def point_to_line_distance(point_lat, point_lon, line_start_lat, line_start_lon, line_end_lat, line_end_lon):
    """Calculate shortest distance from a point to a line segment in kilometers"""
    # Convert lat/lon (in degrees) to approximate meters using planar projection
    # At 45 degrees latitude (middle of Canada):
    # 1 degree latitude ≈ 111,320 meters
    # 1 degree longitude ≈ 111,320 * cos(latitude) meters
    
    # Use average latitude for better accuracy
    avg_lat = (point_lat + line_start_lat + line_end_lat) / 3
    lat_rad = radians(avg_lat)
    
    # Conversion factors (meters per degree)
    meters_per_lat = 111320
    meters_per_lon = 111320 * cos(lat_rad)
    
    # Convert all coordinates to meters
    p_x = point_lon * meters_per_lon
    p_y = point_lat * meters_per_lat
    a_x = line_start_lon * meters_per_lon
    a_y = line_start_lat * meters_per_lat
    b_x = line_end_lon * meters_per_lon
    b_y = line_end_lat * meters_per_lat
    
    # Calculate distance from point to line segment
    ab_x = b_x - a_x
    ab_y = b_y - a_y
    ap_x = p_x - a_x
    ap_y = p_y - a_y
    
    ab_sq = ab_x**2 + ab_y**2
    if ab_sq == 0:
        # Line segment is a point
        return haversine_distance(point_lat, point_lon, line_start_lat, line_start_lon)
    
    # Find closest point on line segment
    t = max(0, min(1, (ap_x * ab_x + ap_y * ab_y) / ab_sq))
    closest_x = a_x + t * ab_x
    closest_y = a_y + t * ab_y
    
    # Distance in meters
    dist_m = sqrt((p_x - closest_x)**2 + (p_y - closest_y)**2)
    return dist_m / 1000  # Convert to km


@lru_cache(maxsize=128)
def get_route_time_from_osrm(start_lon, start_lat, end_lon, end_lat, waypoint_lon=None, waypoint_lat=None):
    """
    Get route time from OSRM in seconds
    If waypoint is provided, route goes through it: start -> waypoint -> end
    Returns the duration in seconds, or None if the request fails
    """
    try:
        if waypoint_lon is not None and waypoint_lat is not None:
            # Route with waypoint: start -> waypoint -> end
            coordinates = f'{start_lon},{start_lat};{waypoint_lon},{waypoint_lat};{end_lon},{end_lat}'
        else:
            # Direct route: start -> end
            coordinates = f'{start_lon},{start_lat};{end_lon},{end_lat}'
        
        osrm_url = f'https://router.project-osrm.org/route/v1/driving/{coordinates}'
        osrm_params = {
            'overview': 'false',  # Don't need geometry for time calculation
            'geometries': 'geojson',
            'alternatives': 'false'
        }
        
        response = requests.get(osrm_url, params=osrm_params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'routes' in data and len(data['routes']) > 0:
                return data['routes'][0]['duration']  # Duration in seconds
    except Exception as e:
        print(f'Error getting route time from OSRM: {e}')
    
    return None


def distance_along_route(station_lat, station_lon, route_points):
    """Calculate the distance along the route to the nearest point on the route"""
    if not route_points or len(route_points) < 2:
        return 0
    
    total_distance = 0
    min_distance_to_route = float('inf')
    distance_at_min = 0
    
    for i in range(len(route_points) - 1):
        p1 = route_points[i]
        p2 = route_points[i + 1]
        
        # Distance from station to this segment
        dist = point_to_line_distance(station_lat, station_lon, p1[0], p1[1], p2[0], p2[1])
        
        if dist < min_distance_to_route:
            min_distance_to_route = dist
            distance_at_min = total_distance + haversine_distance(p1[0], p1[1], station_lat, station_lon)
        
        total_distance += haversine_distance(p1[0], p1[1], p2[0], p2[1])
    
    return distance_at_min


def calculate_station_detour(station_data, start_lon, start_lat, end_lon, end_lat, original_route_time, route_points):
    """Calculate detour time for a single station (for parallel processing)"""
    station_id, banner, address, prix_reg, prix_super, code_postal, lat, lon, gmap = station_data
    
    time_detour = 0
    if original_route_time is not None:
        route_with_station_time = get_route_time_from_osrm(
            start_lon, start_lat,
            end_lon, end_lat,
            lon, lat  # Add station as waypoint
        )
        if route_with_station_time is not None:
            time_detour = (route_with_station_time - original_route_time) / 60
            time_detour = max(0, time_detour)
    
    distance_start = distance_along_route(lat, lon, route_points)
    return {
        'station_data': station_data,
        'distance_from_start': distance_start,
        'time_detour': time_detour
    }


@app.route('/route-planner', methods=['GET', 'POST'])
def route_planner():
    """Route planner page using client-side Leaflet map"""
    map_json = None
    error_message = None
    stations = []
    
    if request.method == 'POST':
        try:
            start_address = request.form.get('start_address', '').strip()
            end_address = request.form.get('end_address', '').strip()
            threshold = float(request.form.get('threshold', 2))
            
            cache_key = _route_cache_key(start_address, end_address, threshold)
            cached = _route_cache_get(cache_key)
            if cached:
                map_json, error_message, stations = cached
            else:
                if not start_address or not end_address:
                    error_message = 'Please enter both start and end addresses'
                else:
                    # Geocode addresses using Nominatim (free)
                    geolocator = Nominatim(user_agent='gasbuddy_route_planner')
                    
                    try:
                        start_loc = geolocator.geocode(start_address + ', Canada', timeout=10)
                    except:
                        start_loc = None
                        
                    try:
                        end_loc = geolocator.geocode(end_address + ', Canada', timeout=10)
                    except:
                        end_loc = None
                    
                    if not start_loc or not end_loc:
                        error_message = 'Could not find one or both addresses. Try more specific addresses (e.g., with city/province).'
                    else:
                        # Create base map
                        center_lat = (start_loc.latitude + end_loc.latitude) / 2
                        center_lon = (start_loc.longitude + end_loc.longitude) / 2
                        route_map = folium.Map(
                            location=[center_lat, center_lon],
                            zoom_start=10,
                            tiles='OpenStreetMap'
                        )
                        
                        # Add start and end markers
                        folium.Marker(
                            location=[start_loc.latitude, start_loc.longitude],
                            popup=f'<b>Start</b><br>{start_address}',
                            icon=folium.Icon(color='green', icon='play', prefix='fa'),
                            tooltip='Start Point'
                        ).add_to(route_map)
                        
                        folium.Marker(
                            location=[end_loc.latitude, end_loc.longitude],
                            popup=f'<b>End</b><br>{end_address}',
                            icon=folium.Icon(color='red', icon='stop', prefix='fa'),
                            tooltip='End Point'
                        ).add_to(route_map)
                        
                        # Get route using OSRM (Open Source Routing Machine) - completely free, no API key needed
                        route_points = [
                            (start_loc.latitude, start_loc.longitude),
                            (end_loc.latitude, end_loc.longitude)
                        ]
                        
                        try:
                            # Use OSRM public API for free routing with GeoJSON output
                            osrm_url = f'https://router.project-osrm.org/route/v1/driving/{start_loc.longitude},{start_loc.latitude};{end_loc.longitude},{end_loc.latitude}'
                            osrm_params = {
                                'overview': 'full',  # Get full route geometry
                                'geometries': 'geojson',  # Return as GeoJSON (no decoding needed)
                                'alternatives': 'false'
                            }
                            
                            response = requests.get(osrm_url, params=osrm_params, timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                if 'routes' in data and len(data['routes']) > 0:
                                    # Extract coordinates from GeoJSON geometry
                                    route_geom = data['routes'][0]['geometry']
                                    if 'coordinates' in route_geom:
                                        # Convert [lon, lat] to (lat, lon) for Folium
                                        route_points = [(coord[1], coord[0]) for coord in route_geom['coordinates']]
                        except Exception as e:
                            print(f'OSRM routing failed: {e}. Using straight line fallback.')
                            # Fallback to straight line if OSRM fails
                            route_points = [
                                (start_loc.latitude, start_loc.longitude),
                                (end_loc.latitude, end_loc.longitude)
                            ]
                        
                        # Get original route time (for calculating detour times)
                        original_route_time = get_route_time_from_osrm(start_loc.longitude, start_loc.latitude, end_loc.longitude, end_loc.latitude)
                        
                        # Draw route
                        folium.PolyLine(
                            locations=route_points,
                            color='blue',
                            weight=4,
                            opacity=0.8,
                            popup='Route'
                        ).add_to(route_map)
                        
                        # Find nearby stations
                        db_stations = get_stations_with_coordinates()
                        
                        # First pass: filter stations within threshold distance
                        filtered_stations = []
                        for station in db_stations:
                            station_id, banner, address, prix_reg, prix_super, code_postal, lat, lon, gmap = station
                            
                            # Check distance to route
                            min_distance = float('inf')
                            for i in range(len(route_points) - 1):
                                dist = point_to_line_distance(
                                    lat, lon,
                                    route_points[i][0], route_points[i][1],
                                    route_points[i + 1][0], route_points[i + 1][1]
                                )
                                min_distance = min(min_distance, dist)
                                if min_distance <= threshold:
                                    break
                            
                            if min_distance <= threshold:
                                filtered_stations.append((station, min_distance))
                        
                        # Parallel processing: calculate detour times for all filtered stations
                        nearby_stations = []
                        with ThreadPoolExecutor(max_workers=8) as executor:
                            futures = {
                                executor.submit(
                                    calculate_station_detour,
                                    station,
                                    start_loc.longitude, start_loc.latitude,
                                    end_loc.longitude, end_loc.latitude,
                                    original_route_time,
                                    route_points
                                ): (station, min_dist) for station, min_dist in filtered_stations
                            }
                            
                            for future in as_completed(futures):
                                station, min_dist = futures[future]
                                result = future.result()
                                station_data = result['station_data']
                                station_id, banner, address, prix_reg, prix_super, code_postal, lat, lon, gmap = station_data
                                
                                nearby_stations.append({
                                    'id': station_id,
                                    'banner': banner,
                                    'address': address,
                                    'prix_regulier': prix_reg,
                                    'prix_super': prix_super,
                                    'latitude': lat,
                                    'longitude': lon,
                                    'gmap': gmap,
                                    'distance_from_start': round(result['distance_from_start'], 2),
                                    'distance_to_route': round(min_dist, 2),
                                    'time_detour': round(result['time_detour'], 1)
                                })
                        
                        # Sort by distance from start
                        nearby_stations.sort(key=lambda x: x['distance_from_start'])
                        stations = nearby_stations
                        
                        # Create map data for client-side rendering with Leaflet
                        map_data = {
                            'center_lat': center_lat,
                            'center_lon': center_lon,
                            'start': {
                                'lat': start_loc.latitude,
                                'lon': start_loc.longitude,
                                'label': f'Start: {start_address}'
                            },
                            'end': {
                                'lat': end_loc.latitude,
                                'lon': end_loc.longitude,
                                'label': f'End: {end_address}'
                            },
                            'route_points': route_points,
                            'stations': stations
                        }
                        
                        # Convert to JSON for passing to template
                        map_json = json.dumps(map_data)

                # Store result in cache (even errors, so we don't hammer geocoding)
                _route_cache_set(cache_key, map_json, error_message, stations)
        except Exception as e:
            error_message = f'Error: {str(e)}'
            print(f'Route planner error: {e}')
            import traceback
            traceback.print_exc()
    
    return render_template(
        'route-planner.html',
        map_json=map_json,
        error_message=error_message,
        stations=stations
    )


if __name__ == '__main__':
    # Setup scheduler
    scheduler = BackgroundScheduler()
    update_all_data()
    scheduler.add_job(update_all_data, 'interval', minutes=5)
    scheduler.start()

    try:
        app.run(host="0.0.0.0")
    except (KeyboardInterrupt):
        scheduler.shutdown()