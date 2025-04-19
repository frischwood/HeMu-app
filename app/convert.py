import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Union, Dict, Any
import numpy as np
import xarray as xr
import rasterio
# import matplotlib.pyplot as plt
from pandas import to_datetime

# Constants
DATETIME_FORMAT = os.environ["DATETIME_FORMAT"]
NODATA_VALUE = -9999.0
DEFAULT_COG_OPTIONS = {
    "driver": "COG",
    "compress": "DEFLATE",
    "predictor": 2,
    # "tiled": True,
    # "blockxsize": 256, 
    # "blockysize": 256,
    "overview_resampling": "average",
    # "overview_levels": [2, 4, 8, 16],
    "nodata": NODATA_VALUE
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def open_netcdf_dataset(file_path: Union[str, Path]) -> xr.Dataset:

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NetCDF file not found: {file_path}")
    
    try:
        return xr.open_dataset(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open NetCDF file: {e}")


def extract_variable_data(
    dataset: xr.Dataset, 
    variable_name: str, 
    time_index: int = 0) -> Tuple[xr.DataArray, str]:

    if variable_name not in dataset:
        raise ValueError(f"Variable '{variable_name}' not found in dataset")
    
    # Handle time-indexed or static data
    if "time" in dataset.dims:
        data_array = dataset[variable_name].isel(time=time_index)
        timestamp = to_datetime(dataset.time.values[time_index]).strftime(format=DATETIME_FORMAT)
    else:
        data_array = dataset[variable_name]
        timestamp = datetime.now().strftime(format=DATETIME_FORMAT)
    
    return data_array, timestamp


def prepare_data_array(data_array: xr.DataArray) -> xr.DataArray:

    # Convert to float32 for better compatibility
    if data_array.dtype != np.float32:
        data_array = data_array.astype(np.float32)
    
    # Replace NaN values with NoData
    if np.isnan(data_array.values).any():
        logger.info("Replacing NaN values with NoData value")
        data_array = data_array.fillna(NODATA_VALUE)
    
    # Handle _FillValue properly to avoid encoding issues
    data_array.encoding.update({"_FillValue": NODATA_VALUE})
    if '_FillValue' in data_array.attrs:
        del data_array.attrs['_FillValue']
    
    # Log diagnostics
    logger.info(f"Data range: {data_array.min().values} to {data_array.max().values}")
    logger.info(f"Data shape: {data_array.shape}")
    logger.info(f"Data contains NaNs: {np.isnan(data_array.values).any()}")
    
    # Ensure georeferencing
    try:
        # Check if spatial dimensions exist
        if 'x' in data_array.dims and 'y' in data_array.dims:
            logger.info("Using x/y dimensions for spatial reference")
            data_array.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
        elif 'lon' in data_array.dims and 'lat' in data_array.dims:
            logger.info("Using lon/lat dimensions for spatial reference")
            data_array.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
        else:
            logger.error(f"Available dimensions: {list(data_array.dims)}")
            raise ValueError("No recognized spatial dimensions found")
        
        # Set CRS
        data_array.rio.write_crs("EPSG:4326", inplace=True)
            
        # Check coordinates
        logger.info(f"Y-coordinates order: {data_array.y.values[0]} to {data_array.y.values[-1]}")
        logger.info(f"X-coordinates order: {data_array.x.values[0]} to {data_array.x.values[-1]}")
        
        # Fix Y coordinates if needed (north should be at top)
        if data_array.y[0] < data_array.y[-1]:
            logger.info("Y-coordinates are in ascending order (south to north), inverting...")
            new_y = np.sort(data_array.y.values)[::-1]
            data_array = data_array.reindex(y=new_y)
            logger.info(f"New Y-coordinates order: {data_array.y.values[0]} to {data_array.y.values[-1]}")
    
    except Exception as e:
        raise ValueError(f"Error setting georeferencing: {str(e)}")
    
    return data_array


def add_metadata(data_array: xr.DataArray, units: str = "W/m^2", data_type: str = "irradiance") -> xr.DataArray:

    # Calculate statistics
    data_min = float(data_array.min().values)
    data_max = float(data_array.max().values)
    data_mean = float(data_array.mean().values)
    data_std = float(data_array.std().values)
    
    # Add metadata
    data_array.attrs.update({
        'min': str(data_min),
        'max': str(data_max),
        'mean': str(data_mean),
        'AREA_OR_POINT': 'Area',
        'data_type': data_type,
        'units': units,
        'rio:statistics': json.dumps({
            '1': {  # Band 1
                'minimum': data_min,
                'maximum': data_max,
                'mean': data_mean,
                'stddev': data_std
            }
        }),
    })
    
    return data_array, (data_min, data_max, data_mean)

def write_cog(
    data_array: xr.DataArray, 
    output_path: Path, 
    cog_options: Optional[Dict[str, Any]] = None) -> None:

    if cog_options is None:
        cog_options = DEFAULT_COG_OPTIONS
    
    logger.info(f"Creating COG file: {output_path}")
    
    try:
        data_array.rio.to_raster(output_path, **cog_options)
        logger.info("COG creation successful")
    except Exception as e:
        raise IOError(f"Failed to write COG: {str(e)}")


# def create_preview(
#     data_array: xr.DataArray, 
#     output_path: Path, 
#     variable_name: str, 
#     timestamp: str, 
#     data_range: Tuple[float, float]) -> None:

#     data_min, data_max = data_range
    
#     plt.figure(figsize=(10, 8))
#     plt.imshow(data_array.values, cmap='magma', vmin=data_min, vmax=data_max)
#     plt.colorbar(label='W/m²')
#     plt.title(f"{variable_name} - {timestamp}")
#     plt.savefig(output_path)
#     plt.close()
#     logger.info(f"Preview image saved to: {output_path}")


def validate_cog(cog_path: Path) -> None:

    with rasterio.open(cog_path) as src:
        logger.info(f"Validating COG file: {cog_path}")
        logger.info(f"Metadata: {src.meta}")
        logger.info(f"Tags: {src.tags()}")
        logger.info(f"NoData value: {src.nodata}")
        logger.info(f"Image bounds: {src.bounds}")
        logger.info(f"CRS: {src.crs}")
        
        # Sample to verify data
        window = ((0, 10), (0, 10))
        sample_data = src.read(1, window=window)
        logger.info(f"Sample data range: {np.min(sample_data)} to {np.max(sample_data)}")


def convert_netcdf_to_cog(
    netcdf_path: Union[str, Path], 
    variable_name: str, 
    output_dir: Union[str, Path] = "data/cogs", 
    time_index: int = 0) -> Tuple[Path, str, float, float]:

    # Convert paths to Path objects
    netcdf_path = Path(netcdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Open the dataset
    dataset = open_netcdf_dataset(netcdf_path)
    
    # Step 2: Extract the variable data
    data_array, timestamp = extract_variable_data(dataset, variable_name, time_index)
    
    # Step 3: Prepare the data array
    data_array = prepare_data_array(data_array)
    
    # Step 4: Add metadata
    data_array, (data_min, data_max, data_mean) = add_metadata(data_array)
    
    # Step 5: Define output paths
    cog_path = output_dir / f"{variable_name}_{timestamp}.tif"
    # preview_path = output_dir / f"{variable_name}_{timestamp}_preview.png"
    
    # Step 6: Write the COG
    write_cog(data_array, cog_path)
    
    # Step 7: Create a preview image
    # create_preview(data_array, preview_path, variable_name, timestamp, (data_min, data_max))
    
    # Step 8: Validate the COG
    validate_cog(cog_path)
    
    # Output rescale values for TiTiler
    logger.info(f"Rescale values for visualization: {data_min},{data_max}")
    logger.info(f"Recommended TiTiler parameters: colormap=magma&rescale={data_min},{data_max}")
    
    return cog_path, timestamp, data_min, data_max

# if __name__ == "__main__":
#     cog_path, timestamp, min_val, max_val = convert_netcdf_to_cog("data/netcdf/SISGHI-No-Horizon_2024-01-03T105743.nc", "SISGHI-No-Horizon")
#     logger.info(f"File saved to: {cog_path}")
#     logger.info(f"Timestamp: {timestamp}")