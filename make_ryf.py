from calendar import isleap
import os
import sys
from pathlib import Path

import netCDF4 as nc
import numpy as np
import xarray as xr

# Pass year and variable as command line arguments
year1, var = sys.argv[1:]

year1 = int(year1)

era5dir = Path('/g/data/rt52/era5/single-levels/reanalysis/')

FillValue = np.int64(-1.e10)

# By default the second half of year1 is stitched into first half of year2
year2 = year1 + 1

files = []
# Make xarray dataset of all data from year1 and year2
for y in (year1, year2):
    files = files + sorted((era5dir / f"{var}/{y}"). glob('*.nc'))

ds = xr.open_mfdataset(files, decode_coords=True)

if isleap(year2):
    base_year = year1
    # Take one less day in to account for the leap day
    end_day = 29
else:
    base_year = year2
    end_day = 30

jan_apr_slice = slice(f'{year2}-1',f'{year2}-4-{end_day}')
jun_dec_slice = slice(f'{year1}-5',f'{year1}-12')

jan_apr = ds.sel(time=jan_apr_slice)
jun_dec = ds.sel(time=jun_dec_slice)

# Alter the time coordinate for one of the sections, depending on base year
if base_year == year1:
    jan_apr['time'] = ds.sel(time=slice(f'{year1}-1', f'{year1}-4')).time
else:
    jun_dec['time'] = ds.sel(time=slice(f'{year2}-5', f'{year2}-12')).time

# Take last six months of year1 and first six months of year2
ryf = xr.concat([jan_apr, jun_dec], dim='time')

encdict = {}

for varname in ryf.data_vars:

    encdict[varname] = ds[varname].encoding

    # Have to give all variables a useless FillValue attribute, otherwise xarray
    # makes it NaN and MOM does not like this
    if '_FillValue' not in ryf[varname].encoding: 
        encdict[varname]['_FillValue'] = FillValue

    # Only process variables with 3 or more dimensions
    if len(ryf[varname].shape) < 3: continue

    print("Processing ",varname)
    # Compress the data?
    encdict[varname].update(
                            { 
                              # zlib: True, 
                              # shuffle: True, 
                              # complevel: 4 
                              chunksizes: (24, 721, 1440),
                            }
                           )

for dim in ryf.dims:
    # Have to give all dimensions a useless FillValue attribute, otherwise xarray
    # makes it NaN and MOM does not like this
    encdim[dim].encoding['_FillValue'] = FillValue

# Make a new time dimension with no offset from origin (1900-01-01) so we don't get an offset after
# changing calendar to noleap
newtime = (ryf.indexes["time"].values - ryf.indexes["time"].values[0]) + np.datetime64('1900-01-01','D')
ryf.indexes["time"].values[:] = newtime[:]

ryf["time"].attrs = {
                     'modulo':' ',
                     'axis':'T',
                     'cartesian_axis':'T',
                    }

outfile = "RYF.{}.{}_{}.nc".format(var,year1,year2)
print(f'Writing to netCDF file {outfile}')
ryf.to_netcdf(outfile, encoding=encdict)

# Open the file again directly with the netCDF4 library to change the calendar attribute. xarray
# has a hissy fit as this violates it's idea of CF encoding if it is done before writing the file above
ryf = nc.Dataset(outfile, mode="r+")
ryf.variables["time"].calendar = "noleap"
ryf.close()
