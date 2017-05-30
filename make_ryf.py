import xarray
import os
import datetime
from glob import glob
from calendar import isleap

jradir = '/g/data1/ua8/JRA55-do/v1-1/'
# variables = ['q_10', 'rain', 'rlds', 'rsds', 'slp', 'snow', 't_10', 'u_10', 'v_10', 'runoff_all' ]
# variables = ['runoff_all' ]
variables = ['u_10']

years = (1984, 1990, 2003)
# years = (2003,)
# years = (1984,)

FillValue = -9.99e34

# loop over years
for year1 in years:

    # By default the second half of year1 is stitched into first half of year2
    year2 = year1 + 1

    # If second year is a leap year swap years
    if isleap(year2):
        baseyear = year1
        timeslice1 = slice(datetime.datetime(year1, 1, 1, 0, 0),datetime.datetime(year1, 4, 30, 23, 59))
        # Take one less day in this slice, to account for the leap day
        timeslice2 = slice(datetime.datetime(year2, 1, 1, 0, 0),datetime.datetime(year2, 4, 29, 23, 59))
    else:
        baseyear = year2
        timeslice1 = slice(datetime.datetime(year1, 5, 1, 0, 0),datetime.datetime(year1, 12, 31, 23, 59))
        timeslice2 = slice(datetime.datetime(year2, 5, 1, 0, 0),datetime.datetime(year2, 12, 31, 23, 59))

    print "Stitching end of {} to {}".format(year1,year2)

    ds = {}

    for var in variables: 
        print var
        for y in (year1, year2):
            files = glob(os.path.join(jradir,"{}.{}.*.nc".format(var,y)))
            print "Loading {} for {}".format(files[0],y)
            ds[y] = xarray.open_dataset(files[0],decode_coords=False)

        # Make a copy of the second year without time_bnds
        ryf = ds[baseyear].drop("time_bnds")

        for varname in ryf.data_vars:
            # Have to give all variables a useless FillValue attribute, otherwise xarray
            # makes it NaN and MOM does not like this
            if '_FillValue' not in ryf[varname].encoding: ryf[varname].encoding['_FillValue'] = FillValue

            # Only process variables with 3 or more dimensions
            if len(ryf[varname].shape) < 3: continue

            print "Processing ",varname
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
            print dim, ryf[dim].encoding

        ryf.to_netcdf("RYF.{}.{}_{}.nc".format(var,year1,year2))
