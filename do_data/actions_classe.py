import csv
import os
import re
import pandas as pd
import scrapy
from PIL import Image
from numpy.core._internal import recursive
from scrapy.http import HtmlResponse
from scrapy.pipelines.files import FilesPipeline
from scrapy import Field, signals
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.log import configure_logging
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from twisted.internet import reactor
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

########################################################
########################################################
#               Scrapy : ScrapCollections              #
#                  from cryptoslam.io                  #
########################################################
########################################################

class ScrapCollectionsSpider(scrapy.Spider):

    name = 'collections'
    start_urls = ['https://cryptoslam.io/',]

    def parse(self, response):
        times = ['24h','7d','30d']
        try:
            os.remove('do_data/collections/collections_all_time.csv')
        except:
            pass

        for time in times:
            table = []
            for row in response.xpath('//*[@class="table table-hover js-top-by-sales-table-'+time+' summary-sales-table"]//tbody//tr'):
                name = row.xpath('td[2]/a/span[contains(@class, "summary-sales-table__column-product-name")]/text()').extract_first()
                img = row.xpath('td[2]/a/img/@data-src').extract_first()
                if name == None:
                    name = row.xpath('td[2]/span/span/text()').extract_first()
                    img = row.xpath('td[2]/span/img/@data-src').extract_first()

                if row.xpath('td[5]/span/@style').extract_first()==None:
                    break

                dict_row = {
                    'rank' : row.xpath('td[1]/text()').extract_first(),
                    'product_link' : row.xpath('td[2]/a/@href').extract_first(),
                    'product_image' : img,
                    'product_name' : name,
                    'protocol' : row.xpath('td[3]/img/@title').extract_first(),
                    'sales_eth' : row.xpath('td[4]/span/@title').extract_first(),
                    'sales_summary_link' : row.xpath('td[4]/span/a/@href').extract_first(),
                    'sales_usd' : row.xpath('td[4]/span/a/span/text()').extract_first(),
                    'change_color' : row.xpath('td[5]/span/@style').extract_first()[7:14],
                    'change' : re.sub('(\xa0)|(\n)|(\r)|(\")|(\')','',str(row.xpath('td[5]/span/text()').extract_first())),
                    'buyers' : row.xpath('td[6]/text()').extract_first(),
                    'sales_link' : row.xpath('td[7]/a/@href').extract_first(),
                    'Txns' : re.sub('(\xa0)|(\n)|(\r)|(\")|(\')|(\s+)','',str(row.xpath('td[7]/a/text()').extract_first()))
                }
                table.append(dict_row)

            pd.DataFrame(table).to_csv(r'do_data/collections/collections_'+time+'.csv', index=False)

        # all time ########################################
        table = []
        for row in response.xpath('//*[@class="table table-hover js-top-by-sales-table-all summary-sales-table"]//tbody//tr'):
            name = row.xpath('td[2]/a/span[contains(@class, "summary-sales-table__column-product-name")]/text()').extract_first()
            img = row.xpath('td[2]/a/img/@data-src').extract_first()
            if name == None:
                name = row.xpath('td[2]/span/span/text()').extract_first()
                img = row.xpath('td[2]/span/img/@data-src').extract_first()

            if row.xpath('td[6]/a/text()').extract_first() == None:
                break

            dict_row = {
                'rank': row.xpath('td[1]/text()').extract_first(),
                'product_link': row.xpath('td[2]/a/@href').extract_first(),
                'product_image': img,
                'product_name': name,
                'protocol': row.xpath('td[3]/img/@title').extract_first(),
                'sales_eth': row.xpath('td[4]/span/@title').extract_first(),
                'sales_summary_link': row.xpath('td[4]/span/a/@href').extract_first(),
                'sales_usd': row.xpath('td[4]/span/a/span/text()').extract_first(),
                'owners_color': 'gold',
                'owners': row.xpath('td[7]/text()').extract_first(),
                'buyers': row.xpath('td[5]/text()').extract_first(),
                'sales_link': row.xpath('td[6]/a/@href').extract_first(),
                'Txns': re.sub('(\xa0)|(\n)|(\r)|(\")|(\')|(\s+)', '', str(row.xpath('td[6]/a/text()').extract_first()))
            }
            table.append(dict_row)

        df = pd.DataFrame(table)
        df.to_csv(r'do_data/collections/collections_all_time.csv', index=False)


# change images name
class CustomImageNamePipeline(ImagesPipeline): #I copied this code from the website
    def get_media_requests(self, item, info):
        for image in item.get('image_urls', []):
            if len(image["url"]) !=0:
                yield scrapy.Request(image["url"], meta={'image_name': image["name"]})

    def file_path(self, request, response=None, info=None):
        return '%s.jpg' % request.meta['image_name']


########################################################
########################################################
#       Scrapy + Selenium : CollectionsStatistics      #
#                  from cryptoslam.io                  #
########################################################
########################################################

class ScrapCollectionsStatisticsSpider(scrapy.Spider):
    name = 'CollectionsStatistics'

    def __init__(self, filename, start_urls):
        self.filename = filename
        try:
            os.remove("do_data/stats/"+self.filename+".png")
        except:
            pass
        self.start_urls = [start_urls,]
        option = webdriver.ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--incognito')
        option.add_argument('--headless')
        option.add_argument('--start-maximized')

        try:
            self.driver = webdriver.Chrome(
                executable_path="C:/Users/hp/.wdm/drivers/chromedriver/win32/91.0.4472.101/chromedriver.exe",
                options=option)
        except:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)


    def parse(self, response):
        self.driver.get(response.url)
        #the element with longest height on page
        ele = self.driver.find_element_by_id("statistics-row")
        total_height = ele.size["height"] + 1000
        self.driver.set_window_size(1500, total_height)  # the trick
        sleep(1)
        self.driver.save_screenshot("do_data/stats/full.png")
        location = ele.location
        size = ele.size
        x = location['x']
        y = location['y']
        w = x + size['width']
        h = y + size['height']
        fullImg = Image.open("do_data/stats/full.png")
        cropImg = fullImg.crop((x, y, w, h))
        cropImg.save("do_data/stats/"+self.filename+".png")
        self.driver.close()
        self.driver.quit()



########################################################
########################################################
#           Scrapy+Selenium:get SalesVolume            #
#                  from Cryptoslam.io                  #
########################################################
########################################################
import os.path

class ScrapSalesVolumeDataSpider(scrapy.Spider):
    name = 'sales volume data'

    custom_settings = {
        'DOWNLOAD_DELAY': 0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider

    def spider_opened(self, spider):
        option = webdriver.ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--incognito')
        option.add_argument('--headless')
        option.add_argument('--start-maximized')

        try:
            self.driver = webdriver.Chrome(
                executable_path="C:/Users/hp/.wdm/drivers/chromedriver/win32/91.0.4472.101/chromedriver.exe",
                options=option)
        except:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

    def spider_closed(self, spider):
        self.driver.close()

    def __init__(self, start_urls, filename):
        self.start_urls = start_urls
        self.filename = filename
        self.table = []
        self.header = ['Date', 'Sales (USD)', 'Sales (ETH)', 'Unique Buyers', 'Total Transactions', 'Avg Sale (USD)', 'Avg Sale (ETH)']
        self.df = pd.DataFrame(columns=self.header)

        file_exists = os.path.isfile('sales_summary/'+self.filename+'.csv')
        if file_exists:
            with open('sales_summary/'+self.filename+'.csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerow(self.header)
                f.close()
        else:
            with open('sales_summary/'+self.filename+'.csv', 'w') as f:
                f.truncate()
                writer = csv.writer(f)
                writer.writerow(self.header)
                f.close()


    def to_text(self, element):
        return element.get_attribute("innerText")

    def get_attribute_href(self, element):
        return element.get_attribute('href')

    def parse(self, response):
        self.driver.get(response.url)
        data_link = list(map(self.get_attribute_href, self.driver.find_elements_by_xpath('//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[2]/a')))
        for link in data_link:
            yield scrapy.Request(link, callback=self.parse_link)

    def parse_link(self, response):
        self.driver.get(response.url)
        date = list(map(self.to_text, self.driver.find_elements_by_xpath('//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[2]')))
        sales_usd = list(map(self.to_text, self.driver.find_elements_by_xpath( '//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[3]')))
        sales_eth = list(map(self.to_text, self.driver.find_elements_by_xpath( '//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[4]')))
        unique_bayers = list(map(self.to_text, self.driver.find_elements_by_xpath('//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[5]')))
        total_transactions = list(map(self.to_text, self.driver.find_elements_by_xpath( '//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[6]')))
        avg_sales_usd = list(map(self.to_text, self.driver.find_elements_by_xpath( '//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[7]')))
        avg_sales_eth = list(map(self.to_text, self.driver.find_elements_by_xpath( '//*[@id="table"]/tbody/tr[contains(@role, "row")]/td[8]')))

        df = pd.DataFrame(list(zip(date, sales_usd, sales_eth, unique_bayers, total_transactions, avg_sales_usd, avg_sales_eth)), columns=self.header)
        df.loc[df.Date == 'Total', 'Date'] = 'Total : ' + str(df.loc[df.Date != 'Total', 'Date'][0][0:3]) + str(df.loc[df.Date != 'Total', 'Date'][0][-4:])
        df.to_csv(r'sales_summary/'+self.filename+'.csv', mode='a', index=False, header=False)
        

########################################################
########################################################
#    Scrapy+Selenium:get projects twitter accounts     #
########################################################
########################################################

from urllib.parse import urljoin
from selenium.common.exceptions import NoSuchElementException

class tweeter_accounts(scrapy.Spider):
    name = 'sales volume data'
    start_urls = ['https://dappradar.com/nft/collections/'+str(page) for page in range(1,10)]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider

    def spider_opened(self, spider):
        option = webdriver.ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--incognito')
        option.add_argument('--headless')
        option.add_argument('--start-maximized')
        option.add_argument("--kiosk")

        try:
            self.driver = webdriver.Chrome(
                executable_path="C:/Users/hp/.wdm/drivers/chromedriver/win32/91.0.4472.101/chromedriver.exe",
                options=option)
        except:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

    def spider_closed(self, spider):
        self.driver.close()

    custom_settings = {
            'DOWNLOAD_DELAY': 0,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1
        }
    def get_attribute_href(self, element):
        return element.get_attribute('href')

    def parse(self, response):
        self.driver.get(response.url)
        links = list(map(self.get_attribute_href, self.driver.find_elements_by_xpath('//*[@id="root"]/div/div[1]/div[4]/section/div[2]/div[contains(@d, "row")]/div[2]/div[2]/a')))
        for link in links:
            url = urljoin(response.url, link)
            yield scrapy.Request(url, callback=self.parse_twitter)

    def check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def parse_twitter(self, response):
        self.driver.get(response.url)
        if self.check_exists_by_xpath('//*[@id="root"]/div/div[1]/div[2]/section/div[2]/div[1]/div[2]/ul/li[1]/div/a'):

            project_name = self.driver.find_element_by_xpath('//*[@id="root"]/div/div[1]/div[2]/section/div[2]/div[1]/div[2]/h1').text
            twitter_url = self.driver.find_element_by_xpath('//*[@id="root"]/div/div[1]/div[2]/section/div[2]/div[1]/div[2]/ul/li[1]/div/a').get_attribute('href')
            yield {'project_name': project_name,
                   'twitter_url': twitter_url}



########################################################
########################################################
#               Scrapy : Top NFT Sales                #
########################################################
########################################################
class ScrapSalesSpider(scrapy.Spider):
    name = 'sales'
    start_urls = ["https://www.nft-stats.com/top-sales/{}".format(page) for page in ['24h', '7d', '30d']]
    try:
        os.remove('do_data/sales/sales_24h.csv')
    except:
        pass
    def parse(self, response):
        print(str(response.url))
        i, table = 0, []
        for row in response.xpath('//*[@id="__layout"]//div//div[2]//div[2]//table//tr'):
            if i ==0:
                i+=1
                continue
            dict_row = {
                'rank': re.sub('(\xa0)|(\n)|(\")|(\s+)','',row.xpath('td[1]/text()').extract_first()),
                'product_image': row.xpath('td[2]/div/img/@src').extract_first(),
                'product_link': row.xpath('td[2]/a/@href').extract_first(),
                'product_name': row.xpath('td[2]/a/text()').extract_first(),
                'product_collection': row.xpath('td[3]/a/text()').extract_first(),
                'product_collection_link': row.xpath('td[3]/a/@href').extract_first(),
                'date': row.xpath('td[4]/text()').extract_first(),
                'price': row.xpath('td[5]/text()').extract_first()
            }
            table.append(dict_row)

        df = pd.DataFrame(table)
        if str(response.url)[-3:] == '24h':
            df.to_csv(r'do_data/sales/sales_24h.csv', index=False)
        elif str(response.url)[-3:] == '30d':
            df.to_csv(r'do_data/sales/sales_30d.csv', index=False)
        else:
            df.to_csv(r'do_data/sales/sales_7d.csv', index=False)



########################################################
########################################################
#               Scrapy : Top NFT Sales                #
########################################################
########################################################
class ScrapCollectionSalesSpider(scrapy.Spider):
    name = 'CollectionSales'

    def __init__(self, start_urls, filename):
        self.start_urls = ['https://www.nft-stats.com'+start_urls,]
        self.filename = filename
        try:
            os.remove('do_data/sales/sales_'+self.filename+'.csv')
        except:
            pass

    def parse(self, response):
        i, table = 0, []
        for row in response.xpath('//*[@id="__layout"]//div//div[2]//div[9]//table//tr'):
            if i ==0:
                i+=1
                continue
            dict_row = {
                'rank': re.sub('(\xa0)|(\n)|(\")|(\s+)','',row.xpath('td[1]/text()').extract_first()),
                'product_image': row.xpath('td[2]/div/img/@src').extract_first(),
                'product_name': row.xpath('td[2]/a/text()').extract_first(),
                'product_collection': row.xpath('td[3]/a/text()').extract_first(),
                'date': row.xpath('td[4]/text()').extract_first(),
                'price': row.xpath('td[5]/text()').extract_first()
            }
            table.append(dict_row)

        df = pd.DataFrame(table)
        df.to_csv(r'do_data/sales/sales_'+self.filename+'.csv', index=False)




########################################################
########################################################
#       Scrapy + Selenium : Scrap Transactions         #
#                  from cryptoslam.io                  #
########################################################
########################################################

class ScrapTxnsSpider(scrapy.Spider):
    name = 'transcation'
    def __init__(self, start_urls, tx_number):
        self.start_urls = [start_urls,]
        self.tx_number = tx_number
        try:
            os.remove('do_data/transactions/NFT_Transactions.csv')
        except:
            pass
        option = webdriver.ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--incognito')
        option.add_argument('--headless')
        option.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")

        try:
            self.driver = webdriver.Chrome(
                executable_path="C:/Users/hp/.wdm/drivers/chromedriver/win32/91.0.4472.101/chromedriver.exe", options=option)
        except:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

    def parse(self, response):
        self.driver.get(response.url)
        self.driver.execute_script("document.body.style.zoom='50%'")
        sleep(0.2)
        # click submit button
        more = self.driver.find_elements_by_xpath('//*[@id="table_length"]/label/select')[0].find_element_by_xpath('option[3]')
        more.click()

        rows = self.driver.find_elements_by_xpath('//*[@id="table"]/tbody/tr')
        while True:
                if (len(rows)) < 250 :
                    sleep(0.6)
                    rows = self.driver.find_elements_by_xpath('//*[@id="table"]/tbody/tr')
                else:
                    break

        response = HtmlResponse(url="my HTML string", body=str(self.driver.page_source), encoding='utf-8')
        for i, attr in enumerate(response.xpath('//*[@id="table"]/thead/tr/th')):
            index = str(i + 1)
            if attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "Sold")]'):
                date_index = index
            elif attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "NFT")]'):
                nft_index = index
            elif attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "Price")]'):
                price_index = index
            elif attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "USD")]'):
                usd_index = index
            elif attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "Seller")]'):
                seller_index = index
            elif attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "Buyer")]'):
                buyer_index = index

        i, table = 0, []
        for row in response.xpath('//*[@id="table"]/tbody//tr[contains(@role, "row")]'):
            if i == 0:
                i += 1
                continue
            date = row.xpath('td[' + date_index + ']//a//text()').extract_first()
            if date == None:
                date = row.xpath('td[' + date_index + ']//text()').extract_first()
            dict_row = {
                'date': date,
                'hash_add_etherscan': row.xpath('td[' + date_index + ']//a//@href').extract_first(),
                'mint_link_cryptoslam': 'https://www.cryptoslam.io' + row.xpath('td[' + nft_index + ']//a//@href').extract_first(),
                'nft': re.sub('(\xa0)|(\n)|(\")|(\s+)', ' ',row.xpath('td[' + nft_index + ']//a//b//text()').extract_first()),
                'price_eth': re.sub('(\xa0)|(\n)|(\")|(\s+)', ' ',row.xpath('td[' + price_index + ']/text()').extract_first()),
                'price_usd': row.xpath('td[' + usd_index + ']/text()').extract_first(),
                'seller_profil_cryptoslam': 'https://www.cryptoslam.io' + row.xpath('td[' + seller_index + ']//a//@href').extract_first(),
                'seller_add': row.xpath('td[' + seller_index + ']//a//@data-original-title').extract_first(),
                'buyer_profil_cryptoslam': 'https://www.cryptoslam.io' + row.xpath('td[' + buyer_index + ']//a//@href').extract_first(),
                'buyer_add': row.xpath('td[' + buyer_index + ']//a//@data-original-title').extract_first()
            }
            table.append(dict_row)

        df = pd.DataFrame(table)
        df.to_csv("do_data/transactions/NFT_Transactions.csv", index=False)
        self.driver.close()


########################################################
########################################################
#       Scrapy + Selenium + web3 + Opensea API:        #
#               get contract addresses                 #
########################################################
########################################################
import requests
from web3 import Web3

class ScrapContractAddresseSpider(scrapy.Spider):
    name = 'transcation'

    def __init__(self, start_urls):
        with open('do_data/API/end_loop.txt', "w") as myfile:
            myfile.write('loading..')
        self.start_urls = [start_urls, ]
        option = webdriver.ChromeOptions()
        option.add_argument('--ignore-certificate-errors')
        option.add_argument('--incognito')
        option.add_argument('--headless')
        option.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
        try:
            self.driver = webdriver.Chrome(
                executable_path="C:/Users/hp/.wdm/drivers/chromedriver/win32/91.0.4472.101/chromedriver.exe",
                options=option)
        except:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

    def verify_address(self, address):
        len_address = []
        for item in address:
            querystring = {"asset_contract_address": item, "order_direction": "desc", "offset": "0", "limit": "1"}
            response = requests.request("GET", "https://api.opensea.io/api/v1/assets", params=querystring)
            len_address.append(len(response.json()['assets']))

        new_list = []
        for i, l in enumerate(len_address):
            if l == 1:
                new_list.append(address[i])

        return new_list

    def parse(self, response):
        self.driver.get(response.url)
        response = HtmlResponse(url="my HTML string", body=str(self.driver.page_source), encoding='utf-8')

        # get contract address from ethereum protocol
        for i, attr in enumerate(response.xpath('//*[@id="table"]/thead/tr/th')):
            index = str(i + 1)
            if attr.xpath('//*[@id="table"]/thead/tr/th[' + index + '][contains(@aria-label, "Sold")]'):
                date_index = index
                break

        try:
            row = response.xpath('//*[@id="table"]/tbody//tr[contains(@role, "row")][2]//td[' + date_index + ']//a//@href').extract_first()
        except:
            row = None
            with open('do_data/API/end_loop.txt', "w") as myfile:
                myfile.write('error')

        try:
            if not row.startswith('https://etherscan.io/tx/'):
                row = None
                with open('do_data/API/end_loop.txt', "w") as myfile:
                    myfile.write('error')
        except:
            pass

        if row != None:
            hash_transaction = re.sub('https://etherscan.io/tx/', '', row)
            # print(hash_transaction)
            sales_link = self.start_urls[0]
            try:
                w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/9318a8d295074b5cb3f35dba6e0f647d'))
                rep = w3.eth.get_transaction_receipt(hash_transaction)
                address_list = []
                for log in rep.logs:
                    address_list.append(log.address)

                contract_address = list(dict.fromkeys(address_list))
                contract_address = self.verify_address(contract_address)
                print(contract_address)
                df = pd.DataFrame([[sales_link, contract_address[0]]], columns=['sales_link', 'contract_address'])
                df.to_csv(r'do_data/API/contract_address_list.csv', mode='a', index=False, header=False)

                with open('do_data/API/end_loop.txt', "w") as myfile:
                    myfile.write('success')
            except:
                print('error : hash transaction not found')
                with open('do_data/API/end_loop.txt', "w") as myfile:
                    myfile.write('error')

        self.driver.close()




########################################################
########################################################
#                     Opensea API:                     #
#           get assets by contract address             #
########################################################
########################################################

def parse_asset_data(asset_dict):
    asset_id = asset_dict['token_id']
    asset_name = asset_dict['name']
    try:
        asset_img = asset_dict['image_url']
    except:
        asset_img = None
    try:
        asset_external_link = asset_dict['external_link']
    except:
        asset_external_link = None
    try:
        asset_last_sale = asset_dict['last_sale']
    except:
        asset_last_sale = None
    try:
        creator_username = asset_dict['creator']['user']['username']
    except:
        creator_username = None
    try:
        creator_address = asset_dict['creator']['address']
    except:
        creator_address = None
    try:
        owner_username = asset_dict['owner']['user']['username']
    except:
        owner_username = None
    try:
        owner_address = asset_dict['owner']['address']
    except:
        owner_address = None
    traits = asset_dict['traits']
    num_sales = int(asset_dict['num_sales'])

    result = {'asset_id': asset_id,
              'asset_name': asset_name,
              'asset_img': asset_img,
              'creator_username': creator_username,
              'creator_address': creator_address,
              'owner_username': owner_username,
              'owner_address': owner_address,
              'traits': traits,
              'num_sales': num_sales,
              'asset_last_sale': asset_last_sale,
              'asset_external_link': asset_external_link}

    return result

import streamlit as st
@st.cache
def get_assets(address, order_by, assets_number, offest=0):
    assets_list = []
    delta = assets_number//50
    order_by = re.sub(' ','_',order_by)
    for i in range(offest, offest + delta):
        querystring = {
            "asset_contract_address": address,
            "order_by": order_by.lower(),
            "order_direction": "desc",
            "offset": str(i * 50),
            "limit": "50"}
        response = requests.request("GET", "https://api.opensea.io/api/v1/assets", params=querystring)
        if response.status_code != 200:
            print('error')
            break

        # Getting assets data
        assets = response.json()['assets']

        if assets == []:
            break

        # Parsing assets data
        parsed_assets = [parse_asset_data(asset) for asset in assets]
        assets_list.extend(parsed_assets)

    return assets_list



def parse_sale_data(sale_dict):
    is_bundle = False
    if sale_dict['asset'] != None:
        asset_id = sale_dict['asset']['token_id']
    elif sale_dict['asset_bundle'] != None:
        asset_id = [asset['token_id'] for asset in sale_dict['asset_bundle']['assets']]
        is_bundle = True
    try:
        seller_address = sale_dict['seller']['address']
    except:
        seller_address = None
    try:
        buyer_address = sale_dict['winner_account']['address']
    except:
        buyer_address = None
    try:
        seller_username = sale_dict['seller']['user']['username']
    except:
        seller_username = None
    try:
        buyer_username = sale_dict['winner_account']['user']['username']
    except:
        buyer_username = None
    timestamp = sale_dict['transaction']['timestamp']
    total_price = float(sale_dict['total_price'])
    payment_token = sale_dict['payment_token']['symbol']
    usd_price = float(sale_dict['payment_token']['usd_price'])
    transaction_hash = sale_dict['transaction']['transaction_hash']

    result = {'is_bundle': is_bundle,
              'asset_id': asset_id,
              'seller_address': seller_address,
              'buyer_address': buyer_address,
              'buyer_username': buyer_username,
              'seller_username': seller_username,
              'timestamp': timestamp,
              'total_price': total_price,
              'payment_token': payment_token,
              'usd_price': usd_price,
              'transaction_hash': transaction_hash}

    return result


@st.cache
def get_sales_assets(address, sales_number, only_opensea, offest=0):
    sales_list = []
    delta = sales_number//50
    for i in range(offest, offest + delta):
        querystring = {"asset_contract_address": address,
                       "event_type": "successful",
                       "only_opensea": only_opensea,
                       "offset": i * 50,
                       "limit": "50"}

        headers = {"Accept": "application/json"}
        response = requests.request("GET", "https://api.opensea.io/api/v1/events", headers=headers, params=querystring)

        if response.status_code != 200:
            print('error')
            break

        # Getting sales data
        sales = response.json()['asset_events']

        if sales == []:
            break

        # Parsing assets data
        parsed_sales = [parse_sale_data(sale) for sale in sales]
        sales_list.extend(parsed_sales)

    return sales_list
