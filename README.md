# GINCCO_lib

Utilities for:
- Reading SYMPHONIE output model
- Opening multiple files along time  
- Post-processing
- Data visualization

---

## 🚀 Installation (from GitHub)

```bash
# Create environment
conda create -n gincco_test2 python=3.7

# Activate environment
conda activate gincco_test2

# Install dependencies
conda install numpy scipy netcdf4
conda install matplotlib 
conda install basemap

# Install GINCCO_lib
pip install git+https://github.com/duytung/GINCCO_lib.git

# Optional: make video from outputs
pip install imageio[ffmpeg] imageio[pyav] pillow

# To update the library
pip install --force-reinstall --no-deps "git+https://github.com/duytung/GINCCO_lib.git"

```

## Documentation

https://gincco-lib.readthedocs.io/


## Acknowledgememt

If you publish results for which you have used the GINCCO library, please add a sentence such as the following in the acknowledgments: "GINCCO_lib has been developed by Duy Tung Nguyen (HUS, VNU) with the support of the GINCCO project (https://www.legos.omp.eu/gincco/)