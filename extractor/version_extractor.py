import scrapy
from scrapy.crawler import CrawlerProcess

class VersionSpider(scrapy.Spider):
    name = 'versions'
    custom_settings = {
        "FEED_FORMAT": "json",
        "FEED_URI": "data/%(name)s/%(time)s.json"
    }
    
    start_urls = ['https://docs.hortonworks.com/HDPDocuments/HDP3/HDP-3.1.0/release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP3/HDP-3.0.1/release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP3/HDP-3.0.0/release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.5/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.4/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.3/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.2/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.1/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.6.0/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.6/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.5/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.4/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.3/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.2/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.1/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.5.0/bk_release-notes/content/comp_versions.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.3/bk_HDP_RelNotes/content/ch_relnotes_v243.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.2/bk_HDP_RelNotes/content/ch_relnotes_v243.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.1/bk_HDP_RelNotes/content/ch_relnotes_v243.html',
                  'https://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.4.0/bk_HDP_RelNotes/content/ch_relnotes_v243.html']

    def parse(self, response):
        if response.url.split("/")[4] == 'HDP3':
            all_ = response.xpath("//section[@class='section']/ul/li/p/text()").getall()
            if len(all_) == 0:
                all_ = response.xpath("//div[@class='body conbody']/ul/li/p/text()").getall()
        else:
            all_ = response.xpath("//div[@class='itemizedlist']/ul/li/p/text()").getall()
        # print(all_)
        for i in all_:
            if i.strip() == '':
                continue
            if i.strip().split().__len__()  < 2:
                continue
            if i.strip().replace("Apache ","").split().__len__() < 2:
                continue
            yield {"Product": i.replace("Apache ","").split()[0], "Version": i.replace("Apache ","").split()[1].replace("+",""), "HDP": response.url.split("/")[5].split("-")[1]}
        

spider = VersionSpider()
process = CrawlerProcess()

process.crawl(spider)
process.start()