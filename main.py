import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
import urllib
import threading
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
path = "./"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#获取搜索列表
def Search(wd):
    #<h4 class="title"><a class="searchkey" href="/dongman/3709.html">寄生兽生命的准则</a></h4>
    url = "https://www.yhdmw.com/comicsearch/-------------.html?wd=" + urllib.parse.quote(wd)
    res = requests.get(url)
    rep = BeautifulSoup(res.text,'lxml')
    results = rep.find_all("a",{"class","searchkey"})
    return [(result.get_text(strip=True),"https://www.yhdmw.com" + result["href"]) for result in results]
#获取m3u8链接
def Getm3u8(url):
    res = requests.get(url)
    rep = BeautifulSoup(res.text,'lxml')
    result = rep.find("div",{"class","myui-player__video embed-responsive clearfix"})
    fgs = str(result).split(",")
    url = ""
    for fg in fgs:
        if fg[0:4] == "\"url":
            st = fg.find(":")
            url = fg[st+2:-1].replace("\\","").replace("index","hls/index")
            return url
#获取ts列表
def GetTsList(m3u8):
    res = requests.get(m3u8)
    tsList = re.findall("https://.+\\.ts",res.text)
    return tsList
#下载ts文件
def Downloadts(ts):
    return requests.get(ts,verify = False).content
#合并ts文件
def LinkTs(tsList,path):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    with open(path, "wb")as file:
        threads = []
        for ts in tsList:
            future = executor.submit(Downloadts,ts)
            threads.append(future)
        for i in range(len(threads)):
            while True:
                if (threads[i].done() == True):
                    file.write(threads[i].result())
                    print(path + ":", round(((i  + 1) / len(threads)) * 100,2), "%")
                    break
#获取筛选结果
def GetAns(results):
    for i in range(len(results)):
        result = results[i]
        print(f'{i}.',f'《{result[0]}》'," 链接:",result[1])
    choose = input("请输入序号进行选择:")
    return results[int(choose)]
#下载全集
def DownloadAll(alls):
    threads = []
    for ec in alls:
        TsList = GetTsList(Getm3u8(ec[1]))
        future = threading.Thread(target=LinkTs,args=(TsList,path + ec[0] + ".ts"))
        threads.append(future)
        future.start()
        print(ec[0],"开始下载")
    for it in threads:
        it.join()
        print(it[0],"下载完成")

#选集
def Chowhich(result):
    #https://www.yhdmw.com/yinghua/5445-1-1.html
    #<span class="text-red">24集全/2022-04-08 09:08:57</span>
    res = BeautifulSoup(requests.get(result[1]).text,"lxml")
    allVs = res.find_all("a",{"class","btn btn-default"})
    choose = input(f"共{len(allVs)}集，请输入需要下载的集数（输入*下载全部）：")
    if (choose != "*"):
        LinkTs(GetTsList(Getm3u8("https://www.yhdmw.com" + allVs[int(choose) - 1]["href"])), path + allVs[int(choose) - 1].get_text() + ".ts")
    else :
        DownloadAll([(allV.get_text(),"https://www.yhdmw.com" + allV["href"])for allV in allVs])
#配置
def readset():
    global path
    if os.path.exists("./set.txt"):
        with open("./set.txt","r")as file:
            path = file.read()
    else :
        with open("./set.txt","w")as file:
            file.write(path)
if __name__ == "__main__":
    readset()
    wd = input("输入搜索内容:")
    Chowhich(GetAns(Search(wd)))