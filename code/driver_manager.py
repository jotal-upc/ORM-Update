"""
 *
 * Copyright (C) 2020 Universitat Politècnica de Catalunya.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at:
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
"""

# -*- coding: utf-8 -*-

# Basic modules
import os
import re
import time
import logging.config
import zlib

# 3rd party modules
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service # Used to define geckodriver bin + log_path in selenium 4.16
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

# Own modules
from utils import utc_now
from data_manager import manage_requests
from session_storage import SessionStorage


# Paths to be used in production server
geckodriver_path = os.path.join(os.path.abspath("."), "../assets/firefox/geckodriver-v0.33.0-linux64/geckodriver")
firefox_path     = os.path.join(os.path.abspath("."), "../assets/firefox/firefox-115.5.0esr/firefox/firefox")

# Hardcoded paths for the virtual machine
# geckodriver_path = "/home/eprivo/Desktop/geckodriver-v0.33.0-linux64/geckodriver"
# firefox_path     = "/home/eprivo/Desktop/firefox-115.5.0esr/firefox/firefox"


COMPLETED = REPEAT = True
FAILED = NO_REPEAT = False

logging.config.fileConfig('logging.conf')

logger = logging.getLogger("DRIVER_MANAGER")


def get_extension_uuid(path, identifier):
    uuid = ""
    with open(path + '/prefs.js') as f:
        for line in f.readlines():
            if re.search('extensions.webextensions.uuids', line):
                for elem in line.split(","):
                    if re.search(identifier, elem):
                        uuid = elem.split(":")[1]
    uuid = uuid.replace("\"", "").replace("\\", "").replace("}", "").replace(")", "").replace(";", "")
    return uuid


def build_driver(plugin, cache, update_ublock, process):
    """ Creates the selenium driver to be used by the script and loads the corresponding plugin if needed. """
    try:
        profile = FirefoxProfile()
        # Disable browser content protection measures
        profile.set_preference("dom.storage.default_quota", 51200)
        profile.set_preference("dom.storage.default_site_quota", 51200)
        profile.set_preference("privacy.trackingprotection.enabled", False)
        profile.set_preference("browser.contentblocking.enabled", False)
        profile.set_preference("browser.contentblocking.category", "standard")
        profile.set_preference("browser.contentblocking.database.enabled", False)
        profile.set_preference("browser.contentblocking.fingerprinting.preferences.ui.enabled", False)
        profile.set_preference("browser.contentblocking.cryptomining.preferences.ui.enabled", False)
        
        # Disable caches and enables private mode for stateless scraps
        if not cache:
            profile.set_preference("browser.cache.disk.enable", False)
            profile.set_preference("browser.cache.memory.enable", False)
            profile.set_preference("browser.cache.offline.enable", False)
            profile.set_preference("network.http.use-cache", False)

        opts = Options()
        opts.profile = profile
        opts.binary_location = firefox_path

        geckodriver_service = Service(executable_path=geckodriver_path,
                                      log_path="log/geckodriver.log")
       
        driver = webdriver.Firefox(service=geckodriver_service,
                                   options=opts)
        
        driver.set_page_load_timeout(60)
    except Exception as e:
        # logger.error(e)
        logger.error("(proc. %d) Error creating driver: %s" % (process, str(e)))
        return FAILED
    try:
        time.sleep(2)
        # Load received plugin (except for vanilla)
        if plugin.values["name"] != "Vanilla":
            plugin_path = os.path.join(os.path.abspath("."), plugin.values["path"])
            driver.install_addon(plugin_path, temporary=True)
            time.sleep(2)
            profile_path = str(driver.capabilities['moz:profile'])
            uuid = get_extension_uuid(profile_path, plugin.values["identifier"])
            if plugin.values['custom'] and update_ublock:
                driver.get(plugin.values['url'].replace("UUID", uuid))
                time.sleep(10)
                try:
                    driver.find_element_by_xpath(plugin.values['xpath_to_click']).click()
                except NoSuchElementException as e:
                    driver.switch_to.frame(0)
                    driver.find_element_by_xpath(plugin.values['xpath_to_click']).click()
                time.sleep(20)
            if plugin.values["background"]:
                driver.get(plugin.values["background"].replace("UUID", uuid))
        return driver
    except Exception as e:
        driver.quit()
        logger.error("(proc. %d) Error creating driver: %s" % (process, str(e)))
        return FAILED


def reset_browser(driver, process, plugin, cache, update_ublock):
    """ Reset the browser to the default state. """

    driver.quit()
    driver = build_driver(plugin, cache, update_ublock, process)
    while not driver:
        driver = build_driver(plugin, cache, update_ublock, process)
    driver.set_page_load_timeout(60)
    return driver


def visit_site(db, process, driver, domain, plugin, temp_folder, cache, update_ublock, geo_db):
    """ Loads the website and extract its information. """

    try:
        blocker_tab_handle = driver.current_window_handle
    except Exception as e:
        logger.error("Error saving uBlock tab: %s (proc. %d)" % (str(e), process))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT
    try:
        driver.execute_script('''window.open();''')
        second_tab_handle = driver.window_handles[-1]
        driver.switch_to.window(second_tab_handle)
    except WebDriverException as e:
        logger.error("WebDriverException (1) on %s / Error: %s (proc. %d)" % (domain.values["name"], str(e), process))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT

    # Load the website and wait some time inside it
    try:
        driver.get('http://' + domain.values["name"])
    except TimeoutException:
        logger.warning("Site %s timed out (proc. %d)" % (domain.values["name"], process))
        driver.close()
        driver.switch_to.window(blocker_tab_handle)
        try:
            storage = SessionStorage(driver)
            storage.clear()
        except NoSuchWindowException as e:
            logger.error("(proc. %d) Error accessing the session storage: %s" % (process, str(e)))
            driver = reset_browser(driver, process, plugin, cache, update_ublock)
        except WebDriverException as e:
            logger.error("(proc. %d) Error clearing session storage: %s" % (process, str(e)))
            driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT
    except WebDriverException as e:
        # logger.warning("WebDriverException (2) on %s / Error: %s (proc. %d)" % (domain.values["name"], str(e), process))
       
        # Remove Stacktrace for readability -- Most of the time this error is launched when visiting
        # a domain with no webpage associated -- The old log message should be used in production
        stacktrace_start = str(e).find("Stacktrace:")
        if stacktrace_start != -1:
            error_str = str(e)[:stacktrace_start].replace('\n','')
        else:
            error_str = str(e)
        logger.warning("WebDriverException (2) on %s / Error: %s (proc. %d)" % (domain.values["name"], error_str, process))
        
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        domain.values["update_timestamp"] = utc_now()
        domain.values["priority"] = 0
        domain.save()
        return driver, FAILED, NO_REPEAT
    except Exception as e:
        logger.error("%s (proc. %d)" % (str(e), process))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        domain.values["update_timestamp"] = utc_now()
        domain.values["priority"] = 0
        domain.save()
        return driver, FAILED, NO_REPEAT
    # Wait some time inside the website
    time.sleep(10)
    os.makedirs(os.path.join(os.path.abspath("."), temp_folder), exist_ok=True)
    filename = os.path.join(temp_folder, domain.values["name"] + 'ss.png')
    driver.save_screenshot(filename)
    size = os.stat(filename).st_size
    compressed_code = None
    if size > 0:
        # Compress the screenshot to save it into the database when needed
        with open(filename, 'rb') as f:
            blob_value = f.read()
            compressed_code = zlib.compress(blob_value)
    os.remove(filename)
    try:
        # Close possible alerts
        finished = False
        while not finished:
            try:
                alert = Alert(driver)
                alert.dismiss()
            except:
                finished = True
        if not cache:
            driver.delete_all_cookies()
        driver.close()
    except WebDriverException as e:
        logger.warning("WebDriverException (3) on %s / Error: %s (proc. %d)" % (domain.values["name"], str(e), process))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT

    # Process traffic from uBlock Origin tab sessionStorage
    try:
        driver.switch_to.window(blocker_tab_handle)
    except Exception as e:
        logger.error("Error accessing uBlock tab: %s (proc. %d)" % (str(e), process))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT
    try:
        storage = SessionStorage(driver)
        web_list = {}
        for key in storage.keys():
            web_list[key] = storage[key]
    except NoSuchWindowException as e:
        logger.error("(proc. %d) Error accessing the session storage: %s" % (process, str(e)))
        driver = reset_browser(driver, process, plugin, cache, update_ublock)
        return driver, FAILED, REPEAT
    else:
        # Insert data and clear storage before opening the next website
        manage_requests(db, process, domain, web_list, plugin, temp_folder, geo_db)
        try:
            storage.clear()
        except WebDriverException as e:
            logger.error("(proc. %d) Error clearing session storage: %s" % (process, str(e)))
            driver = reset_browser(driver, process, plugin, cache, update_ublock)
            return driver, FAILED, NO_REPEAT
    domain.values["update_timestamp"] = utc_now()
    domain.values["priority"] = 0
    if compressed_code:
        domain.values["screenshot"] = compressed_code;
    domain.save()
    return driver, COMPLETED, NO_REPEAT
