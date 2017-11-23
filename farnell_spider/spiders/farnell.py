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
        # self.product_categories = ['Engineering Software',]
        self.category_details = []
        self.start_url = 'http://uk.farnell.com/sitemap'
        
        self.all_product_urls = []
        self.product_url =''
        for argument, value in kwargs.items():
            setattr(self, argument, value)

    def start_requests(self):
        item = FarnellSpiderItem()
        if self.product_url:
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
            request = scrapy.Request(sub_category_url, callback=self.parse_product_listing, dont_filter=True)
            request.meta['item'] = item
            yield request
            
    def clean_field(self, infos, join_by=' '):
        if infos:
            infos = [info.strip().replace('\n', '').replace('\t', '') for info in infos]
            infos = join_by.join(infos)
            return infos
        return None

    def parse_product_listing(self, response):
        item = response.meta['item']
        if response.meta.get('all_product_urls'):
            all_product_urls = response.meta.get('all_product_urls')
        else:
            all_product_urls = []

        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        next_page_url = tree.xpath(u'//span[@class="paginNextArrow"]/a/@href')
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

    def get_product_information(self, tree):
        feature_set_name = tree.xpath('//section/div[contains(.,"Product Information")]/following-sibling::div/dl/dt')
        feature_set_value = tree.xpath('//section/div[contains(.,"Product Information")]/following-sibling::div/dl/dd')

        information = []
        for name, value in zip(feature_set_name,feature_set_value):
            info = {}
            html_string = etree.tostring(name)
            sub_tree = html.fromstring(html_string)
            feature_name = sub_tree.xpath(u'label//text()')

            html_string2 = etree.tostring(value)
            sub_tree2 = html.fromstring(html_string2)
            feature_value = sub_tree2.xpath(u'a//text()')

            if feature_name and feature_value:
                info['name'] = feature_name[0]
                info['value'] = feature_value[0]
                information.append(info)
        return information

    def parse_product_page(self, response):
        tree = html.fromstring(response.body.decode('utf-8'))
        item = response.meta['item']
        item['url'] = response.url
        item['title'] = tree.xpath('//span[@itemprop="name"]/text()')
        # item['title'] = ''.join(tree.xpath('//div[@id="product"]//section/h1/text()|//div[@id="product"]//section/h2/span/text()'))

        manufacturer = tree.xpath(u'//span[@itemprop="http://schema.org/manufacturer"]/text()')
        manufeture_part = tree.xpath(u'//dd[@itemprop="mpn"]/text()')
        brand = tree.xpath(u'//span[@itemprop="http://schema.org/brand"]/text()')
        overview = tree.xpath(u'//div[@itemprop="http://schema.org/description"]/text()') 
        price = tree.xpath(u'//span[@itemprop="price"]/text()')
        files = tree.xpath(u'//ul[@id="technicalData"]/li/a/text()')
        file_url = tree.xpath(u'//ul[@id="technicalData"]/li/a/@href')
        origin_country =  tree.xpath(u'//div/dl/dt[contains(text(),"Country of Origin:")]/following-sibling::dd[1]/text()')
        tariff_number = tree.xpath(u'//div/dl/dt[contains(.,"Tariff No:")]/following-sibling::dd[1]/text()')
        primary_image_url = tree.xpath(u'//img[@id="productMainImage"]/@src') 
        information = self.get_product_information(tree)
        image_urls = tree.xpath('//div[contains(@class,"thumb")]/img/@src')
        item['manufacturer'] = manufacturer[0]
        # if manufacturer:
        #     item['manufacturer'] = manufacturer[0]
        if manufeture_part:
            item['manufacturer_part'] = self.clean_field(manufeture_part[0], join_by='')
        if brand:
            item['brand'] = brand[0]
        if overview:
            item['overview'] = overview[0]
        if price:
            item['unit_price'] = price[0]
        if files:
            item['files'] = [self.clean_field(file, join_by='') for file in files if self.clean_field(file, join_by='')]
        if file_url:
            item['file_urls'] = file_url
        if origin_country:
            item['origin_country'] = self.clean_field(origin_country)
        if tariff_number:
            item['tariff_number'] = self.clean_field(tariff_number[0], join_by='')
        if primary_image_url:
            item['primary_image_url'] = primary_image_url[0]
        if information:
            item['information'] = self.get_product_information(tree)
        if image_urls:
            item['image_urls'] = image_urls
        yield item

# Testing on product_page       
# scrapy crawl farnell -a product_url='http://uk.farnell.com/silicon-labs/etrx357hr-lrs/zigbee-mod-em357-2-4ghz-u-fl-conn/dp/1854237'
# scrapy crawl farnell -a product_url='http://uk.farnell.com/microchip/rn42-i-rm/module-bluetooth-class-2-w-ant/dp/2143310'
# scrapy crawl farnell -a product_url='http://uk.farnell.com/panduit/fdme8rg/din-rail-fiber-optic-enclosure/dp/2363253'
# scrapy crawl farnell -a product_url='http://uk.farnell.com/rf-solutions/725-ip/4-input-add-on-module-telemetry/dp/2759316'