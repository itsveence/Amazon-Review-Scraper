# Import necessary libraries and modules
import time
from datetime import datetime
import warnings
import re

import pandas as pd
import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome
from undetected_chromedriver import ChromeOptions
from selenium.webdriver import Firefox
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from typing import List

import scraper.constants as const

warnings.simplefilter(action='ignore', category=Warning)


class Scraper(Firefox):
    def __init__(self, teardown=False, headless=True):
        # self.options = ChromeOptions()
        # self.options.headless = headless
        self.teardown = teardown

        super(Scraper, self).__init__(
            # options=self.options,
            # use_subprocess=True,
            # driver_executable_path="chromedriver.exe",
        )

        self.implicitly_wait(1)

    def land_first_page(self):

        self.get(const.BASE_URL)

        self.find_element(By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']").click()



        WebDriverWait(self, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[id='a-autoid-3-announce']"))
        )

        click_ = self.find_element(By.CSS_SELECTOR, "span[id='a-autoid-3-announce']")

        self.execute_script("arguments[0].scrollIntoView(true);", click_)
        click_.click()

        WebDriverWait(self, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[id='sort-order-dropdown_1']"))
        )

        click_sort = self.find_element(By.CSS_SELECTOR, "a[id='sort-order-dropdown_1']")
        self.execute_script("arguments[0].click();", click_sort)

        WebDriverWait(self, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[id='a-autoid-4-announce']"))
        )

        click_review = self.find_element(By.CSS_SELECTOR, "span[id='a-autoid-4-announce']")

        self.execute_script("arguments[0].click();", click_review)

        WebDriverWait(self, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[id='reviewer-type-dropdown_1']"))
        )

        review = self.find_element(By.CSS_SELECTOR, "a[id='reviewer-type-dropdown_1']")
        self.execute_script("arguments[0].click();", review)

        self.refresh()


    def locate_date(self, date_string: str = const.START_DATE):

        while True:
            try:
                # Find all review elements
                reviews = self.find_elements(By.CSS_SELECTOR,"div[data-hook='review']")
                # print("Done")
                print(f"Found {len(reviews)} reviews.")

                # Iterate over reviews and check the date
                for review_index in range(len(reviews)):
                    is_verified = reviews[review_index].find_element(By.CSS_SELECTOR, "div[class='a-row a-spacing-mini review-data review-format-strip']").find_elements(By.CSS_SELECTOR, "a")[-1].find_element(By.CSS_SELECTOR, "span[data-hook='avp-badge']").text == "Verified Purchase"

                    if self.check_date(reviews[review_index], date_string) and is_verified:

                        return reviews[review_index:]

                rev = self.next_review_page(reviews)
                if rev is None:
                    print("no rev")
                    break
                print("Done")

            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def get_verified_reviews(self, reviews: List[WebElement]):
        verified_reviews = []
        if reviews:
            for review_index in range(len(reviews)):  # Directly iterate over elements.
                try:
                    is_verified_element = reviews[review_index].find_element(By.CSS_SELECTOR,
                                                              "div[class='a-row a-spacing-mini review-data review-format-strip']"
                                                              ).find_elements(By.CSS_SELECTOR, "a")[-1].find_element(
                        By.CSS_SELECTOR, "span[data-hook='avp-badge']")

                    is_verified = is_verified_element.text == "Verified Purchase"
                    if is_verified:
                        profile_link_element = reviews[review_index].find_element(By.CSS_SELECTOR, "a[class='a-profile']")
                        verified_reviews.append(profile_link_element.get_attribute('href'))

                except NoSuchElementException as e:
                    print(f"Element not found: {e}")
                except Exception as e:
                    print(f"An error occurred: {e}")

            return verified_reviews
        else:
            print("Review list empty")

    def next_review_page(self, reviews):
        # Click on the next page

        next_page_btn = \
            self.find_element(By.CSS_SELECTOR, "ul[class='a-pagination']").find_elements(By.CSS_SELECTOR, "li")[-1]
        self.execute_script("arguments[0].scrollIntoView(true);", next_page_btn)
        next_page_btn.click()
        # self.execute_script("arguments[0].click();", next_page_btn)
        try:
            # Wait for the next page to load
            WebDriverWait(self, 5).until(
                EC.staleness_of(next_page_btn)
            )

            WebDriverWait(self, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-hook='review']"))
            )

            reviews = self.find_elements(By.CSS_SELECTOR, "div[data-hook='review']")

            return reviews
        except TimeoutException as e:
            print("No more reviews on this product")
            return None

    def str_date(self, date_string: str, return_string=False):
        date_format = "%d-%m-%Y"
        review_date_format = "%B %d, %Y"
        try:
            date_object = datetime.strptime(date_string, date_format).date()

        except:
            date_object = datetime.strptime(date_string, review_date_format).date()

        if return_string:
            return date_object.strftime("%d/%m/%Y")
        else:
            return date_object



    def check_date(self, review: WebElement, date_string: str = const.START_DATE):


        # Convert the input string to a datetime object
        date_object = self.str_date(date_string)

        review_date_string = review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text.split("on ")[-1]
        review_date_object = self.str_date(review_date_string)

        date_checked = review_date_object <= date_object

        if date_checked:
            print(f"Review Date: {review_date_string}")

        return date_checked

    def open_link(self, url):

        self.get(url)

    def get_customer_name(self):

        WebDriverWait(self, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[class='a-size-extra-large card-title']"))
        )

        return self.find_element(By.CSS_SELECTOR, "span[class='a-size-extra-large card-title']").text

    def get_customer_purchases(self) -> List[str]:
        purchases = [purchase.find_element(By.CSS_SELECTOR, "a").get_attribute("href") for purchase in self.find_elements(By.CSS_SELECTOR, "div[class='your-content-card-wrapper  your-content-card-desktop']")]
        return purchases

    def extract_review_details_from_purchase(self, purchase: str):
        self.execute_script("window.open('');")
        # Switch to the new window
        self.switch_to.window(self.window_handles[-1])
        self.open_link(purchase)

        info_dict = {}

        if self.str_date(self.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text.split("on ")[-1]) > self.str_date(const.START_DATE):
            self.close()

            # Switch back to the original window
            self.switch_to.window(self.window_handles[-1])

            return None

        date_string = self.str_date(self.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text.split("on ")[-1], return_string=True)
        review_title = self.find_element(By.CSS_SELECTOR, "a[data-hook='review-title']").find_elements(By.CSS_SELECTOR, "span")[-1].text
        review_text = self.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").find_element(By.CSS_SELECTOR, "span").text
        try:
            if self.find_element(
                        By.CSS_SELECTOR, "span[data-hook='avp-badge']").text == "Verified Purchase":
                verified_review = "Y"
            else:
                verified_review = "N"

        except:
            verified_review = "N"

        # print(verified_review)

        info_dict["date"] = date_string
        info_dict["review_title"] = review_title
        info_dict["review_text"] = review_text
        info_dict["verified_review"] = verified_review

        product_link = self.find_element(By.CSS_SELECTOR, "a[data-hook='product-link']").get_attribute("href")
        product_info_dict = self.extract_product_details_from_purchase(product_link)
        info_dict.update(product_info_dict)
        self.close()

        # Switch back to the original window
        self.switch_to.window(self.window_handles[-1])

        return info_dict


    def extract_product_details_from_purchase(self, product: str):
        self.execute_script("window.open('');")
        # print("open new window")
        self.switch_to.window(self.window_handles[-1])
        self.open_link(product)
        # print(product)

        info_dict = {
            "product_name": self.extract_product_name(),
            "categoryfirst_breadcrumb": "",
            "allbreadcrumbs": "",
            "price": self.extract_price(),
            "product_link": product
        }

        breadcrumbs, info_dict["categoryfirst_breadcrumb"], info_dict["allbreadcrumbs"] = self.extract_breadcrumbs()
        self.close()
        # print(info_dict["product_name"])
        # print(info_dict["allbreadcrumbs"])
        # print(info_dict["categoryfirst_breadcrumb"])
        self.switch_to.window(self.window_handles[-1])

        return info_dict

    def extract_product_name(self):
        selectors = [
            "span[id='productTitle']",
            "div[class='sc-iMfspA sc-itboUC ghwsWj iiaLFA']",
            "img[class='ljcPsM']",
            "h1[class='p-jAFk Qo+b2C']"
        ]
        for selector in selectors:
            try:
                if selector[:3] == "img":
                    return self.find_element(By.CSS_SELECTOR, selector).get_attribute("alt")
                else:
                    return self.find_element(By.CSS_SELECTOR, selector).text
            except:
                print("Error extracting product title.. Changing Selector")
        return ""  # Or some default value, or raise an exception

    def extract_breadcrumbs(self):
        breadcrumb_sets = [
            (
                "ul[class='a-unordered-list a-horizontal a-size-small'] a[class='a-link-normal a-color-tertiary']",
                False
            ),
            (
                "div[class='sc-blLsxD ggTjUZ undefined '] div[class='sc-iMfspA bdNMQs']",
                False
            ),
            (
                "div[class='I0iH2G'] a[class='_1NNx6V']",
                False
            )
        ]

        for breadcrumbs_selector, is_direct_text in breadcrumb_sets:
            try:
                breadcrumbs = self.find_elements(By.CSS_SELECTOR, breadcrumbs_selector)
                category_first_breadcrumb = breadcrumbs[0].text
                all_breadcrumbs = ", ".join([b.text for b in breadcrumbs[1:]])
                return breadcrumbs, category_first_breadcrumb, all_breadcrumbs
            except:
                print("Unable to find breadcrumbs... Changing selector")

        return None, "", ""  # Or raise an exception

    def extract_price(self):
        try:
            price = self.execute_script(
                "return document.querySelector(\"div[id='centerCol'] span[class='a-offscreen']\").textContent;")

        except:
            price = 'no price'

        # print(price)

        return price













