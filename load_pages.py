from bs4 import BeautifulSoup
import urllib2
import re
import pickle
import time
from pandas import DataFrame, Series
import pandas as pd
from os import sys

def find_miles(s):

    kstyles = ["k", ",*[0-9]+"] # is thousand indicated by 'k' or comma and three digits

    for kstyle in kstyles:
        thznd = r"\b[0-9]+"
        expressions = ["(" + thznd + kstyle + ") miles",
                       "(" + thznd + kstyle + ") mi",
                       "odometer: (" + thznd + kstyle + ")",
                       "miles: (" + thznd + kstyle + ")",
                       "mileage: (" + thznd + kstyle + ")",
                       "mileage.{0,4}?(" + thznd  + kstyle + ")",
                       "miles.{0,4}?(" + thznd  + kstyle + ")",
                       "(" + thznd  + kstyle + ").{0,4}?miles"]

        for expression in expressions:
            result = re.search(expression, s, flags=re.IGNORECASE)
            if result:
                if kstyle=="k":
                    str_val = result.group(1).replace('k','').replace('K','')
                    return(1000*int(str_val))
                else:
                    return(int(result.group(1).replace(',','')))


def find_year(s):
    result = re.search(r"\b(19[89][0-9]|200[0-9]|201[0-4])\b", s)
    if result:
        return int(result.group(1))


def find_model(s, models):
    for word in s.lower().split():
        if word in models:
            return word


def find_lat_lon(soup):
    leaflet = soup.find(id="leaflet")
    if leaflet:
        lat = float(leaflet.attrs['data-latitude'])
        lon = float(leaflet.attrs['data-longitude'])
        return lat, lon
    else:
        return None, None


def process_search_page(page_index, df):
    url_root = "http://sfbay.craigslist.org"

    models = set(["accord", "camry", "civic", "corolla"])
    search_page = urllib2.urlopen(url_root + "/cta/index" + str(page_index) + ".html")
    search_soup = BeautifulSoup(search_page)
    rows = search_soup.find_all("p", class_="row")


    for row in rows:
        price_tag = row.find("span", class_="price")
        tag = row.find("span", class_="date").next_sibling.next_sibling#
        title = tag.text
        model = find_model(title, models)

        if price_tag and model:
            price = int(price_tag.text.replace('$',''))

            car_link = tag["href"]

            time.sleep(0.5)

            car_page = urllib2.urlopen(url_root + car_link)

            soup = BeautifulSoup(car_page)
            body = soup.find(id="postingbody").text

            # Find latitude and longitude
            lat, lon = find_lat_lon(soup)

            # Find miles
            miles = find_miles(title)
            if not miles:
                miles = find_miles(body)

            # Find year
            year = find_year(title)
            if not year:
                year = find_year(body)


            if year and miles:
                df_row = DataFrame([{'year': year,
                                     'model': model,
                                     'price': price,
                                     'miles': miles,
                                     'lat': lat,
                                     'lon': lon,
                                     'url':car_link}])
                df = df.append(df_row,  ignore_index=True)


    return df


def main():

    if (sys.argv[1] == 'scrape'):
        df = DataFrame(columns=['year', 'model', 'price', 'miles', 'lat', 'lon', 'url'])
        for page_index in range(0,300,100):
            print(page_index)
            df = process_search_page(page_index, df)

        pickle.dump(df, open('my_df.pickle', "w"))

    elif (sys.argv[1] == 'load'):
        df = pickle.load(open('my_df.pickle'))

    else:
        raise ValueError("Please provide scrape or load")

    print(df)


if __name__ == "__main__":
    main()
