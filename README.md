## Generate RYF data files

This script generates RYF data files for the ERA-5 forcing.

To run, do:

python3 make_ryf_loop.py

make_ryf_loop.py submits a single cpu job for each ERA-5 variable
using the submission script make_ryf.sub. For each variable this calls
the script make_ryf.py.
