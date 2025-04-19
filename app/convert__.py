import os
import xarray as xr
import rioxarray
from pandas import to_datetime
from pathlib import Path
import datetime

DATETIME_FORMAT = os.environ["DATETIME_FORMAT"]

def convert_netcdf_to_cog(netcdf_path, variable_name, output_dir="data/cogs", time_index=0):
    netcdf_path = Path(netcdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(netcdf_path)

    if variable_name not in ds:
        raise ValueError(f"Variable '{variable_name}' not found in {netcdf_path}")

    # Handle time-indexed or static data
    if "time" in ds.dims:
        da = ds[variable_name].isel(time=time_index)
        # timestamp = str(ds.time.values[time_index])[:10]
        timestamp = to_datetime(ds.time.values[time_index]).strftime(format=DATETIME_FORMAT)
    else:
        da = ds[variable_name]
        timestamp = to_datetime(datetime.datetime.now(), format=DATETIME_FORMAT)

    # Ensure georeferencing
    da.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    da.rio.write_crs("EPSG:4326", inplace=True)

    out_path = output_dir / f"{variable_name}_{timestamp}.tif"
    da.rio.to_raster(out_path, driver="COG")

    return out_path, timestamp, None, None


# if __name__ == "__main__":
#     convert_netcdf_to_cog("/Users/frischho/Documents/dev/heliomont_dml/app/data/netcdf/SISGHI-No-Horizon_2024-01-03T105743.nc", "SISGHI-No-Horizon")