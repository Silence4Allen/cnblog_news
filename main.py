# -*- coding: utf-8 -*-#

# ------------------------------------------------------------------------------
# Name:         main
# Description:  
# Author:       Allen
# Time:         2021/1/5 22:22
# ------------------------------------------------------------------------------


from scrapy.cmdline import execute
import sys
import os

program_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(program_path)
execute(["scrapy", "crawl", "cnblog_news_spider"])


