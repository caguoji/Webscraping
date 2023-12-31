import scrapy
from scrapy_splash import SplashRequest 


lua_script = """
function main(splash, args)
  splash.private_mode_enabled = false
  splash.js_enabled = true
  assert(splash:go(args.url))
  assert(splash:wait(2))

  return {html = splash:html()}
end
""" 

rolex_url = 'https://www.rolex.com'


class RolexspiderSpider(scrapy.Spider):
    name = "rolexspider"
    #allowed_domains = ["www.rolex.com"]
    #start_urls = ["https://www.rolex.com/en-us/watches"]
    
    
    def start_requests(self):
        url = 'https://www.rolex.com/en-us/watches'
        yield SplashRequest(
                    url, 
                    callback=self.parse,
                    endpoint = 'execute',
                    args = {'wait':0.5, 'lua_source':lua_script,url:'https://www.rolex.com/en-us/watches' }
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

            #force render on local host
            splash_link = 'http://localhost:8050/render.html?url='+watch_model_link

           #for each watch type, open all drop down menus to prepare page to be scraped
            #yield response.follow(watch_model_link,callback=self.parse_watch_page)
            yield SplashRequest(splash_link,callback=self.parse_watch_page)

   
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


        #scrape data not in dropdown menu
        other_specs = {
        'model_name' : response.css('section.css-1vaz9md.e11axyq41 h2::text').get(),
        'price' : response.css('p.css-2im8jf.css-1g545ff.e8rn6rx1 span::text').get(),
        #'price2': response.css('div.wv_reveal ::text').get(),
        'reference_number': response.css('p.css-pzm8qd.e1yf0wve6 ::text').getall()[2],
        'model_url':response.url,
        'model_image': response.css('figure.wv_reveal img.css-fmei9v.er6nhxj0 ::attr(srcset)').get().split(',')[0].strip(','),
        'collection':str(response).split('/')[-2]  
        }
        
        print(other_specs)
        #stack both dictionaries together for output
        yield {**specs, **other_specs}
       

