## Generate RYF data files

Run the following to create the May-May repeat year forcings
for the 1990/91 repeat year for ERA5

```bash
for var in msdwswrf msdwlwrf crr lsrr msr msl 2t 2d sp 10u 10v
do
  qsub -vyear=1990,var=${var} make_ryf.sub 
done
```

