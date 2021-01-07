# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
"""
pipelines中对数据（多半是item）的处理，需要配合settings.py文件使用
"""
import codecs
import json

import MySQLdb
from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi


class CnblogNewsPipeline:
    def process_item(self, item, spider):
        return item


class NewsImagePipeline(ImagesPipeline):
    """
    保存文件下载路径到item中
    """

    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            image_file_path = ''
            for ok, value in results:
                if isinstance(value, dict) and 'path' in list(value.keys()):
                    image_file_path = value['path']
            item["front_image_path"] = image_file_path
        return item


class JsonWithEncodingPipeline(object):
    """
    自定义文件导出
    """

    def __init__(self):
        self.file = codecs.open('news.json', "a", encoding='utf-8')

    # 多态
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    # 多态
    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    """
    自带的file open写入json
    """

    def __init__(self):
        self.file = open('news_export.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    # 多态
    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    # 多态
    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()


class MysqlPipeline(object):
    """
    同步的方式插入数据库
    """

    def __init__(self):
        self.conn = MySQLdb.connect(
            host="127.0.0.1",
            user='root',
            password='silence4allen',
            database='cnblog_news',
            charset='utf8',
            use_unicode=True
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into cnblog_news
            (title,url,url_object_id,front_image_path,front_image_url,praise_nums,comment_nums,fav_nums,tags,content,create_time)
            values 
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE praise_nums=VALUES(praise_nums)
        """
        params = list()
        params.append(item.get('title', ''))
        params.append(item.get('url', ''))
        params.append(item.get('url_object_id', ''))
        params.append(item.get('front_image_path', ''))
        front_image = ','.join(item.get('front_image_url', []))
        params.append(front_image)
        params.append(item.get('praise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('tags', ''))
        params.append(item.get('content', ''))
        params.append(item.get('create_time', '1970-07-01'))

        self.cursor.execute(insert_sql, tuple(params))
        self.conn.commit()
        return item

    def spider_closed(self, spider):
        self.conn.close()


class MysqlTwistedPipeline(object):
    """
    异步方式插入数据库
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        db_params = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True
        )
        db_pool = adbapi.ConnectionPool('MySQLdb', **db_params)
        return cls(db_pool)

    def process_item(self, item, spider):
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        print(failure)

    def do_insert(self, cursor, item):
        insert_sql = """
                    insert into cnblog_news
                    (title,url,url_object_id,front_image_path,front_image_url,praise_nums,comment_nums,fav_nums,tags,content,create_time)
                    values 
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE praise_nums=VALUES(praise_nums)
                """
        params = list()
        params.append(item.get('title', ''))
        params.append(item.get('url', ''))
        params.append(item.get('url_object_id', ''))
        params.append(item.get('front_image_path', ''))
        front_image = ','.join(item.get('front_image_url', []))
        params.append(front_image)
        params.append(item.get('praise_nums', 0))
        params.append(item.get('comment_nums', 0))
        params.append(item.get('fav_nums', 0))
        params.append(item.get('tags', ''))
        params.append(item.get('content', ''))
        params.append(item.get('create_time', '1970-07-01'))

        cursor.execute(insert_sql, tuple(params))
