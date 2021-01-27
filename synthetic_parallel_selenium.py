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


def download_csv(drivers, vds_num, server_info, driver2dates, driver_dex):
    # search for the banner first, it's html is only there after the data loads.
    # However, you can click the download buttom before, so the banner must be found first.
    banner = interact(drivers[driver_dex], server_info['banner'], click=False, delay=0.3, count=2, status_rate=5)
    if banner == None:
        return False
    ret = interact(drivers[driver_dex], '//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_ButtonLink"]', click=True,
                   delay=0.7, count=200)
    ret1 = interact(drivers[driver_dex], '//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_Menu"]/div[2]/a', click=True,
                    delay=0., count=200)
    if ret == None or ret1 == None:
        missed_stations.append(f'{vds_num}')
        print(f'Missed: {vds_num}')
        return driver2dates
    print(colored('Downloaded: ', None), colored(f'vds: {vds_num}  dates: {driver2dates[driver_dex]}', 'green'))
    driver2dates[driver_dex] = None


# set working dir
working_dir = 'H:/UGA MASTERS/VDS_CCS_Project'
os.chdir(working_dir)

from project_tools import load_obj, interact, save_obj

# this is a data set collected from vds-info-scrape-gui-interact
info = load_obj('info')
cols = list(pd.read_csv('support//inventory_xpath.csv').names)  # columns
info = pd.DataFrame(info)  # refromat to df
info = info.T
info.columns = cols

# load passwords
private_info = load_obj('private_info')
# load server info
server_info = load_obj('server_info')

# tmp url
url = server_info['template_url0'] + server_info['template_url1'] + server_info['template_url2'] + server_info[
    'template_url3']
vds_id = '4101'
start_date = '2021-01-14'
end_date = '2021-01-14'
url = server_info['template_url0']
for i, (var) in enumerate([vds_id, start_date, end_date]):
    url = url + str(var) + server_info[f'template_url{i + 1}']

# set number of drivers, load them on a test page required.
number_of_workers = 6
download_dirs = []
drivers = {}
for idx in range(number_of_workers):
    download_dir = f'{working_dir}/data/vds_dump_worker' + str(idx)
    if not os.path.exists(download_dir):
        download_dirs.append(download_dir)
        os.mkdir(download_dir)
    options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': r'H:\UGA MASTERS\VDS_CCS_Project\data\vds_dump_worker' + str(idx)}
    options.add_experimental_option('prefs', prefs)
    # load a test pg
    drivers[idx] = webdriver.Chrome(chrome_options=options)  # each worker has its own download dir
    drivers[idx].get(url)

    # inelegant approach to entering pass and username, xpath was not an option here because
    # there is a apache httpd .htaccess username and password that the driver cannot act on by traditional means
    time.sleep(3)
    for input_, action_ in zip(['username', 'password'], ['tab', 'enter']):
        time.sleep(0.5)
        pyautogui.write(private_info[input_])
        pyautogui.press(action_)

# optional sleep to allow all drivers to fully load before scraping
time.sleep(10)

# load dict of stations and transpose to df
map_ = load_obj('map')
del map_['would_not_load']
del map_['loaded_not_a_name']
vds_df = pd.DataFrame(map_, index=['vds_station_number']).T

move_files = False

start = '2019-07-31'
intervals = {}
for val in range(37):
    date_1 = datetime.datetime.strptime(start, "%Y-%m-%d")
    end = date_1 + datetime.timedelta(days=10)
    end = end.strftime("%Y-%m-%d")
    # number to date interval
    intervals[val + 1] = [start, end]
    start = end

driver2dates = {}
for vds in vds_df.iterrows():
    start_time = time.time()
    vds_name, vds_num = vds[0], vds[1][0]
    print(f'{vds_name}  -----  {vds_num}')

    # reset
    for idx in range(number_of_workers):
        driver2dates[idx] = None
    # list [1-37] related to dates sections of 10 days or 370 day (more than target one year)
    dates_not_downloaded = [x + 1 for x in range(37)]
    print(driver2dates)
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
                url = server_info['template_url0']
                for idx, (var) in enumerate([vds_num, intervals[new_date_num][0], intervals[new_date_num][1]]):
                    url = url + str(var) + server_info[f'template_url{idx + 1}']
                drivers[driver_dex].get(url)

        # this is nested but only acts after the first loop this is
        # done to provide additional download it with limited time cost.
        if move_files == True:
            i = 0
            for path in download_dirs:
                for file in os.listdir(path):
                    if not os.path.exists(f'{working_dir}/data/{prev_vds}'):
                        os.mkdir(f'{working_dir}/data/{prev_vds}')
                    i += 1
                    shutil.move(f'{path}/{file}', f'{working_dir}/data/{prev_vds}/{prev_vds}_{i}.csv')
            move_files = False  # only happens once every station

        # if all workers have a current url to process this loops until at least one completes a job
        while None not in driver2dates.values():
            for driver_dex in drivers.keys():
                download_csv(drivers, vds_num, server_info, driver2dates, driver_dex)

    # the last three are not covered by the previous double loop for matted like [x, y, None, z]
    while any(driver2dates.values()):
        for driver_dex, ret in driver2dates.items():
            if ret != None:
                # this loops generates url from parts. match url enumerate([vds_num, start, end])
                download_csv(drivers, vds_num, server_info, driver2dates, driver_dex)

    move_files, prev_vds = True, vds_num  # to trigger files from being moved from dumps to organized folder, next loop
    end = time.time()
    print(colored('Loop-speed: ', None), colored(f'{end - start}', 'red'))
