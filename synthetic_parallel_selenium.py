import os, sys, time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import pandas as pd
import datetime
from termcolor import colored
import shutil
import glob


def download_csv(drivers, vds_num ,server_info, driver2dates, driver_dex):
    # search for the banner first, it's html is only there after the data loads.
    # However, you can click the download buttom before, so the banner must be found first.
    banner =  interact(drivers[driver_dex],server_info['banner'],click=False,delay=0.3,count=2,status_rate=5)
    if banner == None:
        return False
    ret = interact(drivers[driver_dex],'//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_ButtonLink"]',click=True,delay=0.7,count=200)
    ret1 = interact(drivers[driver_dex],'//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_Menu"]/div[2]/a',click=True,delay=0.,count=200)
    if ret == None or ret1 == None:
        missed_stations.append(f'{vds_num}')
        print(f'Missed: {vds_num}')
        return driver2dates
    print(colored('Downloaded: ', None),colored(f'vds: {vds_num}  dates: {driver2dates[driver_dex]}', 'green'))
    driver2dates[driver_dex] = None

def generate_url(vds_id, start_date, end_date, server_info):
    url = server_info['template_url0']
    for i, (var) in enumerate([vds_id, start_date, end_date]):
        url = url + str(var) + server_info[f'template_url{i+1}']  
    return url

def file_mover(download_dirs, working_dir, prev_vds, i=0, allfiles=[]):
    if not os.path.exists(f'{working_dir}/data/{prev_vds}'):
        os.mkdir(f'{working_dir}/data/{prev_vds}')
    for path in download_dirs:
        allfiles = allfiles + glob.glob(f'{path}/*')
    while len(allfiles) > 0:
        newset = allfiles
        for file in newset:
            try:
                shutil.move(file,f'{working_dir}/data/{prev_vds}/{prev_vds}_{i}.csv')
                allfiles.remove(file)
                i += 1
            except PermissionError:
                continue # work around if the file is downloading 

def generate_date_intervals(period,count,intervals={},start = '2019-07-31'):
    # period: days in each segment count: number of periods
    for val in range(count):
        date_1 = datetime.datetime.strptime(start, "%Y-%m-%d")
        end = date_1 + datetime.timedelta(days=period)
        end = end.strftime("%Y-%m-%d")
        # number to date interval
        intervals[val+1] = [start,end]
        start = end
    return intervals


# set working dir
working_dir = 'H:/UGA MASTERS/VDS_CCS_Project'
os.chdir(working_dir)
from project_tools import load_obj, interact, save_obj
private_info = load_obj('private_info')
# load server info
server_info = load_obj('server_info')
# load dict of stations and transpose to df
map_ = load_obj('map')
del map_['would_not_load']
del map_['loaded_not_a_name']
vds_df = pd.DataFrame(map_, index=['vds_station_number']).T

# tmp url
url = generate_url('4101', '2021-01-14', '2021-01-14', server_info)
# set number of drivers, load them on a test page required.
number_of_workers = 4

download_dirs = []
drivers = {}
for idx in range(number_of_workers):
    download_dir = f'{working_dir}/data/vds_dump_worker'+str(idx)
    if not os.path.exists(download_dir):
        download_dirs.append(download_dir)
        os.mkdir(download_dir)
    options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : r'H:\UGA MASTERS\VDS_CCS_Project\data\vds_dump_worker'+str(idx)}
    options.add_experimental_option('prefs', prefs)
    # load a test pg
    drivers[idx] = webdriver.Chrome(chrome_options=options) # each worker has its own download dir
    drivers[idx].get(url)

    # inelegant approach to entering pass and username, xpath was not an option here because
    # there is a apache httpd .htaccess username and password that the driver cannot act on by traditional means
    time.sleep(3)
    for input_, action_ in zip(['username','password'],['tab','enter']):
        time.sleep(0.5)
        pyautogui.write(private_info[input_])
        pyautogui.press(action_)
      
    
# optional sleep to allow all drivers to fully load before scraping
time.sleep(10)

move_files = False
intervals = generate_date_intervals(10,37,intervals={})
skip = True
driver2dates = {}


for vds in vds_df.iterrows():
    start_time = time.time()
    vds_name, vds_num = vds[0], vds[1][0] 
    print(f'{vds_name}  -----  {vds_num}')
    
    
    if skip:
        if vds_num == '3176':
            skip = False
        else:
            continue
    
    # reset values
    for idx in range(number_of_workers):
        driver2dates[idx] = None
    # list [1-37] related to dates sections of 10 days or 370 day (more than target one year)
    dates_not_downloaded = [x+1 for x in range(37)]
    

    while len(dates_not_downloaded) > 0:
        # if one worker has downloaded its file, this loop will assign it the next url
        for driver_dex, date_num in driver2dates.items():
            if date_num == None:
                # assign next in list
                if len(dates_not_downloaded) > 0:
                    new_date_num = dates_not_downloaded.pop(0)
                else: 
                    continue 
                driver2dates[driver_dex] = new_date_num
                # this loops generates url from parts. match url enumerate([vds_num, start, end])
                url = generate_url(vds_num, intervals[new_date_num][0],intervals[new_date_num][1], server_info)
                drivers[driver_dex].get(url)
                
        # this is nested but only acts after the first loop this is 
        # done to provide additional download it with limited time cost.
        if move_files == True:
            move_files = file_mover(download_dirs, working_dir, prev_vds, i=0)
            move_files = False
            
        # if all workers have a current url to process this loops until at least one completes a job
        while None not in driver2dates.values():
            for driver_dex in drivers.keys():
                download_csv(drivers, vds_num ,server_info, driver2dates, driver_dex)
    
    # the last three are not covered by the previous double loop for matted like [x, y, None, z]
    while any(driver2dates.values()):
        for driver_dex, ret in driver2dates.items():
            if ret != None:
                # this loops generates url from parts. match url enumerate([vds_num, start, end])
                download_csv(drivers, vds_num ,server_info, driver2dates, driver_dex)
                    
    move_files, prev_vds = True, vds_num # to trigger files from being moved from dumps to organized folder, next loop
    end_time = time.time()
    print(colored('Loop-speed: ', None), colored(f'{end_time-start_time}', 'red'))
