"""
Author: Clint Morris

Synthetic Parallel Collection:
This tool was developed to systematically download data in parallel.
It can be applied to cases where more efficient web-crawlers are not applicable.
"""
import os
import pandas as pd
from src.constants import *
import time
from src import synthetic_parallel_selenium

# set working dir
os.chdir(WORKING_DIR)
# load dict of stations and transpose to df
map_ = load_obj('map')
del map_['would_not_load']
del map_['loaded_not_a_name']
vds_df = pd.DataFrame(map_, index=['vds_station_number']).T
# set number of drivers, load them on a test page required.
number_of_workers = 4
download_directories, driver_dictionary = synthetic_parallel_selenium.initialize_drivers(number_of_workers)
# optional sleep to allow all drivers to fully load before scraping
time.sleep(10)
synthetic_parallel_selenium.main(download_directories, driver_dictionary, move_files=False, prev_vds=False)