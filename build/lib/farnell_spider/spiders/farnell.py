# -*- coding: utf-8 -*-
from copy import deepcopy

import scrapy
from lxml import html, etree
from farnell_spider.items import FarnellSpiderItem
from w3lib.html import remove_tags

class FarnellSpider(scrapy.Spider):
    name = "farnell"
    def __init__(self, **kwargs):
        self.allowed_domains = ["uk.farnell.com"]
        self.product_categories = ['Electrical', 'Wireless Modules & Adaptors', 'Engineering Software']
        self.category_details = []
        self.start_url = 'http://uk.farnell.com/sitemap'
        
        self.all_product_urls = []
        self.product_url =''
        for argument, value in kwargs.items():
            setattr(self, argument, value)

    def start_requests(self):
        item = FarnellSpiderItem()
        if self.product_url:
            print('---------------------******----------------------')
            request = scrapy.Request(self.product_url, callback=self.parse_product_page, dont_filter=True)
            request.meta['item'] = item
            yield request
        else:
            request = scrapy.Request(self.start_url, callback=self.parse_sitemap_page, dont_filter=True)
            request.meta['item'] = item
            yield request

    def parse_sitemap_page(self, response):
        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        for product_category in self.product_categories:
            item_c = deepcopy(item)
            category_url = tree.xpath(u'id("categories")//h2/a[contains(text(),"'+product_category+'")]/@href')[0]
            item_c['trail']= []
            item_c['trail'].append(product_category)
            request = scrapy.Request(category_url, callback=self.parse_sub_category_page, dont_filter=True)
            request.meta['item'] = item_c
            yield request
                
    def parse_sub_category_page(self, response):
        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        is_category_page = tree.xpath(u'//div[@class="categoryContainer"]')
        is_product_listing = tree.xpath(u'//section[@id="listerresultsView"]')
        if is_category_page:
            sub_categories = tree.xpath(u'//div[@class="categoryList"]//li')
            if sub_categories:
                for sub_category in sub_categories:
                    c_item = deepcopy(item)
                    html_string = etree.tostring(sub_category)
                    sub_tree = html.fromstring(html_string)
                    sub_category_url = sub_tree.xpath(u'//a/@href')[0]
                    sub_category_name = sub_tree.xpath(u'//a/text()')[0]
                    c_item['trail'].append(sub_category_name)

                    request = scrapy.Request(sub_category_url, callback=self.parse_sub_category_page, dont_filter=True)
                    request.meta['item'] = c_item
                    request.meta['sub_category_url'] = sub_category_url
                    yield request

        elif is_product_listing:
            sub_category_url = response.meta['sub_category_url']
            request = scrapy.Request(sub_category_url, callback=self.get_product_listing, dont_filter=True)
            request.meta['item'] = item
            yield request
            
    
    def get_product_listing(self, response):
        item = response.meta['item']
        if response.meta.get('all_product_urls'):
            all_product_urls = response.meta.get('all_product_urls')
        else:
            all_product_urls = []

        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        next_page_url = tree.xpath(u'//span[@class="paginNextArrow"]/@href')
        product_urls = tree.xpath(u'//section[@id="listerresultsView"]//tr/td[@class="description"]/a/@href')
        all_product_urls += product_urls

        if next_page_url:
            next_page_url = next_page_url[0]
            request = scrapy.Request(next_page_url, callback=self.parse_product_listing, dont_filter=True)
            request.meta['all_product_urls'] = all_product_urls
            request.meta['item'] = item
            yield request

        else:
            for product_url in all_product_urls:
                request = scrapy.Request(product_url, callback=self.parse_product_page, dont_filter=True)
                request.meta['item'] = item
                yield request

    def parse_product_page(self, response):
        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        item['url']=response.url
        item['title'] = ''.join(tree.xpath('//div[@id="product"]//section/h1/text()|//div[@id="product"]//section/h2/span/text()'))
        yield item
    
# Testing on product_page       
# scrapy crawl farnell -a product_url='http://uk.farnell.com/silicon-labs/etrx357hr-lrs/zigbee-mod-em357-2-4ghz-u-fl-conn/dp/1854237'



# class FarnellSpiderItem(scrapy.Item):
#DONE     url = scrapy.Field() # Url of the product being scraped
#     brand = scrapy.Field() # Product Brand Name
#DONE     title = scrapy.Field() # Product headline containing the brand and product name
#     unit_price = scrapy.Field() # Unit price of the product
#     overview = scrapy.Field() # Product Overview description, usually has advertising copy
#     information = scrapy.Field() # Dict array of specification objects in {name: specname, value: specvalue}
#TODO     manufacturer = scrapy.Field() # Manufacturer
#TODO    manufacturer_part = scrapy.Field() # Manufacturer part number
#     tariff_number = scrapy.Field() # Tariff code/number
#     origin_country = scrapy.Field() # Origin country
#     files = scrapy.Field() # (string list) String array of "Technical Docs" titles (usually PDF or URL titles)
#     file_urls = scrapy.Field() # (string list) String array of "Technical Docs" URLs
#     image_urls = scrapy.Field() # (string list) String Array of additional image urls
#     primary_image_url = scrapy.Field() # (string) URL of the main product image
#DONE     trail = scrapy.Field() # (string list) Ordered string array (highest level category first) of categories
#     pass