# Gas Station Route Planner Setup Guide

## Overview
The application now includes a **Route Planner** feature that allows you to:
1. Search for a route using addresses (completely free, no API keys needed!)
2. Automatically find all nearby gas stations along the route
3. View gas prices and estimated time detours for each station

## Why No API Keys?

This implementation uses **completely free, open-source tools**:
- **Folium** - Open-source mapping library (creates interactive maps)
- **OpenStreetMap** - Free map tiles (used instead of Google Maps)
- **Nominatim** - Free address geocoding (powered by OpenStreetMap)
- **OpenRouteService** - Free routing API (no key required for basic use)

**Cost: $0 forever!** No sign-ups, no API key management, no surprise bills.

## Quick Start

### 1. Install Dependencies

Run this once:
```bash
pip install -r requirements.txt
```

New packages added:
- `folium==0.14.0` - Interactive maps
- `geopy==2.4.0` - Address geocoding

### 2. No Configuration Needed!

That's it! Just run the app:
```bash
python app.py
```

### 3. Access the Route Planner

Visit: `http://localhost:5000/route-planner`

Or click the green **"📍 Route Planner"** button on the main page.

## How It Works

### Address Search
- Enter a starting address and destination
- Uses **Nominatim** (free OpenStreetMap geocoding) to find coordinates
- Works best with Canadian addresses

### Route Display
- Map shows start (🟢 green), end (🔴 red), and route (blue line)
- Uses **OpenRouteService** free API to calculate actual driving routes
- Falls back to straight line if routing unavailable

### Gas Station Finder
- Automatically finds all nearby gas stations within your threshold distance
- Shows for each station:
  - **Gas Station Name/Banner**
  - **Address**
  - **Prix Régulier** (regular gas price)
  - **Prix Super** (premium gas price)
  - **Distance from Start** (km along route)
  - **Time Detour** (estimated extra time in minutes)

### Distance Calculations
- Uses **Haversine formula** for accurate Earth distances
- Point-to-line distance calculation to find closest station to route
- All calculations done server-side (no external API calls)

## Features

### Search
- Enter starting and destination addresses
- Supports Canadian addresses best
- Example: "45 Rue McGill, Montreal" to "Quebec City, QC"

### Filtering
- Adjust **"Within (km)"** threshold to change search radius
- Default: 2 km from the route
- Try increasing to 5-10 km for longer routes

### Map Display
- Interactive Folium map (zoom, pan, click markers)
- Green marker = Start point
- Red marker = End point
- Blue marker = Gas stations
- Hover over stations to see name and distance

## Troubleshooting

### "Could not find one or both addresses"
**Solution:**
- Be more specific with addresses
- Include city and province/state
- Try: "123 Main St, Montreal, QC" instead of just "123 Main"

### No stations appear on map
**Possible causes:**
1. No gas stations with valid coordinates in database
2. Threshold distance is too small
3. Gas stations are far from the route

**Solutions:**
- Increase threshold distance (try 5-10 km)
- Ensure database has been updated: the app auto-updates every 5 minutes
- Check that your `data.xlsx` has "Latitude" and "Longitude" columns

### Map loads but route line doesn't show
- This might happen if OpenRouteService rate-limits (rare)
- The app will fall back to a straight line route
- Functionality remains unchanged (stations still found)

### Application slow on first search
- Nominatim (free geocoding) can be slow sometimes (1-3 seconds)
- This is normal for free services
- Subsequent searches are usually faster

## Data Requirements

Your gas station data (from `data.xlsx`) should have these columns:
- ✓ **Bannière** (gas station brand)
- ✓ **Adresse** (street address)
- ✓ **Prix Régulier** (regular gas price)
- ✓ **Prix Super** (premium gas price)
- ✓ **Code Postal** (postal code)
- ✓ **Latitude** (latitude coordinate) - Required for route planner
- ✓ **Longitude** (longitude coordinate) - Required for route planner

If Latitude/Longitude are missing:
- The station will still appear in the main station list
- But won't show up in the route planner
- It will skip stations without coordinates

## Technical Details

### Libraries Used
- **Folium** - Creates interactive Leaflet.js maps
- **Geopy** - Geocodes addresses using Nominatim (OpenStreetMap)
- **Requests** - Makes HTTP requests to OpenRouteService
- **Flask** - Web framework (already in use)

### Free APIs Used
- **Nominatim** - Address geocoding (OpenStreetMap project)
  - Rate limit: ~1 request per second
  - No key required
- **OpenRouteService** - Route calculation
  - Rate limit: ~40 requests/minute without key
  - Perfect for personal use
  - No key required

### Distance Formula
- **Haversine Formula**: Calculates great-circle distance on Earth
- **Point-to-Line Distance**: Finds closest point on route to station
- All in kilometers, all free calculations

## Performance Notes

- First search may take 2-5 seconds (geocoding)
- Subsequent searches are faster
- Map generates server-side, sent to browser as HTML
- All distance calculations on server
- No third-party JavaScript libraries required (except Leaflet, which comes with Folium)

## Privacy

**Your data stays private!**
- No Google tracking
- No third-party analytics
- Only request data sent to:
  - Nominatim (for address lookup)
  - OpenRouteService (for routing)
- No personal information collected

## Limitations

- **Address accuracy**: Depends on OpenStreetMap data quality
- **Routing**: May be less detailed than commercial routing services
- **Rate limits**: Free tier can handle ~40 routes/minute
- **Coverage**: Works best with North American addresses

## Future Enhancements (Optional)

If you want to upgrade later:
- Add Google Maps or Mapbox for better routing (requires API key, $$$)
- Use HERE Maps API
- Integrate with OSRM (Open Source Routing Machine)
- Add turn-by-turn directions
- Calculate actual time to visit each station

## Support

**For issues with the app:**
- Check the terminal/console for error messages
- Look at the browser console (F12 > Console tab)
- Ensure `data.xlsx` is up-to-date
- Verify database is initialized

**For OpenStreetMap/Nominatim:**
- [OpenStreetMap Docs](https://www.openstreetmap.org/)
- [Nominatim Usage](https://nominatim.org/usage/)

**For Folium:**
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [Leaflet.js Docs](https://leafletjs.com/)

## Summary

✅ **Completely Free** - No API keys, no costs ever  
✅ **Open Source** - Using open-source libraries  
✅ **Privacy-Friendly** - Your data stays local  
✅ **Easy Setup** - Just run the app  
✅ **Reliable** - Uses proven open-source projects  

Enjoy your route planner!
