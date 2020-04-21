# -*- coding: utf-8 -*-
import scrapy
from copy import deepcopy
import json
import urllib

class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com', 'p.3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    def parse(self, response):
        dt_list = response.xpath('//div[@class="mc"]/dl/dt')
        for dt in dt_list:
            # 获取大分类名词
            item = {}
            item['b_cate'] = dt.xpath('./a/text()').extract_first()
            # 获取小分类，当前dt下一个兄弟节点 第一个dd里的 所有em标签
            em_list = dt.xpath('./following-sibling::dd[1]/em')
            for em in em_list:
                item['s_href'] = em.xpath('./a/@href').extract_first()
                item['s_cate'] = em.xpath('./a/text()').extract_first()
                if item['s_href'] is not None:
                    item['s_href'] = 'https:' + item['s_href']
                    yield scrapy.Request(
                        item['s_href'],
                        callback=self.parse_book_list,
                        meta={'item': deepcopy(item)}
                    )

    def parse_book_list(self, response):
        item = response.meta['item']
        li_list = response.xpath('//div[@id="plist"]/ul/li')
        for li in li_list:
            item["book_img"] = li.xpath(".//div[@class='p-img']//img/@src").extract_first()
            if item["book_img"] is None:
                item["book_img"] = li.xpath(".//div[@class='p-img']//img/@data-lazy-img").extract_first()
            item["book_img"] = "https:" + item["book_img"] if item["book_img"] is not None else None

            item["book_name"] = li.xpath(".//div[@class='p-name']/a/em/text()").extract_first().strip()
            item["book_author"] = li.xpath(".//span[@class='author_type_1']/a/text()").extract()
            item["book_publish_date"] = li.xpath('.//span[@class="p-bi-date"]/text()').extract_first().strip()
            item["book_press"] = li.xpath(".//span[@class='p-bi-store']/a/@title").extract_first()
            # 图书价格在网页源码上无法找到，是通过js加载出来
            # 先搜索价格，通过对比preview，在network中找到对应的http://p.3.cn/prices/mgets? 文件
            # 将其请求的url地址在百度上进行UrlDecode解码
            # 观察后得到http://p.3.cn/prices/mgets?skuIds=J_12508277
            # 需从源码中获取skuids，构造请求得到价格数据
            item['book_sku'] = li.xpath('./div/@data-sku').extract_first()
            yield scrapy.Request(
                'http://p.3.cn/prices/mgets?skuIds=J_()'.format(item['book_sku']),
                callback=self.parse_book_price,
                meta={'item': deepcopy(item)}
            )

        # 实现翻页
        next_url=response.xpath('//a[@class="pn-next"/@href]').extract_first()
        if next_url is not None:
            next_url = urllib.parse.urljoin(response.url,next_url)
            yield scrapy.Request(
                next_url,
                callback=self.parse_book_list,
                meta = {"item":item}
            )

    def parse_book_price(self, response):
        item = response.meta['item']
        item['book_price'] = json.loads(response.text)[0]['op']
        # response.text 是'[{"cbf":"0","id":"J_12508277","m":"55.00","op":"55.00","p":"55.00"}]'
        print(item)
        yield item
