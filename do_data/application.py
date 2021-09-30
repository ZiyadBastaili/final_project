import asyncio
import base64
import io
import itertools
import os
import re
import sys
import time
import datetime
import seaborn as sns
import nltk
from PIL import Image
from dateutil.parser import parse
import snscrape.modules.twitter as sntwitter
import altair as alt
import _cffi_backend
import pandas as pd
import requests
import streamlit as st
import hydralit_components as hc
import twint
from annotated_text import annotated_text
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px
from crochet import setup, wait_for
from matplotlib import pyplot as plt
from textblob import TextBlob
from texthero import preprocessing
import texthero as hero
from wordcloud import WordCloud
setup()
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

from .actions_classe import ScrapCollectionsSpider, ScrapCollectionsStatisticsSpider, ScrapSalesVolumeDataSpider, \
    ScrapSalesSpider, ScrapCollectionSalesSpider, ScrapTxnsSpider, ScrapContractAddresseSpider, get_assets, \
    get_sales_assets


class Application():

    def __init__(self):
        self.runner = CrawlerRunner()
        self.usedetails = list()

        st.set_page_config(page_title='Tweet Visualization and Sentiment Analysis in Python', layout="wide")

        st.markdown(""" <style>
                    footer {visibility: hidden;}
                    </style> """, unsafe_allow_html=True)

        padding = 3
        st.markdown(f""" <style>
                    .reportview-container .main .block-container{{
                        padding-top: {padding}rem;
                        padding-right: {padding}rem;
                        padding-left: {padding}rem;
                        padding-bottom: {padding}rem;
                    }} </style> """, unsafe_allow_html=True)



    def run_app(self):
        self.frame()

    def frame(self):
        self.title()
        self.body()
        self.footer()

    def title(self):
        #Image.open('do_data/images/background.png').convert('RGB').save('do_data/images/background.png')
        st.image("do_data/images/background.png", use_column_width=True)

    def body(self):
        menu_data = [
            {'icon': "fas fa-layer-group", 'label': "Top Collections"},  # no tooltip message
            {'icon': "fab fa-twitter", 'label': "Scrape From twitter"},  # no tooltip message
            {'icon': "fas fa-search-dollar", 'label': "Sales", 'ttip': "Top Sales"},
        ]

        over_theme = {'txc_inactive': '#FFFFFF','menu_background':'#000033','txc_active':'#fffff','option_active':'#9999ff'}
        menu_id = hc.nav_bar(menu_definition=menu_data, home_name='Home', override_theme=over_theme)

        if menu_id == 'Top Collections':
                    self.runner = CrawlerRunner()
                    self.get_collections()
                    time.sleep(0.2)
                    while True:
                        time.sleep(3)
                        if os.path.isfile('do_data/collections/collections_all_time.csv'):
                            break
                    self.display_collections()

        if menu_id == 'Scrape From twitter':
                    st.session_state.nav = 'Collections'
                    self.runner = CrawlerRunner()
                    st.title("Scrape Data From Twitter")

                    projects_names = pd.read_csv("do_data/collections/collections_all_time.csv")
                    projects_names = projects_names['product_name'].tolist()
                    projects_names.insert(0, 'Select username:')
                    st.markdown('<br>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    try:
                        c1.markdown("<br>", unsafe_allow_html = True)
                        self.all_tweets_search(projects_names)
                    except Exception as e:
                        st.warning(e)
                        st.image("https://www.reinforcedesigns.com/onlinemin/default-img/empty1.png", use_column_width=True)

        if menu_id == 'Sales':
                    self.runner = CrawlerRunner({'DOWNLOAD_DELAY': 1})
                    try:
                        self.get_sales()
                        time.sleep(0.2)
                        while True:
                            time.sleep(3)
                            if os.path.isfile('do_data/sales/sales_24h.csv'):
                                break
                        self.display_sales()
                    except:
                        st.markdown('<center><h1>ERROR<h1></center>', unsafe_allow_html=True)
                        st.image("https://www.reinforcedesigns.com/onlinemin/default-img/empty1.png", use_column_width=True)



    def footer(self):
        st.markdown('<i style="font-size:11px">alpha version 0.1</i>', unsafe_allow_html=True)




##############################################################################
##############################################################################
##################    Functions
##############################################################################
##############################################################################
    @st.cache
    @wait_for(timeout=20.0)  # wait 20s max
    def get_collections(self):
        d = self.runner.crawl(ScrapCollectionsSpider)

    @st.cache
    @wait_for(timeout=40.0)  # wait 40s max
    def get_contract_address(self, link):
        d = self.runner.crawl(ScrapContractAddresseSpider, link)

    @st.cache
    @wait_for(timeout=20.0)  # wait 20s max
    def get_sales(self):
        d = self.runner.crawl(ScrapSalesSpider)

    @st.cache
    @wait_for(timeout=40.0)  # wait 40s max
    def get_collections_sales(self, link, name):
        d = self.runner.crawl(ScrapCollectionSalesSpider, link, name)

    @st.cache
    @wait_for(timeout=60.0) #wait 1min max
    def get_collections_summary(self, name, link):
        d = self.runner.crawl(ScrapCollectionsStatisticsSpider, filename = name, start_urls = link)

    @st.cache
    @wait_for(timeout=60.0) #wait 1min max
    def get_transaction_by_project(self, link, tx_number):
        d = self.runner.crawl(ScrapTxnsSpider, link, tx_number)


    def time_nav(self, time):
        st.session_state.file = 'do_data/collections/collections_'+time+'.csv'
        st.session_state.time = time
        st.session_state.page_number = 0

    def button_navigation(self, nav, name_product = None, img_product = None, sales_product = None, summary_product = None):
        st.session_state.nav = nav
        st.session_state.name_product = name_product
        st.session_state.img_product = img_product
        st.session_state.sales_product = sales_product
        st.session_state.summary_product = summary_product

    def load_data(self, filename):
        data=pd.read_csv(filename)
        return data

    def dataframe_transformation(self, df):
        # *************** Daily Summary
        daily_summary = df[~df.Date.str.contains("Total")]
        # convert to date
        daily_summary['Date'] = pd.to_datetime(daily_summary['Date'])
        # sort
        daily_summary.sort_values(by='Date', inplace=True)
        # keep first format
        #daily_summary['Date'] = daily_summary['Date'].apply(lambda d: d.strftime("%d %B, %Y"))

        # *************** Monthly Summary
        monthly_summary = df[df.Date.str.contains("Total")]
        monthly_summary['Date'] = monthly_summary['Date'].apply(lambda x: x[8:11] + ' ' + x[11:])
        monthly_summary['Date'] = pd.to_datetime(monthly_summary['Date'])
        monthly_summary.sort_values(by='Date', inplace=True)
        #monthly_summary['Date'] = monthly_summary['Date'].apply(lambda d: d.strftime("%B, %Y"))

        return daily_summary.reset_index(drop=True), monthly_summary.reset_index(drop=True)

    @st.cache
    def display_chart(self, df):
        # Create figure
        fig = go.Figure()

        df['Sales (ETH)'] = df['Sales (ETH)'].apply(lambda x: re.sub('\\$|,', '', x))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Sales (ETH)']), name='Sales (ETH)'))

        df['Sales (USD)'] = df['Sales (USD)'].apply(lambda x: re.sub('\\$|,', '', x))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Sales (USD)']), name='Sales (USD)'))

        df['Total Transactions'] = df['Total Transactions'].apply(lambda x: re.sub('\\$|,', '', x))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Total Transactions']), name='Total Transactions'))

        df['Unique Buyers'] = df['Unique Buyers'].apply(lambda x: re.sub('\\$|,', '', str(x)))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Unique Buyers']), name='Unique Buyers'))

        df['Avg Sale (USD)'] = df['Avg Sale (USD)'].apply(lambda x: re.sub('\\$|,', '', str(x)))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Avg Sale (USD)']), name='Avg Sale (USD)'))

        df['Avg Sale (ETH)'] = df['Avg Sale (ETH)'].apply(lambda x: re.sub('\\$|,', '', str(x)))
        fig.add_trace(go.Scatter(x=list(df.Date), y=list(df['Avg Sale (ETH)']), name='Avg Sale (ETH)'))

        # Add range slider
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label="1m",
                             step="month",
                             stepmode="backward"),
                        dict(count=6,
                             label="6m",
                             step="month",
                             stepmode="backward"),
                        dict(count=1,
                             label="1y",
                             step="year",
                             stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        fig.update_layout(hovermode='x')
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)

        return fig

    @st.cache
    def user_profile(self, username):
        c = twint.Config()
        c.Username = username
        c.Store_object = True
        c.Hide_output = True
        twint.run.Lookup(c)
        user_profile = twint.output.users_list[-1]
        return user_profile

    def display_profile(self, user_profile):
        # get the profile_pic_url
        prof_pic = user_profile.avatar.replace("normal", "400x400")
        # download the image in a folder called static I created
        response = requests.get(prof_pic)
        filename = "image.jpg"
        with open(filename, "wb") as f:
            f.write(response.content)

        # show the full name
        st.markdown(annotated_text(("Full Name:", "", "#fea")," ", user_profile.name), unsafe_allow_html=True)
        st.write(' ')
        # we can format the output into as many columns as we want using beta_columns
        col1, col2 = st.columns(2)
        col1.image(filename)
        col2.markdown(annotated_text(("Biography:", "", "#faa")," ", user_profile.bio), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Location:", "", "#faa")," ", user_profile.location), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Number Of Tweets:", "", "#faa")," ", str(user_profile.tweets)), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Number Of Following:", "", "#faa")," ", str(user_profile.following)), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Number Of Followers:", "", "#faa")," ", str(user_profile.followers)), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Is Private Account:", "", "#faa")," ", str(user_profile.is_private)), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Is Verified Account:", "", "#faa")," ", str(user_profile.is_verified)), unsafe_allow_html=True)
        col2.write(' ')
        col2.markdown(annotated_text(("Number Of Liked tweets:", "", "#faa")," ", str(user_profile.likes)), unsafe_allow_html=True)
        col2.write(' ')
        date = str(user_profile.join_date) + str(' ') + str(user_profile.join_time)
        col2.markdown(annotated_text(("Date Of Join:", "", "#faa")," ", date), unsafe_allow_html=True)

    @st.cache
    def get_table_download_link_csv(self, df):
        csv = df.to_csv(index=False).encode()
        b64 = base64.b64encode(csv).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="captura.csv" target="_blank">Download csv file</a>'
        return href

    @st.cache
    def get_table_download_link_excel(self, df):
        towrite = io.BytesIO()
        downloaded_file = df.to_excel(towrite, encoding='utf-8', index=False, header=True)
        towrite.seek(0)  # reset pointer
        b64 = base64.b64encode(towrite.read()).decode()  # some strings
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="myDataframe.xlsx">Download excel file</a>'
        return href

    def select_details(self):
            try:
                details = ['Search', 'Limit', 'Period']
                label='Select fields'
                self.usedetails = st.multiselect(label=label, default='Limit',options=details)
            except:
                st.write('Field Select Error')

    def more_details(self, user_account):
        def twint_to_pd(columns):
            return twint.output.panda.Tweets_df[columns]
        def options():
            with st.form(key='my_form'):
                st.markdown(annotated_text(("User Account: ", "", "#faa"), " ", user_account), unsafe_allow_html=True)
                st.markdown('<br>', unsafe_allow_html=True)
                if 'Search' in self.usedetails:
                    Search = st.text_input(label='Text To Search')
                if 'Limit' in self.usedetails:
                    Limit = st.text_input(label='Number of Tweets to Pull')
                if 'Period' in self.usedetails:
                    yesterday = datetime.date.today() + datetime.timedelta(days=-1)
                    today = datetime.date.today()
                    Since = st.date_input('Start date', yesterday)
                    until = st.date_input('End date', today)
                submit_button = st.form_submit_button(label='Search')


            if submit_button:
                x = 0
                c = twint.Config()  # Set up TWINT config
                c.Username = user_account
                c.Hide_output = True # Suppress Terminal Output when running search ...
                if 'Search' in self.usedetails:
                    c.Search = Search  # Fill in the query that you want to search
                # ===================> Custom output format
                if 'Limit' in self.usedetails:
                    c.Limit = Limit  # Number of tweets to pull
                c.Pandas = True  # Storing objects in Pandas dataframes
                if 'Period' in self.usedetails:
                    c.Since = str(Since) # Filter tweets from this date
                    c.until= str(until) # Filter tweets upto this date
                    if Since > until:
                        x=1
                        st.error('Error: End date must fall after start date.')

                if x==0:
                    st.text('Loading data...')
                    asyncio.set_event_loop(asyncio.new_event_loop())
                    twint.run.Search(c)
                    st.success('Loading data... done!')
                    self.tweet_df = twint_to_pd(['date', 'username', 'tweet', 'language', 'hashtags', 'nlikes', 'nreplies', 'nretweets', 'link', 'urls'])
                    st.write(self.tweet_df)
                    # save
                    tweet_df_CSV = twint_to_pd(['id', 'conversation_id', 'created_at', 'date', 'timezone', 'place',
                                                'tweet', 'language', 'hashtags', 'cashtags', 'user_id', 'user_id_str',
                                                'username', 'name', 'day', 'hour', 'link', 'urls', 'photos', 'video',
                                                'thumbnail', 'retweet', 'nlikes', 'nreplies', 'nretweets', 'quote_url',
                                                'search', 'near', 'geo', 'source', 'user_rt_id', 'user_rt',
                                                'retweet_id', 'reply_to', 'retweet_date', 'translate', 'trans_src',
                                                'trans_dest'])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(self.get_table_download_link_csv(tweet_df_CSV), unsafe_allow_html=True)
                    with col2:
                        pass
                    with col3:
                        st.markdown(self.get_table_download_link_excel(tweet_df_CSV), unsafe_allow_html=True)

        options()


    def twint_to_pd(self, columns):
        return twint.output.panda.Tweets_df[columns]

    @st.cache
    def twint_function(self, username, Limit=None, Since=None, Until=None):
        x = 0
        c = twint.Config()  # Set up TWINT config
        c.Hide_output = True  # Suppress Terminal Output when running search ...
        c.Search = "\""+ username +"\""  # Fill in the query that you want to search
        if username == 'Select username:':
            x = 1
        if Limit != None:
            c.Limit = Limit  # Number of tweets to pull
        c.Pandas = True  # Storing objects in Pandas dataframes
        if Since != None:
            c.Since = str(Since)  # Filter tweets from this date
            c.until = str(Until)  # Filter tweets upto this date
            if Since > Until:
                x = 1
        if x == 0:
            asyncio.set_event_loop(asyncio.new_event_loop())
            twint.run.Search(c)
            tweet_df = self.twint_to_pd(['date', 'username', 'tweet', 'language'])
            return x, tweet_df

    @st.cache(allow_output_mutation=True)
    def snscrape_function(self, username, Limit=None, Since=None, Until=None):
        x, tweets_df2 = 0, None
        if username == 'Select username:' :
            x = 1
        if Limit != None:
            try:
                Limit = int(Limit)
            except:
                x = 1
        if x == 0 :
            # Creating list to append tweet data to
            tweets_list2 = []
            if Since != None:
                # Using TwitterSearchScraper to scrape data and append tweets to list
                since, until = str(Since) , str(Until)
                for i, tweet in enumerate(sntwitter.TwitterSearchScraper(username+' since:'+since+' until:'+until).get_items()):
                    if Limit != None:
                        if i > int(Limit):
                            break

                    tweets_list2.append([tweet.date, tweet.id, tweet.content,\
                         tweet.user.username, tweet.user.followersCount,tweet.replyCount,\
                         tweet.retweetCount, tweet.likeCount, tweet.quoteCount, tweet.lang,\
                         tweet.hashtags, tweet.cashtags])

            else:
                for i, tweet in enumerate(sntwitter.TwitterSearchScraper(username).get_items()):
                    if Limit != None:
                        if i > int(Limit):
                            break
                    tweets_list2.append([tweet.date, tweet.id, tweet.content,\
                         tweet.user.username, tweet.user.followersCount,tweet.replyCount,\
                         tweet.retweetCount, tweet.likeCount, tweet.quoteCount, tweet.lang,\
                         tweet.hashtags, tweet.cashtags])

            tweets_df2 = pd.DataFrame(tweets_list2, columns=['date', 'Tweet Id', 'tweet', 'username', 'followersCount', 'replyCount',
                                                 'retweetCount', 'likeCount', 'quoteCount', 'lang', 'hashtags', 'cashtags'])

        return x, tweets_df2

    def date_custom(self, datetime):
        dt = parse(datetime)
        return dt.date()

    @st.cache
    def display_date_picker(self, date_picker):
        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=date_picker['date'].tolist(),y=date_picker['Size'].tolist(),
                                 line=dict(color='red'), opacity=0.8))

        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label='1d',
                             step='day',
                             stepmode='backward'),

                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        fig.update_layout(hovermode='x', margin=dict(l=10,r=10,b=10,t=15))
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)

        return fig


    def all_tweets_search(self, projects_names):
        if 'run' not in st.session_state:
            st.session_state.run = 'no'

        Limit, Since, until = None, None, None
        st.caption("* **Number of Tweets to Pull: ** Leave the box blank if you don't want to specify the limit")
        with st.form(key='my_form'):
            c1, c2, c3 = st.columns(3)
            c1.markdown(annotated_text(("Product Name: ", "", "#faa"), " ", ''), unsafe_allow_html=True)
            username = c1.selectbox(label="", options=projects_names, key='11')

            c3.markdown(annotated_text(("Number of Tweets to Pull: ", "", "#789cfa"), " ", ''), unsafe_allow_html=True)
            Limit = c3.text_input(label='', help = "Leave the box blank if you don't want to specify the limit")
            if len(Limit)==0:
                Limit=None

            c2.markdown(annotated_text(("Select Period: ", "", "#faa"), " ", ''), unsafe_allow_html=True)
            period = c2.selectbox(label='', options=['2days','3days','7days','15days','30days','6months','1year','5years','all'])
            if period in ['2days','3days', '7days']:
                d =period[0]
                Since = datetime.date.today() + datetime.timedelta(days=-int(d))
            elif period in ['15days','30days']:
                d =period[0:2]
                Since = datetime.date.today() + datetime.timedelta(days=-int(d))
            elif period == '6months':
                d =period[0]
                Since = datetime.date.today() + datetime.timedelta(days=-int(d)*30)
            elif period in ['1year','5years']:
                d =period[0]
                Since = datetime.date.today() + datetime.timedelta(days=-int(d)*365)
            else:
                Since = None

            Until = datetime.date.today()

            submit_b = st.form_submit_button(label='Search')

        if submit_b:
            st.session_state.run = 'yes'

        if st.session_state.run == 'yes':
                x, tw_df = self.snscrape_function(username, Limit, Since, Until)

                if x == 1:
                    c1, c2 = st.columns((1,6))
                    c1.image('https://cdn.dribbble.com/users/2469324/screenshots/6538803/comp_3.gif', use_column_width=True)
                    c2.warning('''**Error: You may do something wrong:**  
                    
                    1) The product name must be selected. 
                    
                    2) Leave Limit blank or set an integer.''')

                else:
                    tw_df['date'] = tw_df['date'].apply(lambda d: parse(str(d)).date())
                    st.success('Loading data... done!')

                    with st.expander('Show Table of Tweets'):
                        # save
                        tweet_df_CSV = tw_df
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(self.get_table_download_link_csv(tweet_df_CSV), unsafe_allow_html=True)
                        with col2:
                            pass
                        with col3:
                            st.markdown(self.get_table_download_link_excel(tweet_df_CSV), unsafe_allow_html=True)
                        st.table(tw_df['tweet'])

                    tw_nlp = tw_df[['date', 'tweet']]
                    date_picker = tw_nlp.groupby('date').size().reset_index(name='Size')

                    st.markdown('<h2>Number of Tweets per day</h2>', unsafe_allow_html=True)
                    c1, c2 = st.columns((4,1))
                    with c1:
                        fig = self.display_date_picker(date_picker)
                        st.plotly_chart(fig, use_container_width=True)
                    with c2:
                        st.markdown('<br><br><br><br>', unsafe_allow_html = True)
                        colorscale = [[0, 'red'], [.5, '#f2e5ff'], [1, '#ffffff']]
                        fig = ff.create_table(date_picker, colorscale= colorscale)
                        fig.layout.xaxis.fixedrange = True
                        fig.layout.yaxis.fixedrange = True
                        st.plotly_chart(fig, use_container_width=True)

                    # Data preprocessing
                    st.markdown("<h2 style='text-align: left; color: gry;'> Data preprocessing </h2>", unsafe_allow_html=True)
                    with st.expander('Data preprocessing'):
                        tw_nlp = self.DF_cleaning(tw_nlp)
                    st.success('Data Cleaning... Done')

                    # Sentiment Analysis of Tweets
                    st.title('Sentiment Analysis of Tweets')
                    fig, tw_nlp = self.nlp_analysis(tw_nlp, date_picker)
                    with st.expander('Show Clean Data of Tweets'):
                        st.table(tw_nlp)
                    st.plotly_chart(fig, use_container_width=True)

                    # creating word cloud visualizations
                    st.title("Word Cloud")
                    st.set_option('deprecation.showPyplotGlobalUse', False)
                    c1, c2, c3 = st.columns(3)
                    for i, word_sentiment in enumerate(['Positive', 'Neutral', 'Negative']):
                        df = tw_nlp[tw_nlp['Analysis'] == word_sentiment]
                        words = ' '.join(df['tweet'])
                        wordcloud = WordCloud(background_color='black').generate(words)
                        plt.imshow(wordcloud, interpolation='bilinear')
                        plt.axis("off")
                        plt.show()
                        if i == 0:
                            c1.subheader('Word cloud for %s sentiment' % word_sentiment)
                            c1.pyplot()
                        elif i == 1:
                            c2.subheader('Word cloud for %s sentiment' % word_sentiment)
                            c2.pyplot()
                        else:
                            c3.subheader('Word cloud for %s sentiment' % word_sentiment)
                            c3.pyplot()


                    # Active accounts
                    st.title("Active accounts ")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                            st.subheader('Average Likes Per Person')
                            tweet_likes = tw_df[['username', 'likeCount']]
                            likes = tweet_likes.groupby(['username']).mean().sort_values(by=['likeCount'],ascending=False).reset_index()
                            colorscale = [[0, 'red'], [.5, '#f2e5ff'], [1, '#ffffff']]

                            rows = st.slider('How much person number to display?', 0, len(likes), 10)

                            fig = ff.create_table(likes.head(int(rows)), colorscale=colorscale)
                            fig.layout.xaxis.fixedrange = True
                            fig.layout.yaxis.fixedrange = True
                            st.plotly_chart(fig, use_container_width=True)
                    with col2:
                            st.subheader('Total Tweets Per Person')
                            tweet_count = tw_df[['username']]
                            tweet_count = tweet_count.groupby('username').size().reset_index(name='Size')
                            user_count = tweet_count.sort_values(by=['Size'], ascending=False).reset_index(drop=True)

                            rows1 = st.slider('How much person number to display?', 0, len(likes), 10, key = '2')

                            fig = ff.create_table(user_count.head(int(rows1)), colorscale=colorscale)
                            fig.layout.xaxis.fixedrange = True
                            fig.layout.yaxis.fixedrange = True
                            st.plotly_chart(fig, use_container_width=True)
                    with col3:
                        st.subheader('Engagement Rate')
                        usernames = list(set(tw_df['username'].tolist()))
                        users_df = pd.DataFrame(columns=['username', 'engagement_rate'], index=list(range(len(usernames))))
                        for i, user in enumerate(usernames):
                            user_df = tw_df[tw_df['username']==user]
                            engagement_rate = ((((user_df['likeCount'].sum() + user_df['retweetCount'].sum() + user_df['replyCount'].sum()) / user_df['followersCount'].tolist()[0])) * 100) / len(usernames)
                            if user_df['followersCount'].tolist()[0] == 0:
                                engagement_rate = '-------'
                                users_df.loc[i, :] = [user, engagement_rate]
                            else:
                                users_df.loc[i, :] = [user, str(round(engagement_rate, 2)) + '%']

                        users_df = users_df.sort_values(by=['engagement_rate'], ascending=False).reset_index(drop=True)
                        help = """Engagement rate is a metric used to assess the average number of interactions your social media content receives per follower.

                        Engagement Rate = [Total Engagement(shares, comments, reactions, etc.)/Total Followers x 100%]/Total Users
                        """
                        rows2 = st.slider('How much person number to display?', 0, len(users_df), 10, key='3', help = help)

                        fig = ff.create_table(users_df.head(int(rows2)), colorscale=colorscale)
                        fig.layout.xaxis.fixedrange = True
                        fig.layout.yaxis.fixedrange = True
                        st.plotly_chart(fig, use_container_width=True)



                    # select top hashtags
                    st.title('Select Top 10 Hashtags')
                    hashtags_list = self.hashtags_extract(tw_df)
                    col1, col2 = st.columns((1,2))

                    with col1:
                        freq = nltk.FreqDist(hashtags_list)
                        d = pd.DataFrame({'Hashtag': list(freq.keys()), 'Count': list(freq.values())})
                        d = d.sort_values(by=['Count'], ascending=False).reset_index(drop=True)
                        fig = ff.create_table(d.head(10), colorscale=colorscale)
                        fig.layout.xaxis.fixedrange = True
                        fig.layout.yaxis.fixedrange = True
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        dplot = d.nlargest(columns='Count', n=10)
                        x = dplot['Hashtag'].tolist()
                        y = dplot['Count'].tolist()
                        fig = go.Figure(data=[go.Bar(x=x, y=y, text=y, textposition='inside')])
                        fig.update_traces(marker_color='red', marker_line_color='red', marker_line_width=1.5,opacity=0.8)
                        fig.update_layout(barmode='stack', margin=dict(l=10, r=10, b=10, t=15), hoverlabel=dict(bgcolor="white", font_size=11))
                        fig.update_xaxes(tickangle=-80)
                        fig.layout.xaxis.fixedrange = True
                        fig.layout.yaxis.fixedrange = True
                        st.plotly_chart(fig, use_container_width=True)


    # extract the Hashtags
    def hashtags_extract(self, tweets):
        hashtags = []
        # loop words in the tweet
        for i in range(len(tweets)):
            hashtag = tweets['hashtags'][i]
            if hashtag is not None:
                hashtags.extend(hashtag)

        hashtag_list = [elem.upper() for elem in hashtags]
        return hashtag_list

    @st.cache
    def nlp_analysis(self, tw_nlp, date_picker):
        tw_nlp['Subjectivity'] = tw_nlp['tweet'].apply(self.getSubjectivity)
        tw_nlp['Polarity'] = tw_nlp['tweet'].apply(self.getPolarity)
        tw_nlp['Analysis'] = tw_nlp['Polarity'].apply(self.getAnalysis)

        date, positives, negatives, neutrals = [], [], [], []
        for d in date_picker['date']:
            df = tw_nlp[tw_nlp['date'] == d]
            pos = len(df[df['Analysis'] == 'Positive'])
            net = len(df[df['Analysis'] == 'Neutral'])
            neg = len(df[df['Analysis'] == 'Negative'])
            date.append(d)
            positives.append(pos)
            negatives.append(neg)
            neutrals.append(net)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=date, y=positives, name='Positives'))
        fig.add_trace(go.Bar(x=date, y=negatives, name='Negatives'))
        fig.add_trace(go.Bar(x=date, y=neutrals, name='Neutrals'))
        fig.update_layout(hovermode='x', barmode='stack', margin=dict(l=10, r=10, b=10, t=15))
        fig.layout.xaxis.fixedrange = True
        fig.layout.yaxis.fixedrange = True

        return fig, tw_nlp

    # Create a function to get the subjectivity
    def getSubjectivity(self, text):
        return TextBlob(text).sentiment.subjectivity

    # Create a function to get the polarity
    def getPolarity(self, text):
        return TextBlob(text).sentiment.polarity

    # Create a function to compute the negative, neutral and positive analysis
    def getAnalysis(self, score):
        if score < 0:
            return 'Negative'
        elif score == 0:
            return 'Neutral'
        else:
            return 'Positive'

    def DF_cleaning(self, tweet_df):
        _1, c2, _2 = st.columns(3)
        size = c2.number_input('Number of rows :', min_value=3, max_value=len(tweet_df), value=3, step=3)
        size = int(size)

        st.subheader('Remove urls')
        tweet_df['tweet'] = tweet_df['tweet'].str.replace('http\S+|www.\S+', '', case=False)# just in case texthero cant remove URLs
        st.info('Remove urls... Done')
        st.table(tweet_df['tweet'].head(size))

        st.subheader('Remove mentions')
        tweet_df['tweet'] = tweet_df['tweet'].apply(lambda x: re.sub(r'\@\w+','',x))# remove mentions
        st.info('Remove mentions... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove punctuation')
        tweet_df['tweet'] = tweet_df['tweet'].apply(self.remove_punctuation, args=(''''!"&\'()*+,-./:;<=>?-[\\]^_{|}~`''',))# remove punctuation
        st.info('Remove punctuation... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove diacritics')
        custom_diacritics_pipeline = [preprocessing.remove_diacritics]
        tweet_df['tweet'] = hero.clean(tweet_df['tweet'], pipeline=custom_diacritics_pipeline)# Remove diacritics
        st.info('Remove diacritics... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove stopwords')
        custom_stopwords_pipeline = [preprocessing.lowercase, preprocessing.remove_stopwords]
        tweet_df['tweet'] = hero.clean(tweet_df['tweet'], pipeline=custom_stopwords_pipeline)# remove stopwords
        st.info('Remove stopwords... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove words of length less than 3')
        tweet_df['tweet'] = tweet_df['tweet'].apply(lambda old_string: ' '.join([w for w in old_string.split() if len(w)>3]))  # remove words of length less than 3
        st.info('Remove words of length less than 3... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove digits')
        tweet_df['tweet'] = tweet_df['tweet'].apply(lambda x: re.sub(r'\s\d+\s', ' ', x))# remove digits
        st.info('Remove digits... Done')
        st.table(tweet_df.head(size))

        st.subheader('Remove empty rows')
        tweet_df = tweet_df.replace(r'^s*$', float('NaN'), regex=True)  # Replace blanks by NaN
        tweet_df.dropna(inplace=True)
        st.info('Remove empty rows... Done')
        st.table(tweet_df.head(size))

        st.subheader('stemming')
        custom_stem_pipeline = [preprocessing.stem]
        tweet_df['tweet'] = hero.clean(tweet_df['tweet'], pipeline=custom_stem_pipeline)# stemming
        st.info('stemming... Done')
        st.table(tweet_df.head(size))

        return tweet_df



    def remove_punctuation(self, text, punctuations):
        """custom function to remove the punctuation"""
        return text.translate(str.maketrans('', '', punctuations))

    def porcentage(self, num, total):
        p = num / total
        percentage = "{:.2%}".format(p)
        return percentage


    def display_collections(self):
        if 'nav' not in st.session_state:
            st.session_state.nav = 'Collections'

        if 'file' not in st.session_state:
            st.session_state.file = 'do_data/collections/collections_24h.csv'
            st.session_state.time = '24h'

        if 'twitter_account' not in st.session_state:
            st.session_state.twitter_account = None
        if 'sales_link' not in st.session_state:
            st.session_state.sales_link = None

        if st.session_state.nav == 'Collections':

            st.title("Top Collections ")
            st.markdown("<h3>Rankings for NFT collections. Discover the top NFT collections across multiple protocols including Ethereum, BSC, WAX and Flow <br><br><br></h3>", unsafe_allow_html=True)
            file = 'do_data/collections/collections_all_time.csv'
            st.markdown(annotated_text(("The Data was obtained at the time:", "", "#faa"), " ", str(time.ctime(os.path.getmtime(file)))), unsafe_allow_html=True)
            st.markdown('<br><br>', unsafe_allow_html=True)

            c0, c1, c2, c3, c4 = st.columns((6, 1, 1, 1, 1))
            c1.button("24 hours", key='24 hours', on_click= self.time_nav, args=('24h',))
            c2.button("7 days", key='7 days', on_click= self.time_nav, args=('7d',))
            c3.button("30 days", key='30 days', on_click= self.time_nav, args=('30d',))
            c4.button("All time", key='All time', on_click= self.time_nav, args=('all_time',))

            ###############

            # Number of entries per screen
            N = 20
            # A variable to keep track of which product we are currently displaying
            if 'page_number' not in st.session_state:
                st.session_state.page_number = 0

            data = self.load_data(st.session_state.file)
            if 'df_collection' not in st.session_state:
                st.session_state.df_collection = data

            last_page = len(data) // N
            # Add a next button and a previous button
            prev, next = st.columns([1, 13])
            if next.button("Next"):
                if st.session_state.page_number + 1 > last_page:
                    pass
                else:
                    st.session_state.page_number += 1

            if prev.button("Prev"):
                if st.session_state.page_number - 1 < 0:
                    pass
                else:
                    st.session_state.page_number -= 1

            # Get start and end indices of the next page of the dataframe
            start_idx = st.session_state.page_number * N
            end_idx = (1 + st.session_state.page_number) * N
            # Index into the sub dataframe
            df = data.iloc[start_idx:end_idx]

            st.markdown('-----')

            c1, c2, c3, c4, c44, c5, c6, c7, c8, c9 = st.columns((0.5, 0.3, 1, 1, 1, 1, 0.9, 1, 1, 0.6))
            c1.markdown(annotated_text(('RANK', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c3.markdown(annotated_text(('PRODUCT', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c4.markdown(annotated_text(('SALES (ETH)', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c44.markdown(annotated_text(('SALES (USD)', "", "#ffff"), "", ''), unsafe_allow_html=True)
            if st.session_state.time != 'all_time':
                c5.markdown(annotated_text(('Change (' + st.session_state.time + ')', "", "#ffff"), "", ''),
                            unsafe_allow_html=True)
            else:
                c5.markdown(annotated_text(('OWNERS', "", "#ffff"), "", ''), unsafe_allow_html=True)

            c6.markdown(annotated_text(('BUYERS', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c7.markdown(annotated_text(('TRANSACTIONS', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c8.markdown(annotated_text(('PROTOCOLE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c9.markdown(annotated_text(('ANALYSE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            st.markdown('-----')

            for i in range(df.index[0], df.index[-1]+1):
                RANK = df.loc[i, 'rank']
                PRODUCT = df.loc[i, 'product_name']
                IMAGE = df.loc[i, 'product_image']
                SALES_ETH = df.loc[i, 'sales_eth']
                SALES_USD = df.loc[i, 'sales_usd']
                if st.session_state.time != 'all_time':
                    Change = df.loc[i, 'change']
                    COLOR = df.loc[i, 'change_color']
                else:
                    OWNERS = df.loc[i, 'owners']
                    COLOR = df.loc[i, 'owners_color']

                BUYERS = df.loc[i, 'buyers']
                TRANSACTIONS = df.loc[i, 'Txns']
                PROTOCOLE = df.loc[i, 'protocol']
                sales_link = df.loc[i, 'product_link']
                summary_link = df.loc[i, 'sales_summary_link']

                c1, c2, c3, c4, c44, c5, c6, c7, c8, c9 = st.columns((0.5, 0.3, 1, 1, 1, 1, 0.9, 1, 1, 0.6))
                c1.markdown(annotated_text((str(RANK), "", "#ffff"), "", ''), unsafe_allow_html=True)

                try:
                    c2.image(IMAGE, use_column_width=True)
                except:
                    c2.image("do_data/images/blank.png", use_column_width=True)

                c3.write(PRODUCT)
                c4.write(SALES_ETH)
                c44.write(SALES_USD)

                if COLOR == '#ca2d2d':
                    c5.write('🔻 ' + str(Change))
                elif COLOR == '#1d8843':
                    c5.write('🟩 ' + str(Change))
                elif COLOR == 'gold':
                    c5.write('🟡 ' + str(OWNERS))

                c6.write(BUYERS)
                c7.write(TRANSACTIONS)
                c8.write(PROTOCOLE)

                c9.button("🔍", key='Magnifying Glass ' + str(i), help = SALES_ETH, on_click=self.button_navigation,
                              args=('Analyse',PRODUCT,IMAGE,sales_link,summary_link,))
                st.markdown('-----')

        elif st.session_state.nav == 'Analyse':
            c1, c2, c3 = st.columns((0.3, 3.5, 1))

            try:
                c1.image(st.session_state.img_product, use_column_width=True)
            except:
                c1.image("do_data/images/blank.png", use_column_width=True)

            c2.title(st.session_state.name_product + ' NFTs statistics')
            c2.markdown(st.session_state.name_product + ' sales volume data, graphs & charts ', unsafe_allow_html=True)

            twitter_csv = pd.read_csv("do_data/twitter_accounts/twitter.csv")
            if st.session_state.name_product in twitter_csv['project_name'].tolist():
                with c3:
                    with st.expander('Scrape Tweets From Twitter Account'):
                        st.image("do_data/images/twitter.png", use_column_width=True)
                        tw = twitter_csv[twitter_csv['project_name'] == st.session_state.name_product]['username_account']
                        st.session_state.twitter_account = tw.tolist()[0]
                        st.button('Scrape Tweets From '+ st.session_state.name_product +' Account', key='twitter', on_click=self.button_navigation,
                                args=('Scrape Tweets From Twitter',st.session_state.name_product,))


            df = st.session_state.df_collection
            df = df[df['product_name'] == st.session_state.name_product][['sales_link', 'protocol']]

            st.session_state.sales_link = df['sales_link'].tolist()[0]

            col1, col2, col3 = st.columns((1, 1, 5))
            col1.button('↩️ Collections', key='Home', on_click=self.button_navigation, args=('Collections',))
            st.markdown('<br><br> ', unsafe_allow_html=True)

            if df['protocol'].tolist()[0] == 'Ethereum':
                st.subheader(st.session_state.name_product + ' NFTs Assets')
                st.markdown(annotated_text(("The Data was obtained at the time:", "", "#faa"), " ", str(datetime.datetime.now())), unsafe_allow_html=True)
                st.markdown('<br>', unsafe_allow_html=True)

                link_sales = 'https://www.cryptoslam.io'+st.session_state.sales_link
                df = pd.read_csv('do_data/API/contract_address_list.csv')
                try:
                    contract_address = df.loc[df.sales_link == link_sales,'contract_address'].values[0]
                    etat = 'success'
                    st.markdown(annotated_text(('The NFT contract address for the assets : ', "", "#FFFF33"), " ",  contract_address)+'<br>', unsafe_allow_html=True)

                except:
                    etat = 'error'
                    st.write('Searching for contract address...')
                    self.get_contract_address(link_sales)

                    while True:
                        print('===================> no')
                        time.sleep(2)
                        with open('do_data/API/end_loop.txt', "r") as f:
                            data = f.read()
                            print(data)
                        if data == 'success':
                            etat = 'success'
                            break
                        if data == 'error':
                            break

                    st.markdown(annotated_text(('The NFT contract address for the assets : ', "", "#FFFF33"), " ",  contract_address)+'<br>', unsafe_allow_html=True)


                if etat == 'success':
                    c1, c2 = st.columns(2)
                    assets_number = c1.number_input('Insert Max of assets', min_value=200, value=200, step=100)
                    order_by = c2.selectbox('Filter By: ', ('Sale price', 'Sale count', 'Sale date'), index = 0)
                    st.markdown('<br>', unsafe_allow_html= True)
                    df = pd.read_csv('do_data/API/contract_address_list.csv')
                    contract_address = df.loc[df.sales_link == link_sales, 'contract_address'].values[0]
                    assets = get_assets(contract_address, order_by, int(assets_number), offest=0)
                    st.markdown('<br>', unsafe_allow_html=True)
                    st.markdown('<center>'+annotated_text(('The Number of assets returned : ', "", "#CCCCFF"), " ",  str(len(assets)))+'</center><br>', unsafe_allow_html=True)

                    _1, c1, _2 = st.columns(3)
                    ass_number = c1.slider('How much assets to display?', 0, int(assets_number), 12)

                    j = 1
                    ccc1, ccc2, ccc3, ccc4, ccc5, ccc6 = st.columns(6)
                    i=0
                    for asset in assets:
                        try:
                            if i == ass_number:
                                break
                            i+=1
                        except:
                            pass

                        asset_id = asset['asset_id']
                        asset_name = asset['asset_name']
                        asset_img = asset['asset_img']
                        creator_address = asset['creator_address']
                        owner_address = asset['owner_address']
                        asset_external_link = asset['asset_external_link']

                        traits = str()
                        try:
                            for item in asset['traits']:
                                traits = traits + ' | ' + item['value']
                        except:
                            traits = None

                        num_sales = asset['num_sales']
                        if num_sales != '0':
                            try:
                                asset_last_sale_time = asset['asset_last_sale']['event_timestamp'][:10]
                            except:
                                asset_last_sale_time = '----'
                            try:
                                asset_last_sale_price = asset['asset_last_sale']['total_price']
                            except:
                                asset_last_sale_price = '----'
                            try:
                                payment_token = 'ETH | 1 eth = ' + asset['asset_last_sale']['payment_token']['usd_price']
                            except:
                                payment_token = '----'
                            try:
                                from_ = asset['asset_last_sale']['transaction']['from_account']['address']
                                to_ = asset['asset_last_sale']['transaction']['to_account']['address']
                            except:
                                from_ = '----'
                                to_ = '----'
                        else:
                            asset_last_sale_price = '----'
                            asset_last_sale_time = '----'

                        if j == 1:
                            ccc1.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc1.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc1.image(asset_img, use_column_width=True)
                            ccc1.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc1.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc1.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc1.expander('Owner/Creator'):
                                st.markdown('<center><h4>'+annotated_text(("Owner:", "", "#faa"), "",'')+'</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>'+annotated_text(("Creator:", "", "#faa"), "",'')+'</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)

                        elif j == 2:
                            ccc2.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc2.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc2.image(asset_img, use_column_width=True)
                            ccc2.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc2.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc2.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc2.expander('Owner/Creator'):
                                st.markdown('<center><h4>' + annotated_text(("Owner:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>' + annotated_text(("Creator:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                        elif j == 3:
                            ccc3.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc3.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc3.image(asset_img, use_column_width=True)
                            ccc3.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc3.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc3.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc3.expander('Owner/Creator'):
                                st.markdown('<center><h4>' + annotated_text(("Owner:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>' + annotated_text(("Creator:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                        elif j == 4:
                            ccc4.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc4.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc4.image(asset_img, use_column_width=True)
                            ccc4.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc4.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc4.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc4.expander('Owner/Creator'):
                                st.markdown('<center><h4>' + annotated_text(("Owner:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>' + annotated_text(("Creator:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                        elif j == 5:
                            ccc5.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc5.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc5.image(asset_img, use_column_width=True)
                            ccc5.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc5.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc5.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc5.expander('Owner/Creator'):
                                st.markdown('<center><h4>' + annotated_text(("Owner:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>' + annotated_text(("Creator:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                        elif j == 6:
                            ccc6.markdown('<center><h4>' + annotated_text((asset_id, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            if not asset_name is None:
                                ccc6.markdown('<center><h4>' + annotated_text((asset_name, "", "#1c87c9"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc6.image(asset_img, use_column_width=True)
                            ccc6.markdown('<center><h4>'+annotated_text(("Num Sales: "+str(num_sales), "", "#faa"), "",'') + '</h4></center>', unsafe_allow_html=True)
                            ccc6.markdown('<center><h4>'+annotated_text(("Last sale date:", "", "#faa"), "",'')+'<br>' + str(asset_last_sale_time) + '</h4></center>', unsafe_allow_html=True)
                            ccc6.markdown('<center><h4>'+annotated_text(("Last price:", "", "#faa"), "",'')+'</h4><h6>' + str(asset_last_sale_price) + '</h6></center>', unsafe_allow_html=True)
                            with ccc6.expander('Owner/Creator'):
                                st.markdown('<center><h4>' + annotated_text(("Owner:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)
                                st.markdown('<center><h4>' + annotated_text(("Creator:", "", "#faa"), "",'') + '</h4><p style="font-size:6.5px">' + str(creator_address) + '</p></center>', unsafe_allow_html=True)


                        j+=1
                        if j == 7:
                            j=1
                            st.markdown('-----')
                            ccc1, ccc2, ccc3, ccc4, ccc5, ccc6 = st.columns(6)



                    st.markdown('<br>', unsafe_allow_html=True)
                    # assets to dataframe
                    assets_df = pd.DataFrame(assets)
                    # Getting total number Creators and Owners.
                    st.subheader("There are {} unique creators and There are {} unique owners.".format(len(assets_df['creator_address'].unique()), len(assets_df['owner_address'].unique())))
                    c1, c2 = st.columns(2)
                    # Getting Top 10 Creators
                    with c1.expander('Top 10 Creators'):
                        df_creator = self.get_top_creators(assets_df)
                        st.write(df_creator)

                    # Getting Top 10 Owners
                    with c2.expander('Top 10 Owners'):
                        df_owners = self.get_top_owners(assets_df)
                        st.write(df_owners)

                    #################################################################
                    ###############     Sales API
                    #################################################################
                    st.markdown('<br>', unsafe_allow_html=True)
                    st.subheader(st.session_state.name_product + ' sales')
                    with st.form("sales"):
                        c1, c2 = st.columns(2)
                        sales_number = c1.number_input('Insert Max of sales', min_value=50, value=100, step=100)
                        only_opensea = c2.selectbox('Only from Opensea ', ('true', 'false'), index = 1)

                        submitted_sales = st.form_submit_button("Submit")
                        #submitted_sales = True
                        if submitted_sales:
                            assets_sales = get_sales_assets(contract_address, int(sales_number), only_opensea, offest=0)
                            # sales to dataframe
                            sales_df = pd.DataFrame(assets_sales)
                            if len(sales_df) == 0 :
                                st.warning('**Dataframe is empty** : if "Only from Opensea = true" try change it to "false"')
                            else:
                                with st.expander('Stats about Bundle / Types of Payment'):
                                    colorscale = [[0, 'red'], [.5, '#f2e5ff'], [1, '#ffffff']]
                                    c1, c2 = st.columns(2)
                                    # Getting Stats about Bundle
                                    stats = sales_df.groupby('is_bundle').size().reset_index(name='Count')
                                    fig = ff.create_table(stats, colorscale=colorscale)
                                    fig.layout.xaxis.fixedrange = True
                                    fig.layout.yaxis.fixedrange = True
                                    c1.plotly_chart(fig, use_container_width=True)

                                    # Getting Types of Payment
                                    copy_df = sales_df
                                    copy_df = copy_df[copy_df['is_bundle'] == False]
                                    payement = copy_df.groupby('payment_token').size().reset_index(name='Count')
                                    fig = ff.create_table(payement, colorscale=colorscale)
                                    fig.layout.xaxis.fixedrange = True
                                    fig.layout.yaxis.fixedrange = True
                                    c2.plotly_chart(fig, use_container_width=True)

                                # Getting Top 10 Buyers
                                with st.expander('Top 10 Buyers'):
                                    buyers = []
                                    for buyer_address in sales_df['buyer_address'].value_counts().index[:10]:
                                        buyer_data = {}
                                        buyer_data['buyer_address'] = buyer_address
                                        #buyer_data['buyer_username'] = sales_df[sales_df['buyer_address'] == buyer_address]['buyer_username'].iloc[0]
                                        buyer_data['number_buys'] = len(sales_df[sales_df['buyer_address'] == buyer_address])
                                        buyer_data['min_price'] = sales_df[sales_df['buyer_address'] == buyer_address]['total_price'].min()
                                        buyer_data['max_price'] = sales_df[sales_df['buyer_address'] == buyer_address]['total_price'].max()
                                        #buyer_data['mean_price'] = sales_df[sales_df['buyer_address'] == buyer_address]['total_price'].mean()
                                        buyers.append(buyer_data)
                                    buyers = pd.DataFrame(buyers)
                                    st.table(buyers)

                                # Getting Top 10 Sellers
                                with st.expander('Top 10 Sellers'):
                                    sellers = []
                                    for seller_address in sales_df['seller_address'].value_counts().index[:10]:
                                        seller_data  = {}
                                        seller_data ['seller_address'] = seller_address
                                        #buyer_data['seller_username'] = sales_df[sales_df['seller_address'] == seller_address]['seller_username'].iloc[0]
                                        seller_data ['number_sales'] = len(sales_df[sales_df['seller_address'] == seller_address])
                                        seller_data ['min_price'] = sales_df[sales_df['seller_address'] == seller_address]['total_price'].min()
                                        seller_data ['max_price'] = sales_df[sales_df['seller_address'] == seller_address]['total_price'].max()
                                        #buyer_data['mean_price'] = sales_df[sales_df['seller_address'] == seller_address]['total_price'].mean()
                                        sellers.append(seller_data)
                                    sellers = pd.DataFrame(sellers)
                                    st.table(sellers)

                                # Intersection of Top 10 Buyers and Top 10 sellers
                                with st.expander('Intersection of Top 10 Buyers and Top 10 sellers'):
                                    parsed_buyers, parsed_sellers = buyers[['buyer_address', 'number_buys']], sellers[['seller_address','number_sales']]
                                    parsed_buyers = parsed_buyers.rename(columns={"buyer_address": "address"})
                                    parsed_sellers = parsed_sellers.rename(columns={"seller_address": "address"})
                                    Intersection = pd.merge(parsed_buyers, parsed_sellers, how='inner', on=['address'])
                                    st.table(Intersection)

                                ###########################################################
                                ########   Charts
                                ###########################################################
                                # Parsing dates
                                sales_df['timestamp'] = pd.to_datetime(sales_df['timestamp'])
                                # Converting sales price from WEI to ETH
                                sales_df['total_price'] = sales_df['total_price'] * 10. ** (-18)
                                # Calculating the sale prices in USD
                                sales_df['total_price_usd'] = sales_df['total_price'] * sales_df['usd_price']

                                # Total Number of Sales per Day
                                with st.expander('Total number of sales per Day'):
                                    data = sales_df[['timestamp', 'total_price']].resample('D', on='timestamp').count()['total_price']
                                    data = data.reset_index()

                                    trans = alt.Chart(data).mark_bar().encode(x=alt.X('timestamp', title='DATE'),
                                        y=alt.Y('total_price:Q', title='Number of Sales per Day'), color=alt.value('#db0026'))

                                    text = trans.mark_text(align='left', baseline='middle', dy=-14).encode(
                                        text='total_price:Q')

                                    trans2 = alt.Chart(data).mark_line().encode(x=alt.X('timestamp', title='DATE'),
                                        y=alt.Y('total_price:Q', title='Number of Sales per Day'), color=alt.value('pink'))

                                    trans3 = alt.Chart(data).mark_area(opacity=0.3).encode(x="timestamp:T",
                                        y=alt.Y("total_price:Q", stack=None))

                                    chart = (trans + text + trans2 + trans3)

                                    chart.properties(width=500)
                                    st.altair_chart(chart, use_container_width=True)

                                # Total Sales per Day in ETH
                                with st.expander('Total sales per Day in ETH'):
                                    data = sales_df[['timestamp', 'total_price']].resample('D', on='timestamp').sum()['total_price']
                                    data = data.reset_index()

                                    chart = self.plot_chart_sales(data, 'Total price', 'timestamp', 'total_price')
                                    st.altair_chart(chart, use_container_width=True)

                                # Total Sales per day in USD
                                with st.expander('Total sales per Day in USD'):
                                    data = sales_df[['timestamp', 'total_price_usd']].resample('D', on='timestamp').sum()['total_price_usd']
                                    data = data.reset_index()

                                    chart = self.plot_chart_sales(data, 'Sales in Million USD', 'timestamp', 'total_price_usd')
                                    st.altair_chart(chart, use_container_width=True)

                                # Average Price per Day in ETH
                                with st.expander('Average price per Day in ETH'):
                                    data =sales_df[['timestamp', 'total_price']].resample('D', on='timestamp').mean()['total_price']
                                    data = data.reset_index()

                                    chart = self.plot_chart_sales(data, 'Average Price in ETH', 'timestamp', 'total_price')
                                    st.altair_chart(chart, use_container_width=True)

                                # Floor Price per Day in ETH
                                with st.expander('Floor price per Day in ETH'):
                                    data = sales_df[['timestamp', 'total_price']].resample('D', on='timestamp').min()['total_price']
                                    data = data.reset_index()

                                    chart = self.plot_chart_sales(data, 'Floor price per Day in ETH', 'timestamp', 'total_price')
                                    st.altair_chart(chart, use_container_width=True)

                                # Max Price per Day in ETH
                                with st.expander('Max price per Day in ETH'):
                                    data = sales_df[['timestamp', 'total_price']].resample('D', on='timestamp').max()['total_price']
                                    data = data.reset_index()

                                    chart = self.plot_chart_sales(data, 'Max price per Day in ETH', 'timestamp', 'total_price')
                                    st.altair_chart(chart, use_container_width=True)

                else:
                    st.warning('**We can not find contract address**')
                    _1, c, _2 = st.columns((1, 2, 1))
                    c.image('https://th.bing.com/th/id/R.64f8a3d82a098e29677c6d9a8e359e75?rik=ggvdm6%2b%2fioCNbw&pid=ImgRaw&r=0',use_column_width=True)


            else:
                st.warning('**We can get only NFT Data from collections that use Ethereum protocol**')
                _1, c, _2 = st.columns((1,2,1))
                c.image('https://th.bing.com/th/id/R.64f8a3d82a098e29677c6d9a8e359e75?rik=ggvdm6%2b%2fioCNbw&pid=ImgRaw&r=0', use_column_width=True)


        elif st.session_state.nav == 'Scrape Tweets From Twitter':
            st.title(st.session_state.name_product + ' NFTs statistics')
            st.markdown(st.session_state.name_product + ' Twitter Account ', unsafe_allow_html=True)

            st.markdown(annotated_text(("The Data was obtained at the time:", "", "#faa"), " ", str(datetime.datetime.now())), unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns((1, 1, 5))
            col1.button('↩️ Collections', key='Home', on_click=self.button_navigation, args=('Collections',))
            st.markdown('<br> ', unsafe_allow_html=True)

            user_info = self.user_profile(st.session_state.twitter_account)
            self.display_profile(user_info)

            st.markdown('<br> <br> ', unsafe_allow_html=True)

            self.More_details = st.checkbox('More details on Tweets', value=False, key='5')
            if self.More_details:
                self.select_details()
            self.more_details(st.session_state.twitter_account)



    def plot_chart_sales(self, data, title, x, y):
        trans = alt.Chart(data).mark_bar().encode(x=alt.X(x, title='DATE'),
                                                  y=alt.Y(y+':Q', title=title),
                                                  color=alt.value('#db0026'))

        nearest = alt.selection_single(nearest=True, on='mouseover', encodings=['x', 'y'], empty='none')

        text = trans.mark_point().encode(tooltip=y+':Q', opacity=alt.condition(nearest, alt.value(1),
                                                                                        alt.value(0))).add_selection(nearest)

        trans2 = alt.Chart(data).mark_line().encode(x=alt.X(x, title='DATE'),
                                                    y=alt.Y(y+':Q', title=title),
                                                    color=alt.value('pink'))

        trans3 = alt.Chart(data).mark_area(opacity=0.3).encode(x=x+":T", y=alt.Y(y+":Q", stack=None))

        chart = (trans + text + trans2 + trans3)
        chart.properties(width=500)

        return chart


    def get_top_creators(self, df):
        creators = []
        for creator_address in df['creator_address'].value_counts().index[:10]:
            creator_data = {}
            creator_data['creator_address'] = creator_address
            #creator_data['creator_username'] = df[df['creator_address'] == creator_address]['creator_username'].iloc[0]
            creator_data['number_nft'] = len(df[df['creator_address'] == creator_address])
            creators.append(creator_data)

        return pd.DataFrame(creators)

    def get_top_owners(self, df):
        owners = []
        for owner_address in df['owner_address'].value_counts().index[:10]:
            owner_data = {}
            owner_data['owner_address'] = owner_address
            owner_data['number_nft'] = len(df[df['owner_address'] == owner_address])
            owners.append(owner_data)

        return pd.DataFrame(owners)


    def sales_time_nav(self, time):
        st.session_state.sales_time = time

    def sales_navigation(self, sales_navigation, collection_name = None, collection_url = None):
        st.session_state.sales_navigation = sales_navigation
        st.session_state.collection_name = collection_name
        st.session_state.collection_url = collection_url

    def display_sales(self):
        if 'sales_time' not in st.session_state:
            st.session_state.sales_time = '24h'

        if 'sales_navigation' not in st.session_state:
            st.session_state.sales_navigation = 'Top NFT Sales'

        if st.session_state.sales_navigation == 'Top NFT Sales':
            st.title("Top NFT Sales")
            st.markdown("<h3>This page lists the top NFT protocols and tokens. They are listed by last sale price with the most valuable first and then in descending order. <br><br><br></h3>", unsafe_allow_html=True)
            file = 'do_data/sales/sales_'+st.session_state.sales_time+'.csv'
            st.markdown(annotated_text(("The Data was obtained at the time:", "", "#faa"), " ", str(time.ctime(os.path.getmtime(file)))), unsafe_allow_html=True)
            st.markdown('<br><br>', unsafe_allow_html=True)

            c0, c1, c2, c3, c4 = st.columns((4, 1, 1, 1, 4))
            c1.button("24 hours", key='24 hours', on_click= self.sales_time_nav, args=('24h',))
            c2.button("7 days", key='7 days', on_click= self.sales_time_nav, args=('7d',))
            c3.button("30 days", key='30 days', on_click= self.sales_time_nav, args=('30d',))

            df = pd.read_csv(file)
            df_chart = df.groupby('product_collection').size().reset_index(name='Size')
            x = df_chart['product_collection'].tolist()
            for index in range(len(x)):
                if len(x[index]) > 25:
                    x[index] = x[index][:25] + '...'

            hovertext = [None for i in range(len(x))]
            for index in range(len(x)):
                for nft, col in zip(df.product_name.tolist() ,df.product_collection.tolist()):
                    if col == x[index]:
                        try:
                            hovertext[index]+= ' ||| ' + nft
                        except:
                            hovertext[index] = nft

            y = df_chart['Size'].tolist()

            st.subheader('Number of NFT sold for each collection ('+st.session_state.sales_time+')')

            # Use the hovertext kw argument for hover text
            fig = go.Figure(data=[go.Bar(x=x, y=y, text=y, textposition='inside', hovertext= hovertext)])
            # Customize aspect
            fig.update_traces(marker_color='red', marker_line_color='red', marker_line_width=1.5, opacity=0.8)
            fig.update_layout(barmode='stack' ,margin=dict(l=10, r=10, b=10, t=15), hoverlabel=dict( bgcolor="white", font_size=11))
            fig.update_xaxes(tickangle=-80)
            fig.layout.xaxis.fixedrange = True
            fig.layout.yaxis.fixedrange = True
            st.plotly_chart(fig, use_container_width= True)

            ###############
            st.subheader('Top NFT Sales of the last ' + st.session_state.sales_time)
            st.markdown('-----')
            _, c1, c2, c3, c4, c5, c6 = st.columns((0.4, 0.5, 0.3, 1, 1, 1, 1))
            c1.markdown(annotated_text(('RANK', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c3.markdown(annotated_text(('NFT', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c4.markdown(annotated_text(('COLLECTION', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c5.markdown(annotated_text(('DATE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c6.markdown(annotated_text(('PRICE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            st.markdown('-----')
            for i in range(df.index[0], df.index[-1]+1):
                RANK = df.loc[i, 'rank']
                IMAGE = df.loc[i, 'product_image']
                NFT = df.loc[i, 'product_name']
                COLLECTION = df.loc[i, 'product_collection']
                DATE = df.loc[i, 'date']
                PRICE = df.loc[i, 'price']


                _, c1, c2, c3, c4, c5, c6 = st.columns((0.4, 0.5, 0.3, 1, 1, 1, 1))
                c1.markdown(annotated_text((str(RANK), "", "#ffff"), "", ''), unsafe_allow_html=True)

                try:
                    c2.image(IMAGE, use_column_width=True)
                except:
                    c2.image("do_data/images/blank.png", use_column_width=True)

                c3.write(NFT)
                collection_url = df.loc[i, 'product_collection_link']
                c4.button(COLLECTION, key=COLLECTION+'_'+str(i), on_click=self.sales_navigation,
                              args=('collection sales', COLLECTION, collection_url,))
                c5.write(DATE)
                c6.write(PRICE)
                st.markdown('-----')

        elif st.session_state.sales_navigation == 'collection sales':
            st.title(st.session_state.collection_name+" statistics")

            col1, col2, col3 = st.columns((1, 1, 5))
            col1.button('↩️ Top NFT Sales', on_click=self.sales_navigation, args=('Top NFT Sales',))
            st.markdown('<br><br> ', unsafe_allow_html=True)
            self.get_collections_sales(st.session_state.collection_url, st.session_state.collection_name)
            file = 'do_data/sales/sales_'+st.session_state.collection_name+'.csv'

            time.sleep(0.2)
            while True:
                time.sleep(3)
                if os.path.isfile(file):
                    break

            df = pd.read_csv(file)

            st.markdown(annotated_text(("The Data was obtained at the time:", "", "#faa"), " ", str(time.ctime(os.path.getmtime(file)))), unsafe_allow_html=True)
            st.markdown('<br><br>', unsafe_allow_html=True)

            ###############
            st.subheader('Top Selling '+st.session_state.collection_name+' NFTs of the last 30 days')
            st.markdown('-----')
            _, c1, c2, c3, c4, c5, c6 = st.columns((0.4, 0.5, 0.3, 1, 1, 1, 1))
            c1.markdown(annotated_text(('RANK', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c3.markdown(annotated_text(('NFT', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c4.markdown(annotated_text(('COLLECTION', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c5.markdown(annotated_text(('DATE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            c6.markdown(annotated_text(('PRICE', "", "#ffff"), "", ''), unsafe_allow_html=True)
            st.markdown('-----')
            for i in range(df.index[0], df.index[-1] + 1):
                RANK = df.loc[i, 'rank']
                IMAGE = df.loc[i, 'product_image']
                NFT = df.loc[i, 'product_name']
                COLLECTION = df.loc[i, 'product_collection']
                DATE = df.loc[i, 'date']
                PRICE = df.loc[i, 'price']

                _, c1, c2, c3, c4, c5, c6 = st.columns((0.4, 0.5, 0.3, 1, 1, 1, 1))
                c1.markdown(annotated_text((str(RANK), "", "#ffff"), "", ''), unsafe_allow_html=True)

                try:
                    c2.image(IMAGE, use_column_width=True)
                except:
                    c2.image("do_data/images/blank.png", use_column_width=True)

                c3.write(NFT)
                c4.write(COLLECTION)
                c5.write(DATE)
                c6.write(PRICE)
                st.markdown('-----')
