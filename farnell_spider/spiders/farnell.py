# -*- coding: utf-8 -*-
import scrapy


class FarnellSpider(scrapy.Spider):
    name = "farnell"
    allowed_domains = ["farnell.com"]
    start_urls = (
        'http://www.farnell.com/',
    )

    def parse(self, response):
        pass
