from bs4 import BeautifulSoup
import urllib2
import re
import pickle
import time
import MySQLdb
import json
from pandas import DataFrame, Series
import pandas as pd
from os import sys

class Scraper:

    def __init__(self):
        self.df = DataFrame(columns=['year',
                                     'model',
                                     'price',
                                     'miles',
                                     'lat',
                                     'lon',
                                     'title',
                                     'body',
                                     'phone',
                                     'image_count',
                                     'url'])
        self.conn = MySQLdb.connect(user="root", passwd = "", db="carsdb")
        self.table_name = "train"
        self.url_root = "http://sfbay.craigslist.org"

    def _find_miles(self, s):

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


    def _find_year(self, s):
        result = re.search(r"\b(19[89][0-9]|200[0-9]|201[0-4])\b", s)
        if result:
            return int(result.group(1))


    def _find_model(self, s, models):
        for word in s.lower().split():
            if word in models:
                return word

    def _find_phone(self, s):
        result = re.search(r"\d\d\d-\d\d\d\d", s)
        if not result:
            result = re.search(r"\d\d\d\.\d\d\d\.\d\d\d\d", s)
        if not result:
            result = re.search(r"\d\d\d\d\d\d\d\d\d\d", s)

        if result:
            return result.group(0)


    def _find_lat_lon(self, soup):
        leaflet = soup.find(id="leaflet")
        if leaflet:
            lat = float(leaflet.attrs['data-latitude'])
            lon = float(leaflet.attrs['data-longitude'])
            return lat, lon
        else:
            return None, None


    def _process_search_page(self, page_index):

        try:

            f = open("models.json")
            models = {model['name'] for model in json.load(f)}
            search_page = urllib2.urlopen(self.url_root + "/cta/index" + str(page_index) + ".html")
            search_soup = BeautifulSoup(search_page)
            rows = search_soup.find_all("p", class_="row")


            for row in rows:
                price_tag = row.find("span", class_="price")
                tag = row.find("span", class_="date").next_sibling.next_sibling#
                title = tag.text
                model = self._find_model(title, models)

                if price_tag and model:

                    print(title)

                    price = int(price_tag.text.replace('$',''))

                    car_link = tag["href"]

                    time.sleep(0.1)

                    car_page = urllib2.urlopen(self.url_root + car_link)

                    soup = BeautifulSoup(car_page)
                    body = soup.find(id="postingbody").text

                    # Find latitude and longitude
                    lat, lon = self._find_lat_lon(soup)

                    # Find miles
                    miles = self._find_miles(title)
                    if not miles:
                        miles = self._find_miles(body)

                    # Find year
                    year = self._find_year(title)
                    if not year:
                        year = self._find_year(body)

                    # Find phone
                    phone = self._find_phone(body)

                    # Find image_count
                    thumbs = soup.find("div", {"id": "thumbs"})
                    if thumbs:
                        image_count = len(thumbs.findAll("img"))
                    else:
                        image_count = 0

                    if year and miles:
                        df_row = DataFrame([{'year': year,
                                             'model': model,
                                             'price': price,
                                             'miles': miles,
                                             'lat': lat,
                                             'lon': lon,
                                             'title': title,
                                             'body': body,
                                             'phone': phone,
                                             'image_count': image_count,
                                             'url':car_link}])
                        self.df = self.df.append(df_row,  ignore_index=True)

                    print(miles)
                    print(year)
                    print('\n')
        except:
            print('ERROR ENCOUNTERED')


    def load(self):
        #self.df = pickle.load(open('my_df.pickle'))
        self.df = pd.io.sql.read_frame("SELECT * FROM " + self.table_name, self.conn)

    def scrape(self):
        for page_index in range(0, 30000, 100):
            print("page_index = " + str(page_index))
            self._process_search_page(page_index)

    def followup(self):
        new_contents = []
        for url in self.df['url']:
            soup = BeautifulSoup(urllib2.urlopen(self.url_root + url))
            new_contents.append(5)
        self.df['new_contents'] = new_contents



    def save(self):
        pickle.dump(self.df, open('my_df.pickle', "w"))

        # Remove table if already exists
        if pd.io.sql.table_exists(self.table_name, self.conn, flavor="mysql"):
            pd.io.sql.uquery("DROP table " + self.table_name, self.conn)

        # Pandas forces VARCHAR (63). Not long enough for body.
        cmd = pd.io.sql.get_schema(self.df, self.table_name, 'mysql')
        cmd = re.sub(r"`body` VARCHAR \(63\)", r"`body` TEXT", cmd)
        cmd = re.sub(r"`title` VARCHAR \(63\)", r"`title` TEXT", cmd)
        pd.io.sql.execute(cmd, self.conn)
        pd.io.sql.write_frame(self.df, self.table_name, self.conn, flavor="mysql", if_exists="append")


        print(self.df)



