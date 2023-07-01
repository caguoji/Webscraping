import scrapy
from scrapy_selenium import SeleniumRequest
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
#from selenium.webdriver.support import expected_conditions as EC
#import scrapy.selenium_middleware 
#from selenium.webdriver.support.ui import WebDriverWait
# from selenium import webdriver
#import time


rolex_url = 'https://www.rolex.com'


class RolexspiderSpider(scrapy.Spider):
    name = "rolexspider"
    #allowed_domains = ["www.rolex.com"]
    #start_urls = ["https://www.rolex.com/en-us/watches"]
    
    
    def start_requests(self):
        url = 'https://www.rolex.com/en-us/watches'
        yield SeleniumRequest(
                    url=url, 
                    callback=self.parse, 
                    wait_time=2
                    )

    def parse(self, response):
        
        #identify all models
        model_types = response.css('div.dark-theme.css-1bss45e.e1y25pk71') + response.css('div.light-theme.css-1bss45e.e1y25pk71')
        
        #loop through model pages to view page with all watch types for each model
        for model in model_types:   
            link_suffix = model.css('a.inline.reverseIcon.css-17wfajn.eob9b3y0').attrib['href']+'/all-models'

            #there is only one watch type for the air king model 
            if 'air-king' in link_suffix:
                link_suffix = model.css('a.inline.reverseIcon.css-17wfajn.eob9b3y0').attrib['href']
             
            link_suffix = link_suffix.lower().replace(" ","-")
            model_link = rolex_url+link_suffix

            #click on link for each model
            yield response.follow(model_link,callback=self.parse_models_page)


    def parse_models_page(self,response):
        
        #obtain a the list of all watch types for each model
        watches = response.css('div.css-hfsu5e.eyz9ve26').css('ul li a::attr(href)').getall()
       

        for watch in watches:
            watch_link_suffix = watch.replace("'",'')
            watch_model_link = rolex_url + watch_link_suffix
            

           #for each watch type, open all drop down menus to prepare page to be scraped
            yield SeleniumRequest(url=watch_model_link,callback=self.parse_watch_page,script="document.querySelector('.css-1tg8aam e1yf0wve3').click()",wait_time=5)

    
    def parse_watch_page(self,response):
        
        #scrape keys data in dropdown menu
        all_keys = response.css('ul.css-1pwmb5z.e1yf0wve2 h5::text').getall()
        
        #cleaning all keys
        keys = []
        for key in all_keys:
            key= key.replace(' ','_').lower()
            keys.append(key)

        #scrape all key values in dropdown menu
        values = response.css('ul.css-1pwmb5z.e1yf0wve2 p::text').getall()
        #zip keys and values together
        specs = dict(zip(keys,values))

        #time.sleep(3)
        #scrape data not in dropdown menu
        other_specs = {
        
        'model_name' : response.css('section.css-1vaz9md.e11axyq41 h2::text').get(),
        #'Price' : response.xpath('//script/text()').getall() ,
        'reference_number': response.css('p.css-pzm8qd.e1yf0wve6 ::text').getall()[2],
        'model_url':response.url,
        'model_image': response.css('figure.wv_reveal img.css-fmei9v.er6nhxj0 ::attr(srcset)').get().split(',')[0].strip(','),
        'collection':str(response).split('/')[-2]  

        }
        
    

        #stack both dictionaries together for output
        yield {**specs, **other_specs}
       

