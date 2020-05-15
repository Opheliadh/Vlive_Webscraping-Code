import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import re

# Team member names and emails
# Sophie Yun: sophieyun1229@gmail.com
# Ophelia Dong: opheliadong@gmail.com
# Yifan Zhao: zyf18@g.ucla.edu

# We want to scrape all the kpop channels on this page: https://www.vlive.tv/channels?order=popular&tagSeq=18 For
# Each channel, we want to get its name, followers and information on all videos, including views, comments and likes
# We mainly uses the selenium package to assist with the infinite scrolling and BeautifulSoup to extract information

# Get driver
driver = webdriver.Chrome("/Users/opheliadong/Desktop/chromedriver")
driver.implicitly_wait(3)


# The scroll function is obtained from the website below:
# https://dev.to/hellomrspaceman/python-selenium-infinite-scrolling-3o12
def scroll(driver, timeout):
    scroll_pause_time = timeout

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height


# This function will get each channel's link and channel name
# The input x refers to the main page containing all channels, which we will provide in the for loop on line 153.
def get_channel_pages(x):
    vliveurl = x
    vlive = requests.get(vliveurl)
    soup = BeautifulSoup(vlive.content, 'html.parser')

    names = []
    ispremiums = []
    ids = []

    all_artists = soup.find_all("a", class_='ct_box _channelThumbnail')

    for artist in all_artists:
        # get the unique id in http of each individual channel
        link = artist.get("href")
        id_list = re.findall('(?<=/channels/)\w+', link)
        ids.append(id_list[0])

        # get name of each channel
        name = artist.get("data-ga-name")
        names.append(name)

        # get ispremium
        # We want to separate normal channels that everyone can access from the fanship pages
        # fanship page has the label "PREMIUM"
        # normal channel has the label "BASIC"
        ispremium = artist.get("data-ga-type")
        ispremiums.append(ispremium)

    # exclude the "premium" channels
    index_BASIC = [i for i, o in enumerate(ispremiums) if o == "BASIC"]
    link_BASIC = []
    names_BASIC = []

    # Append all links and names of the channels on the main page into two separate objects
    for i in index_BASIC:
        temporary_link = ids[i]
        temporary_name = names[i]
        link_BASIC.append(temporary_link)
        names_BASIC.append(temporary_name)

    # append all individual channel links using their unique id in link_BASIC
    channel_link_pg = []

    for j in link_BASIC:
        each_channel_link = "https://channels.vlive.tv/" + j + "/video"
        channel_link_pg.append(each_channel_link)

    return channel_link_pg, names_BASIC


# This function extracts the information on each individual channel page
# each_link refers to the link of the individual channel
# each_name refers to the name of the channel
def get(each_link, each_name):
    driver.get(each_link)

    scroll(driver, 3)

    views_r = []
    title_r = []
    channel_r = []  # identifies the label of each video, under the category of ARTIST or others, like "V PICK!"
    date_r = []
    comments_r = []
    likes_r = []

    soup_a = BeautifulSoup(driver.page_source, 'html.parser')
    followers = soup_a.find('span', class_='value').get_text()
    infos = soup_a.find_all('div', class_="article_content -video")

    for info in infos:
        valid_data = str(info).find("article_info ng-star-inserted")

        if valid_data != -1:
            vpick_and_date = info.find('div', class_="author_info ng-star-inserted")
            vpick = vpick_and_date.find('span', class_="userName").get_text()
            channel_r.append(vpick)

            date = vpick_and_date.find('span', class_="time").get_text()
            date_r.append(date)

            view = info.find('span', class_="info play").contents[1]
            views_r.append(view)

            comment = info.find('span', class_="info chat").contents[1]
            comments_r.append(comment)

            like = info.find('span', class_='info like').contents[1]
            likes_r.append(like)

            title = info.find('strong', class_="title").get_text()
            title_r.append(title)

    artist_name = np.repeat(each_name, len(date_r))
    followers_rp = np.repeat(followers, len(date_r))

    each_data = pd.DataFrame(
        columns=["Artist", "Title", "V Pick or not", "Date", "Followers", "Views", "Like", "Comment"])

    each_data["Artist"] = artist_name
    each_data["Title"] = title_r
    each_data["V Pick or not"] = channel_r
    each_data["Date"] = date_r
    each_data["Followers"] = followers_rp
    each_data["Views"] = views_r
    each_data["Like"] = likes_r
    each_data["Comment"] = comments_r

    result = pd.concat([our_data, each_data])
    return result


# Dataframe: store information
our_data = pd.DataFrame(
    columns=["Artist", "Title", "V Pick or not", "Date", "Followers", "Views", "Like", "Comment"])

# Store all links on this page containing all kpop channels: https://www.vlive.tv/channels?order=popular&tagSeq=18
# Each new scroll produces a new link, so we created an object to store all of the sub-pages
scroll_down = []

for i in range(1, 32):
    # This link is obtained by manually inspecting the channel page and identifying patterns
    s = "https://www.vlive.tv/channels/more?pageNo=" + str(i) + "&order=popular&tagSeq=18&_=" + str(
        1589045398471 + (i - 2) * 2)
    scroll_down.append(s)

# Scrape the information
# Channel_link_pg contains all individual channel links
# name_BASIC refers to the name of the channels
for n in range(0, 31):
    channel_link_pg, names_BASIC = get_channel_pages(scroll_down[n])

    for i in range(0, len(channel_link_pg)):
        our_data = get(channel_link_pg[i], names_BASIC[i])

    our_data.to_csv("/Users/opheliadong/Desktop/page" + str(n) + ".csv")
