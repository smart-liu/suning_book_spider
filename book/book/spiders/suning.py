# -*- coding: utf-8 -*-
import scrapy
import re
from copy import deepcopy


class SuningSpider(scrapy.Spider):
    name = 'suning'
    allowed_domains = ['snbook.suning.com']
    start_urls = ['http://snbook.suning.com/web/trd-fl/999999/0.htm']

    def parse(self, response):
        li_list = response.xpath("//ul[@class='ulwrap']/li")
        for li in li_list:
            item = {}
            item["b_title"] = li.xpath(".//div[1]/a/text()").extract_first()  # 大标题
            print("大标题", item["b_title"])
            # 遍历小标题
            s_title_list = li.xpath(".//div[2]/a")
            for s_title in s_title_list:
                item["s_title"] = s_title.xpath(".//text()").extract_first()  # 小标题
                print("小标题：", item["s_title"])
                item["s_title_url"] = s_title.xpath(".//@href").extract_first()  # 小标题部分url
                s_title_url = "http://snbook.suning.com" + item["s_title_url"]
                yield scrapy.Request(
                    s_title_url,
                    callback=self.parse_s_title_url,
                    meta={"item": deepcopy(item)}
                )

    def parse_s_title_url(self, response):
        """处理小标题的内容"""

        item = response.meta["item"]
        # 书列表
        book_list = response.xpath("//ul[@class='clearfix']/li")
        for book in book_list:
            item["book_title"] = book.xpath(".//div[@class='book-title']/a/text()").extract_first()  # 书名
            item["book_detail_url"] = book.xpath(".//div[@class='book-title']/a/@href").extract_first()  # 书名
            item["book_author"] = book.xpath(".//div[@class='book-author']/a/text()").extract_first()  # 出版社
            item["book_publish"] = book.xpath(".//div[@class='book-publish']/a/text()").extract_first()  # 作者
            item["book_discrip"] = book.xpath(".//div[@class='book-descrip c6']/text()").extract_first()  # 简介
            # 请求详情页的地址
            yield scrapy.Request(
                item["book_detail_url"],
                callback=self.parse_detail_url,
                meta={"item": deepcopy(item)}
            )

        # 当前页和总页数
        page_total = int(re.findall(r'pagecount=(\d+)', response.body.decode())[0])
        page_current = int(re.findall(r'currentPage=(\d+)', response.body.decode())[0])
        print("第{}页".format(page_current))
        # 判断是否有下一页
        if page_current < page_total:
            next_url = "http://snbook.suning.com" + item["s_title_url"] + "?pageNumber={}&sort=0".format(page_current+1)
            yield scrapy.Request(
                next_url,
                callback=self.parse_s_title_url,
                meta={"item": deepcopy(item)}
            )

    def parse_detail_url(self, response):
        """处理详情页的信息"""
        item = response.meta["item"]
        item["book_price"] = re.findall(r"\"bp\":'(.*?)'", response.body.decode())[0]
        yield item