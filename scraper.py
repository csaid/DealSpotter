'''Module for scraping Craigslist'''

from bs4 import BeautifulSoup
import urllib2
import re
import pickle
import MySQLdb
import json
from pandas import DataFrame, Series
from pandas.io import sql
import pandas as pd
import utilities
reload(utilities)
import utilities as ut
import datetime as dt


class Scraper:

    def __init__(self, area):
        '''
        Args:
            area - Craigslist region, e.g. 'sfbay', 'losangeles', etc (string)
        '''
        self.df = DataFrame(columns=['year',
                                     'model',
                                     'price',
                                     'miles',
                                     'lat',
                                     'lon',
                                     'date',
                                     'area',
                                     'title',
                                     'body',
                                     'phone',
                                     'image_count',
                                     'url'])
        self.conn = MySQLdb.connect(user="root", passwd="", db="carsdb")
        self.table_name = "scraped"
        self.url_root = "http://" + area + ".craigslist.org"
        self.area = area

    def _find_miles(self, s):
        '''
        Args:
            s - Craigslist text (title or body)
        Returns mileage (int)
        '''
        # is thousand indicated by 'k' or comma and three digits
        kstyles = ["k", ",*[0-9]+"]

        for kstyle in kstyles:

            thznd = r"\b[0-9]+"  # e.g. for 15,000 miles, this value is '15'

            expressions = ["(" + thznd + kstyle + ") miles",
                           "(" + thznd + kstyle + ") mi",
                           "odometer: (" + thznd + kstyle + ")",
                           "miles: (" + thznd + kstyle + ")",
                           "mileage: (" + thznd + kstyle + ")",
                           "mileage.{0,4}?(" + thznd + kstyle + ")",
                           "miles.{0,4}?(" + thznd + kstyle + ")",
                           "(" + thznd + kstyle + ").{0,4}?miles"]

            # Look for more sensible expressions of mileage first
            for expression in expressions:
                result = re.search(expression, s, flags=re.IGNORECASE)
                if result:
                    if kstyle == "k":
                        str_val = result.group(
                            1).replace('k',
                                       '').replace('K',
                                                   '')
                        val = 1000 * int(str_val)
                        if val < 999999:
                            return(val)
                    else:
                        val = int(result.group(1).replace(',', ''))
                        if val < 999999:
                            return(val)

    def _find_year(self, s):
        '''
        Args:
            s - Craigslist text (title or body)
        Returns year (int)
        '''
        result = re.search(r"\b(19[89][0-9]|200[0-9]|201[0-4])\b", s)
        if result:
            return int(result.group(1))

    def _find_model(self, s, models):
        '''
        Args:
            s - Craigslist text (title or body)
        Returns model (string)
        '''
        for word in s.lower().split():
            if word in models:
                return word

    def _find_phone(self, s):
        '''
        Args:
            s - Craigslist text (title or body)
        Returns phone number (string)
        '''
        result = re.search(r"\d\d\d-\d\d\d\d", s)
        if not result:
            result = re.search(r"\d\d\d\.\d\d\d\.\d\d\d\d", s)
        if not result:
            result = re.search(r"\d\d\d\d\d\d\d\d\d\d", s)

        if result:
            return result.group(0)

    def _find_date(self, soup):
        '''
        Args:
            soup - Beatiful soup object from Craigslist ad
        Returns date (string)
        '''
        text = soup.find('date').text
        date = text.split()[0].strip(',').replace('-', ':')
        time = text.split()[1]
        time = dt.datetime.strptime(time, '%I:%M%p').time().isoformat()
        return date + ":" + time

    def _find_lat_lon(self, soup):
        '''
        Args:
            soup - Beatiful soup object from Craigslist ad
        Returns latitude and longitude (floats)
        '''
        leaflet = soup.find(id="leaflet")
        if leaflet:
            lat = float(leaflet.attrs['data-latitude'])
            lon = float(leaflet.attrs['data-longitude'])
            return lat, lon
        else:
            return None, None

    def _process_search_page(self, page_index):
        '''
        Args:
            page_index - Craigslist search page index, e.g. 100, 200, etc (int)
        '''
        models = {model['name'] for model in json.load(open("models.json"))}
        url = self.url_root + "/cta/index" + str(page_index) + ".html"
        search_page = urllib2.urlopen(url)
        search_soup = BeautifulSoup(search_page)
        rows = search_soup.find_all("p", class_="row")

        # Read each row of a search page
        for row in rows:

            try:

                price_tag = row.find("span", class_="price")
                tag = row.find("span", class_="date").next_sibling.next_sibling
                title = tag.text
                model = self._find_model(title, models)

                # Only follow link if price and model are in title
                if price_tag and model:

                    # Get price
                    price = int(price_tag.text.replace('$', ''))

                    # Follow link and read page
                    car_link = tag["href"]
                    car_page = urllib2.urlopen(self.url_root + car_link)
                    soup = BeautifulSoup(car_page)
                    body = soup.find(id="postingbody").text

                    # Find latitude and longitude
                    lat, lon = self._find_lat_lon(soup)

                    # Find date
                    date = self._find_date(soup)

                    # Find miles
                    miles = self._find_miles(title)
                    if not miles:
                        miles = self._find_miles(body)

                    # Find year
                    year = self._find_year(title)

                    # Find phone
                    phone = self._find_phone(body)

                    # Find image_count
                    thumbs = soup.find("div", {"id": "thumbs"})
                    if thumbs:
                        image_count = len(thumbs.findAll("img"))
                    else:
                        image_count = 0

                    # Include in dataframe only if a year and mileage were
                    # found
                    if year and miles:
                        df_row = DataFrame([{'year': year,
                                             'model': model,
                                             'price': price,
                                             'miles': miles,
                                             'lat': lat,
                                             'lon': lon,
                                             'date': date,
                                             'area': self.area,
                                             'title': title,
                                             'body': body,
                                             'phone': phone,
                                             'image_count': image_count,
                                             'url': car_link}])
                        self.df = self.df.append(df_row, ignore_index=True)

                    print(title)
                    print(miles)
                    print(year)
                    print('\n')

            except:
                print("\n\nError encountered!!\n\n")

    def load(self):
        '''
        Loads existing scraped data from a pickled dataframe
        '''
        self.df = sql.read_frame("SELECT * FROM " + self.table_name, self.conn)

    def scrape(self, num_posts):
        '''
        Scrape Craigslist

        Args:
            num_posts - Number of posts to consider (int)
        '''
        for page_index in range(0, num_posts, 100):
            print("page_index = " + str(page_index))
            self._process_search_page(page_index)

    def save(self, create_or_append):
        '''
        Saves scraped data to database and to DataFrame pickle. User can choose whether
        to append to or overwrite the database table, but the DataFrame pickle will
        always be overwritten

        Args:
            create_or_append - 'create' or 'append'. Applies only to database table.
            DataFrame pickle will always be overwritten (string)
        '''

        # Pickle DataFrame as extra backup
        pickle.dump(self.df, open('my_df.pickle', "w"))

        # Write to database
        if create_or_append == 'create':
            ut.drop_if_exists(self.conn, self.table_name)
            ut.prepare_table_w_textcols(
                self.df,
                self.table_name,
                self.conn,
                ['body',
                 'title'])
        elif create_or_append == 'append':
            pass
        else:
            raise ValueError("Please provide 'create' or 'append'")
        sql.write_frame(
            self.df,
            self.table_name,
            self.conn,
            flavor="mysql",
            if_exists="append")


        # Remove duplicate
        cur = self.conn.cursor()
        cmd = "ALTER IGNORE TABLE " + self.table_name + " ADD UNIQUE INDEX(miles,price,year)"
        print(cmd)
        cur.execute(cmd)
        print(self.df)
