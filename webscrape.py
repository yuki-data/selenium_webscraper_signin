from bs4 import BeautifulSoup
import time
import urllib.parse
from pathlib import Path
import random
import os
import re
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CustomWebdriver:
    _template_arg_path_userdata = "user-data-dir={path_to_profile}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()
        if exc_type is not None:
            print("エラー内容:", exc_value)

    def __init__(self, chromedriver_path, path_to_profile=None, is_headless=False, implicit_wait=5):
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


def wait_for_element(driver, element_id, wait_time=10):
    WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.ID, element_id)))


class ScreenShot:
    def __init__(self, driver, filename=None, relative_url=None, minimum_wait_time=3,
                 path_to_directory=os.getcwd(), target_selector="body"):
        self.relative_url = relative_url
        self._filename = filename
        self.driver = driver
        self._minimum_wait_time = minimum_wait_time
        self._path_to_directory = path_to_directory
        self._target_selector = target_selector

        self._validate_args()

    def _validate_args(self):
        if not(self.relative_url or self._filename):
            raise ValueError("relative_url or filename must be given")

    def run(self):
        self._move_to_url()
        self._preprocess()
        self._screenshot()
        self._postprocess()

    def _move_to_url(self):
        if self.relative_url:
            move_to_url(self.driver, self.relative_url, wait_time=(self._minimum_wait_time + 2 * random.random()))
        else:
            time.sleep(self._minimum_wait_time + 2 * random.random())

    def _preprocess(self):
        if not self._filename:
            self._filename = _ScreenShotPreprocess.make_filename(self.relative_url)

        self._path_to_img = _ScreenShotPreprocess.build_path_to_file(self._filename,
                                                                     self._path_to_directory,
                                                                     extension=".png")
        self._target_element = _ScreenShotPreprocess.get_target_element(self.driver, self._target_selector)

        self._path_to_raw_text = _ScreenShotPreprocess.build_path_to_file(self._filename,
                                                                          self._path_to_directory,
                                                                          extension=".txt")
        self._path_to_html = _ScreenShotPreprocess.build_path_to_file(self._filename,
                                                                      self._path_to_directory,
                                                                      extension=".html.txt")

    def _screenshot(self):
        page_width = self.driver.execute_script('return document.body.scrollWidth')
        page_height = self.driver.execute_script('return document.body.scrollHeight')
        self.driver.set_window_size(page_width, page_height)
        self._target_element.screenshot(self._path_to_img)

    def _postprocess(self):
        target_soup = _ScreenShotPostprocess.get_target_soup(self.driver.page_source, self._target_selector)
        _ScreenShotPostprocess.save_raw_text(raw_text=target_soup.text,
                                             path_to_file=self._path_to_raw_text,
                                             extension=".txt")

        soup = BeautifulSoup(self.driver.page_source, "lxml")
        html = soup.prettify()
        _ScreenShotPostprocess.save_raw_text(raw_text=html,
                                             path_to_file=self._path_to_html,
                                             extension=".html.txt")


class _ScreenShotPreprocess:
    @staticmethod
    def make_filename(relative_url):
        page = re.search(r"\d{3,6}", relative_url).group(0)
        return page

    @staticmethod
    def build_path_to_file(filename, path_to_directory, extension=".png"):
        path_to_file = Path(path_to_directory).joinpath(filename).with_suffix(extension)
        return str(path_to_file)

    @staticmethod
    def get_target_element(driver, target_selector):
        soup = BeautifulSoup(driver.page_source, "lxml")
        if target_selector and soup.select_one(target_selector):
            return driver.find_element_by_css_selector(target_selector)
        else:
            return driver.find_element_by_css_selector("body")


class _ScreenShotPostprocess:
    @staticmethod
    def get_target_soup(page_source, target_selector):
        soup = BeautifulSoup(page_source, "lxml")
        target_soup = soup.select_one(target_selector)
        if target_soup:
            return target_soup
        else:
            return soup.select_one("body")

    @staticmethod
    def save_raw_text(raw_text, path_to_file, extension=".png"):
        with open(path_to_file, "w") as f:
            f.write(raw_text)


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

    def get_screenshot(self, filename, path_to_directory, landmark_elemend_id, wait_time=10):
        with CustomWebdriver(
                is_headless=False,
                chromedriver_path=self._config["chrome"]["chromedriver_path"],
                path_to_profile=self._config["chrome"]["profile_path"]) as custom_driver:
            driver = custom_driver.driver
            self._login(driver)
            wait_for_element(driver, element_id=landmark_elemend_id, wait_time=wait_time)
            save_screenshot(driver, filename, path_to_directory)
