import scrapy
from scrapy.http import Request
from urllib.parse import urlparse

class AdmissionXSpider(scrapy.Spider):
    name = 'crawler'
    # allowed_domains = []
    start_urls = [
            'https://www.admissionx.com/explore/college?country_id[0]=13',
            ]

    def parse(self, response):
        urls = response.xpath('//ul[@class="pagination"]/li/a[not(contains(@rel,"next"))]/@href').extract()
        if urls:
            print(urls)
        else:
            print('error~~~~~~')
        for url in urls:
            yield response.follow(url, callback=self.parse_item)

    def parse_item(self, response):
        print('Im there and working!!!~~~~~~~~~~~~~~~~~~~~~~~~~')
        names = response.xpath('//h6[@class="collegeNameSearch"]/a/@title').extract()
        print(names)

        


