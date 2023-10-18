# Import the necessary constants and classes
import os
import re
import pandas as pd

from scraper.constants import OUT_PATH
from scraper.scraper import Scraper
from selenium.webdriver.common.by import By

# Start the web scraper

bot = Scraper()

bot.land_first_page()

location = bot.locate_date()

verified_reviews = bot.get_verified_reviews(location)

current_page = location

customer_count = 0

customer_count_limit = 2

customer_data = {"Userprofile_url": [],
                             "Username": [],
                             "Reviewdate": [],
                             "Productname": [],
                             "review_title": [],
                             "review_text": [],
                             "categoryfirst_breadcrumb": [],
                             "allbreadcrumbs": [],
                             "price": [],
                             "urlproduct": [],
                             "verified_review": []
                             }

# Creating an empty DataFrame
df = pd.DataFrame(customer_data)


while customer_count < customer_count_limit:
    # print("new customer")
    if verified_reviews is not None:

        for review in verified_reviews:

            customer_data = {"Userprofile_url": [],
                             "Username": [],
                             "Reviewdate": [],
                             "Productname": [],
                             "review_title": [],
                             "review_text": [],
                             "categoryfirst_breadcrumb": [],
                             "allbreadcrumbs": [],
                             "price": [],
                             "urlproduct": [],
                             "verified_review": []
                             }

            # # Creating an empty DataFrame
            # df = pd.DataFrame(customer_data)
            # Open a new window/tab
            bot.execute_script("window.open('');")

            # Switch to the new window
            bot.switch_to.window(bot.window_handles[-1])

            bot.open_link(review)

            customer_name = bot.get_customer_name()

            # print(customer_name)

            customer_count += 1
            print(f"Customer number {customer_count}")
            purchases = bot.get_customer_purchases()
            # try:

            for purchase_index in range(len(purchases)):

                detail_dict = bot.extract_review_details_from_purchase(purchases[purchase_index])
                if detail_dict is None:
                    continue
                customer_data["Userprofile_url"].append(review)
                customer_data["Username"].append(customer_name)
                customer_data["Reviewdate"].append(detail_dict["date"])
                customer_data["Productname"].append(detail_dict["product_name"])
                customer_data["review_title"].append(detail_dict["review_title"])
                customer_data["review_text"].append(detail_dict["review_text"])
                customer_data["categoryfirst_breadcrumb"].append(detail_dict["categoryfirst_breadcrumb"])
                customer_data["allbreadcrumbs"].append(detail_dict["allbreadcrumbs"])
                customer_data["price"].append(detail_dict["price"])
                customer_data["urlproduct"].append(detail_dict["product_link"])
                customer_data["verified_review"].append(detail_dict["verified_review"])

            new_df = pd.DataFrame(customer_data)
            df = pd.concat([df, new_df], axis=0)

            bot.close()


            # Switch back to the original window
            bot.switch_to.window(bot.window_handles[0])
            df.to_excel(OUT_PATH, index=False)
            if customer_count >= customer_count_limit:
                break

        next_page = bot.next_review_page(current_page)
        # print(next_page)
        if next_page is None:
            # print("no rev")
            break
        verified_reviews = bot.get_verified_reviews(next_page)
        current_page = next_page
        # print("end of loop")
    else:
        break

df.to_excel(OUT_PATH, index=False)