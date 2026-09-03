from netCDF4 import Dataset
import pandas as pd
from pathlib import Path

# Path to where the data folder is located
data_path: Path = Path("data")

# Read netCDF files, create dataframes and export to csv
for file in data_path.glob("*.nc"):
    rootgrp = Dataset(file, "r")
    df = pd.DataFrame({varname: rootgrp.variables[varname][:] for varname in rootgrp.variables})
    rootgrp.close()
    
    # Export to csv
    df.to_csv(data_path / f"{file.stem}.csv", index=False)
    
    print(f"Exported {file.stem}.csv")
