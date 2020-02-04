from bs4 import BeautifulSoup
import time
import urllib.parse
from pathlib import Path
from selenium import webdriver
import random
import os
import yaml


class CustomWebdriver:
    _template_arg_path_userdata = "user-data-dir={path_to_profile}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()
        if exc_type is not None:
            print("エラー内容:", exc_value)

    def __init__(self, chromedriver_path, path_to_profile=None, is_headless=False, implicit_wait=0):
        self._option = webdriver.ChromeOptions()
        self._path_to_profile = path_to_profile
        self._chromedriver_path = chromedriver_path
        paths = [self._path_to_profile, self._chromedriver_path]
        self._validate_path(paths)
        self._set_profile(path_to_profile)
        self._headless(is_headless)
        self.driver = self._initialize_webdriver(
            self._chromedriver_path, self._option)
        if implicit_wait > 0:
            self.driver.implicitly_wait(implicit_wait)

    def _set_profile(self, path_to_profile):
        if not path_to_profile:
            return
        arg_path_userdata = self._template_arg_path_userdata.format(
            path_to_profile=path_to_profile)
        self._option.add_argument(arg_path_userdata)

    def _headless(self, is_headless):
        if is_headless:
            self._option.add_argument('--start-maximized')
            self._option.add_argument('--headless')

    def quit(self):
        self.driver.quit()

    @staticmethod
    def _initialize_webdriver(executable_path, option):
        driver = webdriver.Chrome(
            executable_path=executable_path, options=option)
        return driver

    @staticmethod
    def _validate_path(paths):
        for path in paths:
            if path is None:
                continue
            if not Path(path).exists():
                raise FileNotFoundError


class Form:
    def input_text(self, driver, selector, value):
        input_feild = self.get_elem(driver.page_source, selector)
        assert input_feild.name == "input"
        driver.find_element_by_css_selector(selector).send_keys(value)

    def submit(self, driver, selector, click_to_submit=True):
        form_feild = self.get_elem(driver.page_source, selector)
        assert form_feild
        elem = driver.find_element_by_css_selector(selector)
        if click_to_submit:
            elem.click()
        else:
            elem.submit()

    def get_elem(self, page_source, selector):
        soup = BeautifulSoup(page_source, "lxml")
        return soup.select_one(selector)


def search_links(page_source, keyword):
    soup = BeautifulSoup(page_source, "lxml")
    links = soup.find_all('a')
    available_links = []
    for link in links:
        href = link.attrs.get("href")
        if href and (keyword in href):
            available_links.append(href)
    return available_links


def navigate_to_course(driver, navbar_id="course_navigation", item_selector=".course-item a", course_name="基礎", time_to_wait=0.5):
    elem = driver.find_element_by_css_selector(item_selector)
    if not elem.is_displayed():
        driver.find_element_by_id(navbar_id).click()
        time.sleep(time_to_wait)
    for elem in driver.find_elements_by_css_selector(item_selector):
        if course_name in elem.text:
            elem.click()
            break
    else:
        raise ValueError("リンクを見つけ出せません")


def move_to_url(driver, url, wait_time=3):
    parsed = urllib.parse.urlparse(driver.current_url)
    base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed)
    absolute_url = urllib.parse.urljoin(base_url, url)
    driver.get(absolute_url)
    time.sleep(wait_time)


def save_screenshot(driver, filename=None, path_to_directory=os.getcwd()):
    if not filename:
        filename = driver.title + "_" + \
            urllib.parse.urlparse(driver.current_url).path.replace("/", "_")
    path = Path(path_to_directory).joinpath(filename).with_suffix(".png")
    page_width = driver.execute_script('return document.body.scrollWidth')
    page_height = driver.execute_script('return document.body.scrollHeight')
    driver.set_window_size(page_width, page_height)
    driver.save_screenshot(str(path))


def screenshot_urls(driver, urls, path_to_directory, minimum_wait_time=3):
    for url in urls:
        move_to_url(driver, url, wait_time=(
            minimum_wait_time + 2 * random.random()))
        save_screenshot(driver, path_to_directory=path_to_directory)


class Scraper:
    def __init__(self, path_to_config, is_headless=False):
        self._config = self._load_config(path_to_config)
        self._is_headless = is_headless

    def _load_config(self, path_to_config):
        path = Path(path_to_config)
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _login(self, driver):
        driver.get(self._config["login"]["url"])
        Form().input_text(driver,
                          self._config["login"]["selector"]["mail"],
                          self._config["secret"]["mail"])
        Form().input_text(driver,
                          self._config["login"]["selector"]["password"],
                          self._config["secret"]["password"])
        Form().submit(driver, self._config["login"]["selector"]["signin"])

    def get_screenshot(self, filename, path_to_directory):
        with CustomWebdriver(
                is_headless=False,
                chromedriver_path=self._config["chrome"]["chromedriver_path"],
                path_to_profile=self._config["chrome"]["profile_path"]) as custom_driver:
            driver = custom_driver.driver
            self._login(driver)
            save_screenshot(driver, filename, path_to_directory)
