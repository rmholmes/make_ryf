## Generate RYF data files

Then run the following to create the May-May repeat year forcings

```bash
for var in msdwswrf msdwlwrf crr lsrr msr msl 2t 2d sp 10u 10v
do
  qsub -vyear=1990,var=${var} make_ryf.sub 
done
```

