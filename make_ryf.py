import xarray
import netCDF4 as nc
import os
import datetime
from glob import glob
from calendar import isleap
import numpy as np

era5dir = '/g/data/rt52/era5/single-levels/reanalysis/'
variables = ['msdwswrf']#,'msdwlwrf','crr','lsrr','msr','msl','mror','2t','2d','sp','10u','10v']
years = [1990]

FillValue = np.int64(1.e20)

# loop over years
for year1 in years:

    # By default the second half of year1 is stitched into first half of year2
    year2 = year1 + 1

    # If second year is a leap year make the "base year" year1 and use time slices from the beginning of the year
    if isleap(year2):
        baseyear = year1
        timeslice1 = slice(datetime.datetime(year1, 1, 1, 0, 0),datetime.datetime(year1, 4, 30, 23, 59))
        # Take one less day in this slice, to account for the leap day
        timeslice2 = slice(datetime.datetime(year2, 1, 1, 0, 0),datetime.datetime(year2, 4, 29, 23, 59))
    else:
        baseyear = year2
        timeslice1 = slice(datetime.datetime(year1, 5, 1, 0, 0),None)
        timeslice2 = slice(datetime.datetime(year2, 5, 1, 0, 0),None)

    ds = {}

    for var in variables:
        print(var)
        for y in (year1, year2):
            files = glob(os.path.join(era5dir,"{v}/{y}/*.nc".format(v=var,y=y)))
            for f in files:
                print("Loading {} for {}".format(f,y))
            ds[y] = xarray.open_mfdataset(files,decode_coords=False)
        # Make a copy of the second year without time_bnds
        ryf = ds[baseyear]
        ryf.encoding = ds[baseyear].encoding

        for varname in ryf.data_vars:
            # Have to give all variables a useless FillValue attribute, otherwise xarray
            # makes it NaN and MOM does not like this
            if '_FillValue' not in ryf[varname].encoding: ryf[varname].encoding['_FillValue'] = FillValue

            # Only process variables with 3 or more dimensions
            if len(ryf[varname].shape) < 3: continue

            print("Processing ",varname)
            if isleap(year2):
                # Set the Jan->Apr values to those from the first year
                ryf[varname].loc[dict(time=timeslice1)] = ds[year2][varname].sel(time=timeslice2).values
            else:
                # Set the May->Dec values to those from the first year
                ryf[varname].loc[dict(time=timeslice2)] = ds[year1][varname].sel(time=timeslice1).values
            # Compress the data?
            # encdir[varname] = dict(zlib=True, shuffle=True, complevel=4)
            # encdict[varname] = dict(contiguous=True)

        for dim in ryf.dims:
            # Have to give all dimensions a useless FillValue attribute, otherwise xarray
            # makes it NaN and MOM does not like this
            ryf[dim].encoding['_FillValue'] = FillValue


        # Make a new time dimension with no offset from origin (1900-01-01) so we don't get an offset after
        # changing calendar to noleap
        newtime = (ryf.indexes["time"].values - ryf.indexes["time"].values[0]) + np.datetime64('1900-01-01','D')
        ryf.indexes["time"].values[:] = newtime[:]

        ryf["time"].attrs = {'modulo':' ',
                     'axis':'T',
                     'cartesian_axis':'T',
                     # 'calendar':'noleap'
        }

        outfile = "RYF.{}.{}_{}.nc".format(var,year1,year2)
        ryf.to_netcdf(outfile)

        # Open the file again directly with the netCDF4 library to change the calendar attribute. xarray
        # has a hissy fit as this violates it's idea of CF encoding if it is done before writing the file above
        ryf = nc.Dataset(outfile, mode="r+")
        ryf.variables["time"].calendar = "noleap"
        ryf.close()
