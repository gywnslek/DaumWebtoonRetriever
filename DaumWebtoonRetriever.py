#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" run on python 3.5.1 """

import urllib.request
import re
import os, os.path
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class DaumWebtoonRetriever:
    thread_count = 2;

    def __init__(self, title):
        self.driver = webdriver.Chrome(executable_path="./chromedriver.exe")
        self.driver.get("http://webtoon.daum.net/webtoon/view/{}".format(title))
        self.webtoonPageData = []

    def __del__(self):
        self.driver.close()


    def getWebtoonList(self):
        """ 목록페이지에서 회차 정보 추출 """

        link_wt = self.driver.find_elements_by_class_name("link_wt")

        for elem in link_wt:
            data_id = elem.get_attribute("data-id")
            if (data_id != None):
                tit_wt = elem.find_element_by_class_name("tit_wt").text
                href = elem.get_attribute("href")
                self.webtoonPageData.append([data_id, tit_wt, href])


    def hasNextListPage(self):
        """ 다음 페이지 존재 여부 확인 """

        link_page = self.driver.find_elements_by_class_name("link_page")
        page_count = len(link_page)
        if (page_count < 2):
            return False

        idx = 0
        for elem in link_page:
            idx += 1
            data_page = elem.get_attribute("data-page")
            if (data_page == None and idx < page_count):
                return True
        else:
            return False


    def goNextListPage(self):
        """  목록 페이지가 2페이지 이상일때 페이지 이동 """

        link_page = self.driver.find_elements_by_class_name("link_page")
        page_count = len(link_page)
        if (page_count < 2):
            return False

        idx = 1
        foundCurPage = False
        for elem in link_page:
            data_page = elem.get_attribute("data-page")
            if (foundCurPage):
                actions = webdriver.ActionChains(self.driver)
                actions.move_to_element(elem)
                actions.click(elem)
                actions.perform()
                self.driver.get(self.driver.current_url)
                break
            elif (data_page == None and idx < page_count):
                foundCurPage = True


    def downloadImages(self):
        pageUrl = self.webtoonPageData[0][2];
        title = self.webtoonPageData[0][1];
        data_id = self.webtoonPageData[0][0];
        downloader = self.WebtoonDownloader(self, pageUrl, data_id +"_"+ title)
        downloader.start()
#        for page in self.pageUrls:
#            downloader = self.WebtoonDownloader(self, page)
#            downloader.start()



    class WebtoonDownloader(Thread):
        """ 이미지 다운로드용 쓰레드"""

        def __init__(self, retriever, pageUrl, save_dir):
            Thread.__init__(self)
            self.retriever = retriever
            self.driver = retriever.driver
            self.pageUrl = pageUrl
            self.save_dir = save_dir + os.sep
            os.mkdir(save_dir)

        def __del__(self):
            del(self.retriever, self.driver, self.pageUrl, self.save_dir)

        def run(self):
            self.driver.get(self.pageUrl)
            img_webtoon = self.driver.find_elements_by_class_name("img_webtoon")
            idx = 0
            for img in img_webtoon:
                idx += 1
                src = img.get_attribute("src")
                fname = self.downloadImage(src, idx)


        def downloadImage(self, imgUrl, idx):
            req = urllib.request.Request(imgUrl)
            with urllib.request.urlopen(req) as resp :
                ext = resp.getheader("Content-Type").split("/")[1]
                if (ext.lower() == "jpeg"):
                    ext = "jpg"
                with open(r"{}img{:02d}.{}".format(self.save_dir, idx, ext), "wb") as fimg:
                    fimg.write(resp.read())
            return fimg.name


if __name__ == "__main__":
    daum = DaumWebtoonRetriever("afternoonheros")
    daum.getWebtoonList()

#    while(daum.hasNextListPage()):
#        daum.goNextListPage()
#        daum.getWebtoonList()

    daum.downloadImages()














#
# 헤더 정보
#
def getImageHeaders(titleId, no) :
    baseHeaders = {
        "Host":"imgcomic.naver.net",
        "Accept":"image/webp,image/*,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch",
        "Accept-Language":"ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"
    }
    baseHeaders["Referer"] = "http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={:d}".format(titleId, no)
    return baseHeaders

#
# URL 목록에 있는 image 파일을 다운로드 한다.
#
def downloadImages(urls, titleId, no):
    if (not os.path.exists(titleId)):
        os.mkdir(titleId)

    saveDir = "{}{}{:03d}".format(titleId, os.sep, no)
    if (not os.path.exists(saveDir)):
        os.mkdir(saveDir)
    os.chdir(saveDir)


    idx = 0
    for u in urls:
        idx += 1
        imgName = "{:02d}{}".format(idx, os.path.splitext(u)[1])
        with open(imgName, "wb") as fimg:
            req = urllib.request.Request(u, headers=getImageHeaders(titleId, no))
            with urllib.request.urlopen(req) as f :
                fimg.write(f.read())

    with open("index.html", "w") as fhtml:
        fhtml.write("<html><head></head><body>")
        for i in range(idx):
            fhtml.write("<img src='{:02d}{}'><br>".format(i, os.path.splitext(urls[i])[1]))
        fhtml.write("</body></html>")

#
# HTML 에서 웹툰 이미지 URL 를 가져온다.
#
def fetchImageUrls(html, titleId, no):
    patt = r"http://imgcomic.naver.net/webtoon/{}/{:d}/[^>]+\.jpg".format(titleId, no)
    return(re.findall(patt, html))


#
# 해당 페이지 html 소스를 받아온다.
#
def retrieveUrl(titleId, no):
    urlStr = "http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={:d}".format(titleId, no)
    req = urllib.request.Request(urlStr)
    html = ""
    with urllib.request.urlopen(req) as f :
        html = f.read().decode("utf-8")
    return(html)

# 목록페이지에서 목록 추출
#<a href="/webtoon/viewer/40854" class="link_wt  " data-id="40854">
#	<img src="http://t1.daumcdn.net/cartoon/589192A1060AE50001" width="186" height="112" class="img_thumb" alt="2부 57화">
#	<span class="thumb_cover"></span>
#	<span class="stat_choice">
#        <span class="bg_choice"></span>
#        <span class="ico_comm ico_choice"></span>
#    </span>
#	<span class="stat_classify">
#        <span class="ico_comm ico_choice"></span>
#    </span>
#	<strong class="tit_wt">2부 57화</strong>
#</a>

#<span class="inner_pages">
#	<span class="btn_comm btn_prev">이전목록없음</span>
#		<a href="#none" class="link_page" data-page="1">1</a>
#		<span class="txt_bar">·</span>
#		<a href="#none" class="link_page" data-page="2">2</a>
#		<span class="txt_bar">·</span>
#		<span class="screen_out">현재페이지</span>
#		<em class="bg_comm link_page">3</em> <-- 현재페이지 -->
#		<span class="txt_bar">·</span>
#		<a href="#none" class="link_page" data-page="4">4</a>
#	<span class="btn_comm btn_next">다음목록없음</span>
#	</span>

#http://webtoon.daum.net/webtoon/view/afternoonheros#pageNo=3&sort=desc&type=

#<dd class="txt_episode"><span class="ico_comm ico_arrow"></span>16화</dd>

#<div class="cont_view" id="imgView">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88A706041C0001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88A80679C00001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88A906625F0001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88AA06084B0001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88AB0665530001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88AD0676E90001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88AE0607FF0001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88AF0615890001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88B10668EC0001" width="760" class="img_webtoon" alt="웹툰이미지">
#	<img src="http://i1.cartoon.daumcdn.net/svc/image/U03/cartoon/532B88B20609140001" width="760" class="img_webtoon" alt="웹툰이미지">
#</div>

# http://www.seleniumhq.org/docs/03_webdriver.jsp  적용하기.


# 웹툰을 가져오는 절차
def getWebtoon(titleId, no):
    html = retrieveUrl(titleId, no)
    urls = fetchImageUrls(html, titleId, no)
    downloadImages(urls, titleId, no)





