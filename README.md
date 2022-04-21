## Generate RYF data files

First start up an interactive job on Gadi to get enough memory:

```bash
qsub -I -X -P v45 -q express -l mem=32GB -l storage=gdata/hh5+gdata/e14+gdata/ik11+gdata/rt52
```

Then run the following to create the May-May repeat year forcings

```bash
module use /g/data3/hh5/public/modules
module load conda/analysis3

python make_ryf.py
```

