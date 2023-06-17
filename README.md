# guba_spider
股吧评论爬虫
基于seelnium库，使用时需要根据自己电脑chrome浏览器版本下载对应的chromedriver，并在代码中更改你的chromedriver的位置

guba_spyder.py --单线程爬虫
guba_spyder_multiprocessing.py --多进程爬虫
code.xlsx --所爬取的股票代码
002029.xlsx --所爬取的文件示例

爬取的字段
title --帖子标题
author --作者
read --阅读数
comment_number --评论数
time --发布时间
content --帖子内容
comment --帖子评论

可爬取每条帖子评论以及评论下的回复
