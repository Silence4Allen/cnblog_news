import json
import re
from urllib import parse

import scrapy
from scrapy import Request
import requests
from scrapy.loader import ItemLoader

from cnblog_news.items import CnblogNewsItem, NewsItemLoader
from cnblog_news.utils import common


class CnblogNewsSpiderSpider(scrapy.Spider):
    name = 'cnblog_news_spider'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):
        """
        1.获取新闻列表页中的新闻url并交给scrapy进行下载后调用相应的解析方法
        2.获取下一页的url并交给scrapy进行下载，下载完成后交给parse继续跟进
        :param response:
        :return:
        """
        post_nodes = response.xpath('//*[@id="news_list"]//div[@class="news_block"]')
        for post_node in post_nodes:
            image_url = post_node.xpath('.//*[@class="entry_summary"]//img/@src').extract_first('')
            if image_url.startswith("//"):
                image_url = 'http:' + image_url
            post_url = post_node.xpath('.//h2/a/@href').extract_first('')
            yield Request(
                url=parse.urljoin(response.url, post_url),
                meta={"front_image_url": parse.urljoin(response.url, image_url)},
                callback=self.parse_detail
            )

        # 提取下一页
        next_url = response.xpath('//a[contains(text(),"Next >")]/@href').extract_first('')
        next_url = parse.urljoin(response.url, next_url)
        yield Request(url=next_url, callback=self.parse)

    def parse_detail(self, response):
        match_re = re.match('.*?(\d+)', response.url)
        if match_re:
            post_id = match_re.group(1)
            image_url = response.meta.get('front_image_url', [])

            # news_item = CnblogNewsItem()
            # title = response.xpath('//div[@id="news_title"]/a/text()').extract_first('')
            # news_info = response.xpath('//div[@id="news_info"]')
            # news_poster = news_info.xpath('./span[@class="news_poster"]/a/text()').extract_first('')
            # create_time = news_info.xpath('./span[@class="time"]/text()').extract_first('')
            # match_re = re.match(".*?(\d.*)", create_time)
            # if match_re:
            #     create_time = match_re.group(1)
            # content = response.xpath('//div[@id="news_content"]').extract_first('')
            # tag_list = response.xpath('//div[@class="news_tags"]/a/text()').extract()
            # tags = ','.join(tag_list)
            #
            # news_item.update({
            #     "url": response.url,
            #     "title": title,
            #     "poster": news_poster,
            #     "create_time": create_time,
            #     "content": content,
            #     "tags": tags,
            #     "front_image_url": [image_url] if image_url else []
            # })

            item_loader = NewsItemLoader(item=CnblogNewsItem(), response=response)
            item_loader.add_value('url', response.url)
            item_loader.add_xpath('title', '//div[@id="news_title"]/a/text()')
            item_loader.add_xpath('poster', '//span[@class="news_poster"]/a/text()')
            item_loader.add_xpath('create_time', '//span[@class="time"]/text()')
            item_loader.add_xpath('content', '//div[@id="news_content"]')
            item_loader.add_xpath('tags', '//div[@class="news_tags"]/a/text()')
            item_loader.add_value('front_image_url', image_url)

            yield Request(
                url=parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                callback=self.parse_nums,
                meta={
                    "item_loader": item_loader,
                    "url": response.url
                }
            )

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        praise_nums = j_data['DiggCount']
        fav_nums = j_data['TotalView']
        comment_nums = j_data['CommentCount']

        # news_item = response.meta.get('item', {})
        # news_item.update({
        #     "praise_nums": praise_nums,
        #     "comment_nums": comment_nums,
        #     "fav_nums": fav_nums,
        #     "url_object_id": common.get_md5(news_item['url'])
        # })

        item_loader = response.meta.get('item_loader')
        item_loader.add_value("praise_nums", praise_nums)
        item_loader.add_value("comment_nums", comment_nums)
        item_loader.add_value("fav_nums", fav_nums)
        item_loader.add_value("url_object_id", common.get_md5(response.meta.get('url')))
        news_item = item_loader.load_item()

        yield news_item
