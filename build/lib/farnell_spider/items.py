# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FarnellSpiderItem(scrapy.Item):
    url = scrapy.Field() # Url of the product being scraped
    brand = scrapy.Field() # Product Brand Name
    title = scrapy.Field() # Product headline containing the brand and product name
    unit_price = scrapy.Field() # Unit price of the product
    overview = scrapy.Field() # Product Overview description, usually has advertising copy
    information = scrapy.Field() # Dict array of specification objects in {name: specname, value: specvalue}
    manufacturer = scrapy.Field() # Manufacturer
    manufacturer_part = scrapy.Field() # Manufacturer part number
    tariff_number = scrapy.Field() # Tariff code/number
    origin_country = scrapy.Field() # Origin country
    files = scrapy.Field() # (string list) String array of "Technical Docs" titles (usually PDF or URL titles)
    file_urls = scrapy.Field() # (string list) String array of "Technical Docs" URLs
    image_urls = scrapy.Field() # (string list) String Array of additional image urls
    primary_image_url = scrapy.Field() # (string) URL of the main product image
    trail = scrapy.Field() # (string list) Ordered string array (highest level category first) of categories
    pass
