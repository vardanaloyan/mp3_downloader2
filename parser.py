import sys ,os,re
import requests
from bs4 import BeautifulSoup
from Download import *
os.environ['PYTHONWARNINGS']="ignore:Unverified HTTPS request"

def correct(fname):
    #return fname
    for i in fname:
        if i in rlist:
            fname = fname.replace(i,"_").strip()
    return fname

def download(album, url):
    input_url = url
    try:
        proxies, headers = setProxy()
        res = requests.get(input_url, proxies=proxies, headers=headers)
    except Exception as e:
        logger.error('Error accessing website error: ' + e)

    soup = BeautifulSoup(res.text, "lxml")

    try:
        getPlayListID = soup.select(".flip-layout")[0]["data-listid"]
        if getPlayListID is not None:
            print("Initiating PlayList Downloading")
            downloadSongs(getPlayList(getPlayListID))
            # sys.exit()
    except Exception as e:
        print('...')
    try:
        getAlbumID = soup.select(".play")[0]["onclick"]
        getAlbumID = ast.literal_eval(re.search("\[(.*?)\]", getAlbumID).group())[1]

        if getAlbumID is not None:
            print("Initiating Album Downloading")
            downloadSongs(getAlbum(getAlbumID), album) # param
            # sys.exit()
    except Exception as e:
        print('...')

    print("Please paste link of album or playlist")

def parse_page(link = None):
    if link is None:
        return
    session = requests.Session()
    session.max_redirects = 9999999
    page = session.get(link, verify=False)
    soup = BeautifulSoup(page.content, 'lxml')
    # print page.content
    res =  soup.find_all('ul', class_='catalog-items')
    for i in res[0]:
        if hasattr(i, 'a'):
            download(i.a.text, i.a["href"])
            # print(i.a['href'])

link = sys.argv[1]
parse_page(link)
