import ast
import base64
import html
import json
import os
import re
import urllib.request

import logger
import requests
import urllib3.request
from bs4 import BeautifulSoup
from mutagen.mp4 import MP4, MP4Cover
from pySmartDL import SmartDL

from pyDes import *

# Pre Configurations
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# urllib3.disable_warnings()
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
unicode = str
raw_input = input


def addtags(filename, json_data, playlist_name):
    audio = MP4(filename)
    audio['\xa9nam'] = unicode(json_data['song'])
    audio['\xa9ART'] = unicode(json_data['primary_artists'])
    audio['\xa9alb'] = unicode(json_data['album'])
    audio['aART'] = unicode(json_data['singers'])
    audio['\xa9wrt'] = unicode(json_data['music'])
    audio['desc'] = unicode(json_data['starring'])
    audio['\xa9gen'] = unicode(playlist_name)
    # audio['cprt'] = track['copyright'].encode('utf-8')
    # audio['disk'] = [(1, 1)]
    # audio['trkn'] = [(int(track['track']), int(track['maxtracks']))]
    audio['\xa9day'] = unicode(json_data['year'])
    audio['cprt'] = unicode(json_data['label'])
    # if track['explicit']:
    #    audio['rtng'] = [(str(4))]
    cover_url = json_data['image'][:-11] + '500x500.jpg'
    fd = urllib.request.urlopen(cover_url)
    cover = MP4Cover(fd.read(), getattr(MP4Cover, 'FORMAT_PNG' if cover_url.endswith('png') else 'FORMAT_JPEG'))
    fd.close()
    audio['covr'] = [cover]
    audio.save()


def setProxy():
    base_url = 'http://h.saavncdn.com'
    proxy_ip = ''
    if ('http_proxy' in os.environ):
        proxy_ip = os.environ['http_proxy']
    proxies = {
        'http': proxy_ip,
        'https': proxy_ip,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    }
    return proxies, headers


def setDecipher():
    return des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)


def searchSongs(query):
    songs_json = []
    albums_json = []
    playLists_json = []
    topQuery_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?_format=json&query={0}&__call=autocomplete.get'.format(query))
    if respone.status_code == 200:
        respone_json = json.loads(respone.text.splitlines()[6])
        albums_json = respone_json['albums']['data']
        songs_json = respone_json['songs']['data']
        playLists_json = respone_json['playlists']['data']
        topQuery_json = respone_json['topquery']['data']
    return {"albums_json": albums_json,
            "songs_json": songs_json,
            "playLists_json": playLists_json,
            "topQuery_json": topQuery_json}


def getPlayList(listId):
    songs_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?listid={0}&_format=json&__call=playlist.getDetails'.format(listId), verify=False)
    if respone.status_code == 200:
        songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
        songs_json = json.loads(songs_json)
    return songs_json


def getAlbum(albumId):
   songs_json = []
   respone = requests.get(
       'https://www.saavn.com/api.php?_format=json&__call=content.getAlbumDetails&albumid={0}'.format(albumId),
       verify=False)
   if respone.status_code == 200:
       songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
       songs_json = json.loads(songs_json)
   return songs_json


def getSong(songId):
    songs_json = []
    respone = requests.get(
        'http://www.saavn.com/api.php?songid={0}&_format=json&__call=song.getDetails'.format(songId), verify=False)
    if respone.status_code == 200:
        print(respone.text)
        songs_json = json.loads(respone.text.splitlines()[5])
    return songs_json


def getHomePage():
    playlists_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?__call=playlist.getFeaturedPlaylists&_marker=false&language=tamil&offset=1&size=250&_format=json',
        verify=False)
    if respone.status_code == 200:
        playlists_json = json.loads(respone.text.splitlines()[2])
        playlists_json = playlists_json['featuredPlaylists']
    return playlists_json


def downloadSongs(songs_json, folder = "songs"):
    des_cipher = setDecipher()
    for song in songs_json['songs']:
        try:
            enc_url = base64.b64decode(song['encrypted_media_url'].strip())
            dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
            dec_url = dec_url.replace('_96.mp4', '_320.mp4')
            filename = html.unescape(song['song']) + '.m4a'
            filename = filename.replace("\"", "'")
        except Exception as e:
            logger.error('Download Error' + str(e))
        try:
            directory = os.path.join("SONGS",folder)
            location = os.path.join(os.path.sep, os.getcwd(),directory, filename)
            if os.path.isfile(location):
               print("Downloaded %s" % filename)
            else :
                print("Downloading %s" % filename)
                obj = SmartDL(dec_url, location)
                obj.start()
                name = songs_json['name'] if ('name' in songs_json) else songs_json['listname']
                addtags(location, song, name)
                print('\n')
        except Exception as e:
             logger.error('Download Error' + str(e))


if __name__ == '__main__':
    input_url = sys.argv[1]
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
            downloadSongs(getAlbum(getAlbumID)) # param
            # sys.exit()
    except Exception as e:
        print('...')

    print("Please paste link of album or playlist")

# getSongID = soup.select(".current-song")[0]["data-songid"]
# if getSongID is not None:
#    print(getPlayListID)
#    sys.exit()
# for playlist in getHomePage():
#     print(playlist)
#     id = raw_input()
#     if id is "1":
#       downloadSongs(getPlayList(playlist['listid']))
# queryresults = searchSongs('nannare')
# print(json.dumps(getSong(queryresults['topQuery_json'][0]['id']), indent=2))
# response = requests.head(dec_url)
# if os.path.isfile(location) if (os.stat(location).st_size >  int(response.headers["Content-Length"])) else False:
