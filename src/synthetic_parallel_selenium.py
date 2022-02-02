import datetime
import glob
import os
import shutil
import time
import pyautogui
from selenium import webdriver
from termcolor import colored
from src.constants import *
from src.project_tools import interact


def download_csv(dict_drivers, vds_num, driver2dates, driver_dex):
    """ Collect data from a select webdriver.
    Args:
        dict_drivers (dict): web-driver dict.
        vds_num (int): vds id values.
        driver2dates (dict): dict containing data.
        driver_dex (int): index of target driver.
    return:
        driver2dates (dict): dict containing data.
    """
    # search for the banner first, it's html is only there after the data loads.
    banner = interact(dict_drivers[driver_dex], SERVER_INFO['banner'], click=False, delay=0.3, count=2, status_rate=5)
    if not banner:
        return False
    ret = interact(dict_drivers[driver_dex], '//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_ButtonLink"]', click=True,
                   delay=0.7, count=200)
    ret1 = interact(dict_drivers[driver_dex], '//*[@id="ReportViewerControl_ctl05_ctl04_ctl00_Menu"]/div[2]/a',
                    click=True, delay=0., count=200)
    missed_stations = []
    if not ret or not ret1:
        missed_stations.append(f'{vds_num}')
        print(f'Missed: {vds_num}')
        return driver2dates
    print(colored('Downloaded: ', None), colored(f'vds: {vds_num}  dates: {driver2dates[driver_dex]}', 'green'))
    driver2dates[driver_dex] = None


def generate_url(vds_id, start_date, end_date):
    """ Generates url to avoid interfacing with slow UI.
    Args:
        vds_id (str): vds id values.
        start_date (str): "%Y-%m-%d" start date.
        end_date (str): "%Y-%m-%d" end date.
    return:
        output_url (str): url to the datapage.
    """
    output_url = SERVER_INFO['template_url0']
    for i, (var) in enumerate([vds_id, start_date, end_date]):
        output_url = output_url + str(var) + SERVER_INFO[f'template_url{i + 1}']
    return output_url


def file_mover(download_dirs, prev_vds, i=0):
    """ Organize the downloaded data.
    Args:
        download_dirs (list): list of download locations.
        prev_vds (str): id of previous station.
        i (int): start value.
    """
    allfiles = []
    if not os.path.exists(f'{WORKING_DIR}/data/{prev_vds}'):
        os.mkdir(f'{WORKING_DIR}/data/{prev_vds}')
    for path in download_dirs:
        allfiles = allfiles + glob.glob(f'{path}/*')
    while len(allfiles) > 0:
        newset = allfiles
        for file in newset:
            try:
                shutil.move(file, f'{WORKING_DIR}/data/{prev_vds}/{prev_vds}_{i}.csv')
                allfiles.remove(file)
                i += 1
            except PermissionError:
                continue  # work around if the file is downloading


def generate_date_intervals(period, count, start='2019-07-31'):
    """ Generates dates interval for collection. """
    intervals = {}
    # period: days in each segment count: number of periods
    for val in range(count):
        date_1 = datetime.datetime.strptime(start, "%Y-%m-%d")
        end = date_1 + datetime.timedelta(days=period)
        end = end.strftime("%Y-%m-%d")
        # number to date interval
        intervals[val + 1] = [start, end]
        start = end
    return intervals


def initialize_drivers(worker_count):
    """ Initialize drivers. """
    dload_dirs, dict_drivers = [], {}
    url = generate_url('4101', '2021-01-14', '2021-01-14')
    for idx in range(worker_count):
        download_dir = f'{WORKING_DIR}/data/vds_dump_worker' + str(idx)
        if not os.path.exists(download_dir):
            dload_dirs.append(download_dir)
            os.mkdir(download_dir)
        options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': DOWNLOAD_DIR + str(idx)}
        options.add_experimental_option('prefs', prefs)
        # load a test pg
        dict_drivers[idx] = webdriver.Chrome(chrome_options=options)  # each worker has its own download dir
        dict_drivers[idx].get(url)

        # inelegant approach to entering pass and username, xpath was not an option here because
        # there is a apache httpd .htaccess username and password that the driver cannot act on by traditional means
        time.sleep(3)
        for input_, action_ in zip(['username', 'password'], ['tab', 'enter']):
            time.sleep(0.5)
            pyautogui.write(PRIVATE_INFO[input_])
            pyautogui.press(action_)
    return dload_dirs, dict_drivers


def main(download_dirs, drivers, vds_df, move_files=False, prev_vds=None):
    """ Main collection function that cycles through drivers to download data in parallel.
    Args:
        download_dirs (list): List of download locations.
        drivers (dict): Dictionary of web-drivers.
        vds_df (DataFrame): Df of target locations.
        move_files (bool): Move files to organize.
        prev_vds (None): Used to continue from a point in the list.
    """
    driver2dates = {}
    intervals = generate_date_intervals(10, 37)
    for vds in vds_df.iterrows():
        start_time = time.time()
        vds_name, vds_num = vds[0], vds[1][0]
        print(f'{vds_name}  -----  {vds_num}')
        # reset values
        for idx in range(len(drivers.keys())):
            driver2dates[idx] = None
        # list [1-37] related to the dates sections of 10 days or 370 day (more than target one year)
        dates_not_downloaded = [x + 1 for x in range(37)]
        while len(dates_not_downloaded) > 0:
            # if one worker has downloaded its file, this loop will assign it the next url
            for driver_dex, date_num in driver2dates.items():
                if not date_num:
                    # assign next in list
                    if len(dates_not_downloaded) > 0:
                        new_date_num = dates_not_downloaded.pop(0)
                    else:
                        continue
                    driver2dates[driver_dex] = new_date_num
                    # this loops generates url from parts. match url enumerate([vds_num, start, end])
                    url = generate_url(vds_num, intervals[new_date_num][0], intervals[new_date_num][1])
                    drivers[driver_dex].get(url)
            # this is nested but only acts after the first loop this is
            # done to provide additional download it with limited time cost.
            if move_files:
                file_mover(download_dirs, prev_vds, i=0)
                move_files = False
            # if all workers have a current url to process this loops until at least one completes a job
            while None not in driver2dates.values():
                for driver_dex in drivers.keys():
                    download_csv(drivers, vds_num, driver2dates, driver_dex)
        # the last three are not covered by the previous double loop for matted like [x, y, None, z]
        while any(driver2dates.values()):
            for driver_dex, ret in driver2dates.items():
                if ret:
                    # this loops generates url from parts. match url enumerate([vds_num, start, end])
                    download_csv(drivers, vds_num, driver2dates, driver_dex)
        move_files, prev_vds = True, vds_num  # to trigger files from being moved from dumps to organized folder
        end_time = time.time()
        print(colored('Loop-speed: ', None), colored(f'{end_time - start_time}', 'red'))

