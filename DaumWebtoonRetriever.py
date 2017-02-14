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
    thread_count = 2
    page_limit = 0  # 작업 대상 페이지 0 : 전부, x>0 : 1-x 까지 페이지

    def __init__(self, title, download_dir="download"):
        self.driver = webdriver.Chrome(executable_path="./chromedriver.exe")
        self.driver.get("http://webtoon.daum.net/webtoon/view/{}".format(title))
        self.webtoonPageData = []
        self.download_dir = download_dir + os.sep + title

        if (os.path.exists(download_dir)):
            if (not os.path.isdir(download_dir)):
                print("'{}' is not a directory but a file or something.".format(download_dir))
                exit()
        else:
            os.makedirs(download_dir)


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
        threads = []
        pageUrl = self.webtoonPageData[0][2]
        title = self.webtoonPageData[0][1]
        data_id = self.webtoonPageData[0][0]
        downloader = self.WebtoonDownloader(self, pageUrl, self.download_dir + os.sep + data_id +"_"+ title)
        downloader.start()
        # Queue 에 넣어서 작업



    class WebtoonDownloader(Thread):
        """ 이미지 다운로드용 쓰레드 (회차 단위 다운로드)"""

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
