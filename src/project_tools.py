import os
import pickle
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from termcolor import colored
import time

def save_obj(obj, file_name):
    if not os.path.exists('obj/'):
        os.makedirs('obj/')
    with open('obj/'+ file_name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(file_name):
    with open('obj/' + file_name + '.pkl', 'rb') as f:
        return pickle.load(f)

def interact(driver,xpath,click=True,delay=2,count=100,status_rate=1):
    r,i = None,0
    while r is None:
        try:
            r = driver.find_element_by_xpath(xpath)
            if click:
                r.click()
                return True
            else:
                return r
        except (NoSuchElementException, ElementNotInteractableException) as e:
            if i > count:
                return None
            i += 1
            time.sleep(delay)
            if i % status_rate == 0:
                print(colored('Searching for item...', 'red'))

