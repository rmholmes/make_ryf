# /usr/bin/env python3
import os

variables = ['msdwswrf','msdwlwrf','crr','lsrr','msr','msl','2t','2d','sp','10u','10v']

for var in variables:
    os.system('qsub -v var="XXNAMEXX" make_ryf.sub'.replace('XXNAMEXX',var))            
                    
