import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from selenium import webdriver
from selenium.webdriver.firefox.options import Options # for passing parameters to the webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # for sending keystrokes to the webpages
from ..items import AdmissionxItem

import time


class AdmxSpider(scrapy.Spider):
    name = 'admx'
    allowed_domains = ['admissionx.com']
    item = AdmissionxItem()

    start_urls = ['https://www.admissionx.com/explore/college?country_id[]={}'.format(page) for page in range(18,19)] # just Bangladesh

    def parse(self, response):

        # Vertical Scrolling
        college_links = response.xpath('//h6[@class="collegeNameSearch"]/a/@href').extract()
        for college in college_links:
            yield scrapy.Request(url = college , callback = self.parseCollege) 

        # Horizontal Scrolling
        next_page = response.xpath('//li/a[@rel="next"]/@href').extract_first()     # extract_first() returns just the value not a list
        if next_page is not None:
            yield scrapy.Request(url=next_page)     # if no callback is provided then by default the parse function is called


    def parseCollege(self, response):

        ######################################## Course ################################################################
        courseDic = dict()
        allCourses = list()

        xpath_course_list = '//div[@class="col-md-6 md-margin-bottom-40 margin-top10"]'
        course_list = response.xpath(xpath_course_list).extract()

        for course in course_list:
            course = scrapy.Selector(text=course)    # change to a scrapy object, otherwise it is just a string 

            stream = course.xpath('//div[@class="col-md-4 funny-boxes-img"]/h2[@class="collegecourse"]/a/text()').extract_first()
            courseDic['stream'] = stream.strip() if stream else 'N/A'

            if len(course.xpath('//ul/li/text()').extract()) == 1:
                courseDic['branch'] = 'N/A'
                degree = course.xpath('//ul/li/text()').extract()[0]
                courseDic['degree'] = degree[9:].strip() if degree else 'N/A'

            else: 
                branch = course.xpath('//ul/li/text()').extract()[0]
                courseDic['branch'] = branch[10:].strip() if branch else 'N/A'

                degree = course.xpath('//ul/li/text()').extract()[1]
                courseDic['degree'] = degree[9:].strip() if degree else 'N/A'

            courseType= course.xpath('//div[@class="col-md-5"]/p/text()').extract()[0]
            courseDic['courseType'] = courseType[15:].strip() if courseType else 'N/A'

            try:
                duration = course.xpath('//div[@class="col-md-5"]/p/text()').extract()[1]
                courseDic['duration'] = duration[19:].strip() if duration else 'N/A'    # tag present without value then 'N/A'
            except:
                courseDic['duration'] = 'N/A'

            fee = course.xpath('//div[@class="col-md-3 "]/h2/a/b/text()').extract_first()
            courseDic['fee'] = fee[3:].strip() if fee else 'N/A'

            allCourses.append(courseDic)

        self.item['name'] = (response.xpath('//a[@class="hover-effect college-name-style-black fontSize37"]/text()').extract_first()).strip()
        self.item['profile'] = 'N/A'
        self.item['courses'] = allCourses 
        
        ######################################## Address ################################################################

        firefox_options = Options()
        firefox_options.add_argument('--headless')
        browser = webdriver.Firefox(options=firefox_options)	# won't work if geckodriver is not added to $PATH; complains when I set path to the geckodriver .. but why?
                                        # had to move this lil bastard to /usr/local/bin 
        browser.get(response.url)
        addressBtn = browser.find_element_by_id('addressPartialShowButton')
        addressBtn.click()
        time.sleep(3)
        self.item['address'] = self.parseAddress(browser.page_source)

        ######################################## Profile #################################################################
        profileBtn = browser.find_element_by_id('profilePartialShowButton')
        profileBtn.click()
        time.sleep(3)
        self.item['profile'] = self.parseProfile(browser.page_source)
        browser.close()

        ######################################## Print #################################################################
        yield self.item


    def parseAddress(self, src):

        addresses = scrapy.Selector(text=src).xpath('//div[@class="row margin-bottom-30"]/div[@class="col-md-12"]').extract()
        registered = dict()
        campus = dict()

        for count,address in enumerate(addresses):
            rows = scrapy.Selector(text=address).xpath('//div[@class="row"]').extract()

            if count == 0:  # registered address
               registered['address1'] = scrapy.Selector(text=rows[1]).xpath('//h5/span/text()').extract_first(default='N/A')
               registered['address2'] = scrapy.Selector(text=rows[2]).xpath('//h5/span/text()').extract_first(default='N/A')
               registered['landmark'] = scrapy.Selector(text=rows[3]).xpath('//h5/span/text()').extract_first(default='N/A')
               registered['city'] = (scrapy.Selector(text=rows[4]).xpath('//h5/text()').extract_first())[7:].strip()
               registered['state'] = (scrapy.Selector(text=rows[5]).xpath('//h5/text()').extract_first())[8:].strip()
               registered['country'] = (scrapy.Selector(text=rows[6]).xpath('//h5/text()').extract_first())[10:].strip()
               registered['post'] = scrapy.Selector(text=rows[7]).xpath('//h5/span/text()').extract_first(default='N/A')

            if count == 1:  # registered address
               campus['address1'] = scrapy.Selector(text=rows[1]).xpath('//h5/span/text()').extract_first(default='N/A')
               campus['address2'] = scrapy.Selector(text=rows[2]).xpath('//h5/span/text()').extract_first(default='N/A')
               campus['landmark'] = scrapy.Selector(text=rows[3]).xpath('//h5/span/text()').extract_first(default='N/A')
               campus['city'] = (scrapy.Selector(text=rows[4]).xpath('//h5/text()').extract_first())[7:].strip()
               campus['state'] = (scrapy.Selector(text=rows[5]).xpath('//h5/text()').extract_first())[8:].strip()
               campus['country'] = (scrapy.Selector(text=rows[6]).xpath('//h5/text()').extract_first())[10:].strip()
               campus['post'] = scrapy.Selector(text=rows[7]).xpath('//h5/span/text()').extract_first(default='N/A')

        address = dict()
        address['registered'] = registered
        address['campus'] = campus 

        return address 


    def parseProfile(self, src):

        profile = scrapy.Selector(text=src).xpath('//div[@class = "row padding-top5 padding-bottom5"]').extract()
        prof_lst = list() 

        for item in profile:
            item_lst = scrapy.Selector(text=item).xpath('//h5/text()').extract()
            item_str = ' '.join(item_lst)
            if item_str:
                prof_lst.append(item_str)

        return prof_lst
        
