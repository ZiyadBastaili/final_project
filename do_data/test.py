import re
import sys

import pandas as pd
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
from scrapy.pipelines.images import ImagesPipeline


# class ScrapCollectionsSpider(scrapy.Spider):
#
#     name = 'collections'
#     start_urls = ['https://cryptoslam.io/',]
#     ITEM_PIPELINES = {'scrapy.pipelines.images.ImagesPipeline': 1}
#     IMAGES_STORE = 'data/collections/images/images/'
#
#
#     def parse(self, response):
#         names = response.xpath('//*[@class="table table-hover js-top-by-sales-table-24h summary-sales-table"]//tbody//tr//td[2]/a/span[contains(@class, "summary-sales-table__column-product-name")]/text()').extract()
#         rows = response.xpath('//*[@class="table table-hover js-top-by-sales-table-24h summary-sales-table"]//tbody//tr//td[2]/a/img/@data-src').extract()
#         names.extend(response.xpath('//*[@class="table table-hover js-top-by-sales-table-24h summary-sales-table"]//tbody//tr//td[2]/span/span[contains(@class, "summary-sales-table__column-product-name")]/text()').extract())
#         rows.extend(response.xpath('//*[@class="table table-hover js-top-by-sales-table-24h summary-sales-table"]//tbody//tr//td[2]/span/img/@data-src').extract())
#
#         images = []
#         for name , row in zip(names,rows):
#             images.append({'url': str(row), 'name': name})
#             yield {'image_urls': images}
#
# class CustomImageNamePipeline(ImagesPipeline): #I copied this code from the website
#     def get_media_requests(self, item, info):
#         for image in item.get('image_urls', []):
#             if len(image["url"]) != 0:
#                 yield scrapy.Request(image["url"], meta={'image_name': image["name"]})
#
#     def file_path(self, request, response=None, info=None):
#         return '%s.png' % request.meta['image_name']
#
# process = CrawlerProcess({'ITEM_PIPELINES': {'__main__.CustomImageNamePipeline': 1},
#     # this folder has to exist before downloading
#     'IMAGES_STORE': 'data/collections/images/images/',
#     'MEDIA_ALLOW_REDIRECTS' : True})
# process.crawl(ScrapCollectionsSpider)
# process.start()


########################################################
########################################################
#              get transactions by adress              #
#                     api etherscan                    #
########################################################
########################################################

import json
import time
import requests
from decimal import Decimal
import certifi
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import collections


def get_transactions_by_adress(ADDRESS = "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb", NUMBER_TXNS = 100):
    ETHERSCAN_API_KEY = 'ZJVZXQXDKBR38YB2WE2UMMPVZ8QJ9MYT8V'
    ETHERSCAN_API_KEY = 'YourApiKeyToken'
    URL = "https://api.etherscan.io/api?module=account&action=txlist&address=" + ADDRESS + \
          "&startblock=0&endblock=99999999&page=1&offset=" + str(NUMBER_TXNS) + \
          "&sort=desc&apikey=" + ETHERSCAN_API_KEY

    response = requests.get(URL, verify=certifi.where())
    address_content = response.json()
    result = address_content.get("result")

    data = collections.defaultdict(dict)
    for n, transaction in enumerate(result):
        hash = transaction.get("hash")
        tx_from = transaction.get("from")
        tx_to = transaction.get("to")
        value = transaction.get("value")
        confirmations = transaction.get("confirmations")
        if tx_from == ADDRESS:
            tx_type = "Sending"
        else:
            tx_type = "Receiving"
        eth_value = Decimal(value) / Decimal("1000000000000000000")
        if int(confirmations) >= 16:
            stat = "Confirmed"
        else:
            stat = "Pending"

        data[n]["hash"] = hash
        data[n]["tx_from"] = tx_from
        data[n]["tx_to"] = tx_to
        data[n]["value"] = value
        data[n]["eth_value"] = eth_value
        data[n]["confirmations"] = confirmations
        data[n]["tx_type"] = tx_type
        data[n]["stat"] = stat

    return data


# data = get_transactions_by_adress(ADDRESS = "0x165b4d1dd5860b1cc060ca0042a738834b3aac38a71837c3bf3513dd743d2873", NUMBER_TXNS = 1)
# print(data)






########################################################
########################################################
#               Scrapy : ScrapCollections              #
#                  from cryptoslam.io                  #
########################################################
########################################################

# import requests
#
# url = "https://api.opensea.io/api/v1/asset/0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb/7358/"
#
# response = requests.request("GET", url)
#
# print(response.text)


#############################################################################
#############################################################################
#############################################################################
from urllib import request
# import requests
# url = "https://api.opensea.io/api/v1/asset/0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb/2863/"
# response = requests.request("GET", url)
#
# print(json.dumps(response.json(), indent=2))

# import twint
#
#
#
# # Set up TWINT config
# c = twint.Config()
# c.Search = "CryptoPunks"
# # Custom output format
# c.Since = '2021-08-21'
# c.Until = '2021-09-20'
# c.Pandas = True
# twint.run.Search(c)
#
#
# def twint_to_pd(columns):
#     return twint.output.panda.Tweets_df[columns]
# pd.options.mode.chained_assignment = None
#
# tweet_df = twint_to_pd(["date", "username", "tweet", 'language', "hashtags", 'nlikes', 'nreplies', 'nretweets','link', 'urls'])
# tweet_df['date'] = tweet_df['date'].str.slice(0,10)
# print(tweet_df['date'])
# df_chart = tweet_df.groupby('date').size().reset_index(name='Size')
#
# print(df_chart.date.tolist())
#

# import snscrape.modules.twitter as sntwitter
# from dateutil.parser import parse
#
#
# since, until = '2021-08-21', '2021-09-20'
# search = '$SNE'
# tweets_list2 = []
# limit = 50
# for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search).get_items()):
#     if i > limit:
#         break
#     print(str(i) + " : " + str(tweet.date))
#     tweets_list2.append([tweet.date, tweet.id, tweet.content,\
#                          tweet.user.username, tweet.user.followersCount,tweet.replyCount,\
#                          tweet.retweetCount, tweet.likeCount, tweet.quoteCount, tweet.lang,\
#                          tweet.outlinks, tweet.media, tweet.retweetedTweet, tweet.quotedTweet,\
#                          tweet.inReplyToTweetId, tweet.inReplyToUser, tweet.mentionedUsers,\
#                          tweet.coordinates, tweet.place, tweet.hashtags, tweet.cashtags, tweet.url])
#
#
#
# tweets_df2 = pd.DataFrame(tweets_list2, columns=['date', 'Tweet Id', 'tweet', 'username', 'followersCount', 'replyCount',
#                                                  'retweetCount', 'likeCount', 'quoteCount', 'lang', 'outlinks', 'media',
#                                                  'retweetedTweet', 'quotedTweet', 'inReplyToTweetId', 'inReplyToUser',
#                                                  'mentionedUsers', 'coordinates', 'place', 'hashtags', 'cashtags', 'url'])
#
#
# tweets_df2['date'] = tweets_df2['date'].apply(lambda d: parse(str(d)).date())
# tweets_df2.to_excel("tjjjjjw.xlsx", index=False)
# df = tweets_df2
# # df =pd.read_excel('tjjjjjw.xlsx')
# print(len(df))
# df.drop_duplicates(subset='tweet')
# print(len(df))


import streamlit as st

# c1,c2,c3,c4,c5,c6 = st.columns(6)
# url = 'https://lh3.googleusercontent.com/7RMFqd8hwMKhvX-KKn869oznTasyPXW-nixggIBcmWK71zQpy8Kjj_2jS4Nc9z0e7kVBEB4KZ7IvqkudEdIZ8GyF2Spb_YU-CabUmA'
#
# j=1
# for i in range(48):
#     if j == 1:
#         c1.image(url, width=100)
#         c1.markdown('-----')
#         j+=1
#     elif j == 2:
#         c2.image(url, width=100)
#         c2.markdown('-----')
#         j+=1
#     elif j == 3:
#         c3.image(url, width=100)
#         c3.markdown('-----')
#         j += 1
#     elif j == 4:
#         c4.image(url, width=100)
#         c4.markdown('-----')
#         j += 1
#     elif j == 5:
#         c5.image(url, width=100)
#         c5.markdown('-----')
#         j += 1
#     elif j == 6:
#         c6.image(url, width=100)
#         c6.markdown('-----')
#         j = 1


###################################################################################################################
###################################################################################################################
################ bg color and font color
###################################################################################################################
###################################################################################################################


# """A Simple Streamlit App For CSS Shape Generation """
# st.title("Simple CSS Shape Generator")
# html_design = """
# 		<div style="height:{}px;width:{}px;background-color:{};border-radius:{}px {}px {}px {}px;border-color:{}">
# 		</div>
# 		"""
#
#
# st.markdown(html_design.format(20,20,'black',1,1,1,1,'red'),unsafe_allow_html=True)
#
# activity = ['Design', 'About', ]
# choice = st.sidebar.selectbox("Select Activity", activity)
#
# if choice == 'Design':
#     st.subheader("Design")
#     bgcolor = st.color_picker("Pick a Background color")
#     fontcolor = st.color_picker("Pick a Font Color", "#fff")
#
#     html_temp = """
# 		<div style="background-color:{};padding:10px">
# 		<h1 style="color:{};text-align:center;">Streamlit Simple CSS Shape Generator </h1>
# 		</div>
# 		"""
#     st.markdown(html_temp.format(bgcolor, fontcolor), unsafe_allow_html=True)
#     st.markdown("<div><p style='color:{}'>Hello Streamlit</p></div>".format(bgcolor), unsafe_allow_html=True)
#
#     st.subheader("Modify Shape")
#     bgcolor2 = st.sidebar.color_picker("Pick a Bckground color")
#     height = st.sidebar.slider('Height Size', 50, 200, 50)
#     width = st.sidebar.slider("Width Size", 50, 200, 50)
#     # border = st.slider("Border Radius",10,60,10)
#     top_left_border = st.sidebar.number_input('Top Left Border', 10, 50, 10)
#     top_right_border = st.sidebar.number_input('Top Right Border', 10, 50, 10)
#     bottom_left_border = st.sidebar.number_input('Bottom Left Border', 10, 50, 10)
#     bottom_right_border = st.sidebar.number_input('Bottom Right Border', 10, 50, 10)
#
#     border_style = st.sidebar.selectbox("Border Style",
#                                         ["dotted", "dashed", "solid", "double", "groove", "ridge", "inset", "outset",
#                                          "none", "hidden"])
#     border_color = st.sidebar.color_picker("Pick a Border Color", "#654FEF")
#
#     st.markdown(html_design.format(height, width, bgcolor2, top_left_border, top_right_border, bottom_left_border,
#                                    bottom_right_border, border_style, border_color), unsafe_allow_html=True)
#
#     if st.checkbox("View Results"):
#         st.subheader("Result")
#         result_of_design = html_design.format(height, width, bgcolor2, top_left_border, top_right_border,
#                                               bottom_left_border, bottom_right_border, border_style, border_color)
#         st.code(result_of_design)
#
# if choice == "About":
#     st.subheader("About")
#     st.info("Jesus Saves @JCharisTech")
#     st.text("By Jesse E.Agbe(JCharis)")
#     st.success("Built with Streamlit")



###################################################################################################################
###################################################################################################################
###################################################################################################################
###################################################################################################################
#
# import requests
# import pandas as pd
# import json
#
# url = "https://api.opensea.io/api/v1/assets"
#
# for i in range(0, 4000):
#     querystring = {"token_ids":list(range((i*30)+1, (i*30)+31)),
#                   "asset_contract_address" : "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb",
#                   "order_direction":"desc",
#                   "offset":"0",
#                   "limit":"30"}
#     response = requests.request("GET", url, params=querystring)
#     if response.status_code != 200:
#         print('error')
#         break
#
#     print(json.dumps(response.json(), indent=2))




####################################################################
####################################################################
####################################################################

import pandas as pd
import scrapy
import streamlit as st


btn = '''


<div id="myDiv" style="display:none;" class="answer_list" >WELCOME</div>
<input type="button" name="answer" onclick="ShowDiv()" />

'''


st.markdown("<script>function ShowDiv() {document.getElementById('myDiv').style.display = '';}</script>", unsafe_allow_html=True)
st.markdown(btn, unsafe_allow_html = True)