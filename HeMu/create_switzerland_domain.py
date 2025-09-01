#!/usr/bin/env python3
"""
Create Switzerland domain matcher for HeMu processing
"""

import xarray as xr
import numpy as np
import os
from pathlib import Path

def create_switzerland_domain():
    """Create domain matcher for Switzerland"""
    
    # Switzerland boundaries (approximate)
    lon_bounds = (5.95, 10.50)  # Swiss longitude range
    lat_bounds = (45.82, 47.81)  # Swiss latitude range
    resolution = 0.01  # ~1km resolution
    
    lon_min, lon_max = lon_bounds
    lat_min, lat_max = lat_bounds
    
    # Create coordinate arrays
    lons = np.arange(lon_min, lon_max + resolution, resolution)
    lats = np.arange(lat_min, lat_max + resolution, resolution)
    
    print(f"Creating Switzerland domain matcher:")
    print(f"  Longitude: {lon_min}° to {lon_max}° ({len(lons)} points)")
    print(f"  Latitude: {lat_min}° to {lat_max}° ({len(lats)} points)")
    print(f"  Resolution: {resolution}° (~{resolution*111:.1f}km)")
    print(f"  Grid size: {len(lats)} x {len(lons)} = {len(lats)*len(lons):,} pixels")
    
    # Create grid meshes
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Create dummy variable for grid definition (HeMu expects this)
    grid_mask = np.ones_like(lat_grid, dtype=np.float32)
    
    # Create xarray dataset in HeMu expected format
    ds_matcher = xr.Dataset({
        'grid_mask': (['lat', 'lon'], grid_mask),
        'longitude': (['lat', 'lon'], lon_grid), 
        'latitude': (['lat', 'lon'], lat_grid)
    }, coords={
        'lat': lats,
        'lon': lons
    })
    
    # Add attributes
    ds_matcher.attrs = {
        'title': 'Switzerland Domain Matcher for HeMu',
        'description': 'Spatial grid definition for Swiss solar irradiance modeling',
        'domain': 'CH',
        'resolution_degrees': resolution,
        'crs': 'EPSG:4326',
        'created_by': 'HeMu Switzerland setup'
    }
    
    # Add CRS information
    ds_matcher = ds_matcher.rio.write_crs("EPSG:4326")
    
    # Create output directory
    output_dir = Path(__file__).parent / "data/static/domainMatcher/CH"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as NetCDF
    output_file = output_dir / "domainMatcher_CH.nc"
    ds_matcher.to_netcdf(output_file)
    
    print(f"✅ Switzerland domain matcher saved to: {output_file}")
    return str(output_file)

if __name__ == "__main__":
    create_switzerland_domain()
