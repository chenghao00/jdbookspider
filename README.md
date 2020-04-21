# jdbookspider
使用scrapy-redis爬取京东图书

## 图书价格抓取

图书价格在网页源码上无法找到，是通过js加载出来
先搜索价格，通过对比preview，在network中找到对应的http://p.3.cn/prices/mgets? 文件
将其请求的url地址在百度上进行UrlDecode解码
观察后得到http://p.3.cn/prices/mgets?skuIds=J_12508277
需从源码中获取skuids，构造请求得到价格数据
‘’‘python
item['book_sku'] = li.xpath('./div/@data-sku').extract_first()
yield scrapy.Request(
    'http://p.3.cn/prices/mgets?skuIds=J_()'.format(item['book_sku']),
    callback=self.parse_book_price,
    meta={'item': deepcopy(item)}
)

def parse_book_price(self, response):
    item = response.meta['item']
    item['book_price'] = json.loads(response.text)[0]['op']
    # response.text 是'[{"cbf":"0","id":"J_12508277","m":"55.00","op":"55.00","p":"55.00"}]'
    print(item)
    yield item
’‘’
