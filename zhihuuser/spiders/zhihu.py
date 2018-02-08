# -*- coding: utf-8 -*-
import json
import scrapy
from zhihuuser.items import UserItem
from scrapy_redis .spiders import RedisSpider

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_user='excited-vczh'

    #用户详细信息
    user_url='https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query='allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    #关注列表
    follows_url='https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query='data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    #粉丝列表
    followers_url='https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query='data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        #获取起始人的信息
        yield scrapy.Request(self.user_url.format(user=self.start_user,include=self.user_query),callback=self.parse_user)
        #关注列表
        yield scrapy.Request(self.follows_url.format(user=self.start_user,include=self.follows_query,offset=0,limit=20),callback=self.parse_follows)
        #粉丝列表
        yield scrapy.Request(self.followers_url.format(user=result.get('url_token'),include=self.followers_query,offset=0,limit=20),callback=self.parse_followers)

    def parse_user(self, response):
        #处理详细信息
        result=json.loads(response.text)
        item=UserItem()
        #获取详细信息存入item
        for field in item.fields:
            if field in result.keys():
                item[field]=result.get(field)
        yield item
        #递归请求访问他关注的人的信息
        yield scrapy.Request(self.follows_url.format(user=result.get('url_token'),include=self.follows_query,offset=0,limit=20),callback=self.parse_follows)
        #递归请求访问关注他的用户的信息
        yield scrapy.Request(self.followers_url.format(user=result.get('url_token'),include=self.followers_query,offset=0,limit=20),callback=self.parse_followers)

    def parse_follows(self, response):
        #处理关注他的用户列表
        results = json.loads(response.text)
        #判断该信息是否存在
        if 'data' in results.keys():
            for result in results.get('data'):
                #获得urltoken来抓取用户的信息,递归抓取用户信息传给parse_user，
                yield scrapy.Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),callback=self.parse_user)

        #判断是否有下一页 递归自己抓取下一页的关注信息
        if 'paging' in results.keys() and results.get('paging').get('is_end')==False:
            next_page= results.get('paging').get('next')
            yield scrapy.Request(next_page,callback=self.parse_follows)

    def parse_followers(self, response):
        # 处理他关注的用户列表
        results = json.loads(response.text)
      # 判断该信息是否存在
        if 'data' in results.keys():
            for result in results.get('data'):
                # 获得urltoken来抓取用户的信息,递归抓取用户信息传给parse_user，
                yield scrapy.Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                                    callback=self.parse_user)

        # 判断是否有下一页 递归自己抓取下一页的关注信息
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield scrapy.Request(next_page, callback=self.parse_followers)
