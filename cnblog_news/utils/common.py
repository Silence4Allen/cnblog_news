# -*- coding: utf-8 -*-#

# ------------------------------------------------------------------------------
# Name:         common
# Description:  
# Author:       Allen
# Time:         2021/1/6 17:47
# ------------------------------------------------------------------------------

import hashlib


def get_md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()
