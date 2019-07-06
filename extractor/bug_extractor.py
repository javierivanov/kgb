from scrapy.spiders import SitemapSpider

class BugSitemapSpider(SitemapSpider):
    name = 'filtered_sitemap_spider'
    allowed_domains = ['docs.hortonworks.com']
    sitemap_urls = ['https://docs.hortonworks.com/HDPDocuments/HDP3/HDP-3.1.0/sitemap.xml']
    
    def parse(self, response):
        htags = ['h3', 'h2', 'h1']
        
        for idx, _ in enumerate(response.xpath("(//*)")): 
            if response.xpath("(//*)[%d]/text()"%(idx+1)).re("[A-Z]+-\d+").__len__() != 0: 
                bug = response.xpath("(//*)[%d]/text()"%(idx+1)).extract()
                additional = response.xpath("(//*)[%d]/following-sibling::*/text()"%(idx+1)).extract()
                additional = [a for a in additional if a.strip().__len__() > 3]

                if additional.__len__() == 0:
                    continue

                title = response.xpath("//title/text()").get()
                if type(bug) == list:
                    continue
                yield {"bug": bug, "additional": additional, "title": title, "url": response._url}
        
        for idx, _ in enumerate(response.xpath("(//p)")):
            if response.xpath("(//p)[%d]"%(idx+1)).re(r'[A-Z]+-\d+').__len__() > 0:
                bug = response.xpath("(//p)[%d]/a/text()"%(idx+1)).get()
                additional = [response.xpath("(//p)[%d]/text()"%(idx+1)).get()]

                title = response.xpath("//title/text()").get()

                if type(bug) == list:
                    continue
                yield {"bug": bug, "additional": additional, "title": title, "url": response._url}