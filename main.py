# -*- coding: utf-8 -*-
# Module: default
# Author: NaZo

import sys
import re
from urlparse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import urllib
import json
import inputstreamhelper

_URL = sys.argv[0]
_HANDLE = int(sys.argv[1])
_WIN = xbmcgui.Window()
_WERDER_URL = 'https://www.werder.de'
_STREAM_MIME_TYPE = 'application/dash+xml'
_STREAM_PROTOCOL = 'mpd'
_STREAM_MANIFEST = '/manifest(format=mpd-time-csf,filter=360-720p)'
_IS_HELPER = inputstreamhelper.Helper(_STREAM_PROTOCOL)
_KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
if _KODI_VERSION_MAJOR >= 19:
    _INPUTSTREAM_PROPERTY = 'inputstream'
else:
    _INPUTSTREAM_PROPERTY = 'inputstreamaddon'

class WerderVideo(object):
    
    def __init__(self, json):

        self.title = json['title'] 
        self.image = json['image'].lstrip('/')
        self.primaryTagLabel = json['videoInformation']['primaryTag'] if 'primaryTag' in json['videoInformation'] else ''
        self.description = json['description']
        self.date = json['publishDateTime']
        self.tagList = json['tagList']
        self.mediaid = json['id']
    
    def toListItem(self):
        listItem = xbmcgui.ListItem(label=self.title)
        listItem.setInfo('video', {'title': self.title, 'genre': self.primaryTagLabel, 'date': self.date, 'plot': self.description, 'plotoutline': self.description})
        listItem.setProperty('IsPlayable', 'true')
        thumb = _WERDER_URL + '/?eID=crop&width=400&height=300&file=' + self.image
        xbmc.log('Thumb: ' + thumb)
        
        fanart = _WERDER_URL + '/?eID=crop&width=' + str(_WIN.getWidth()) + '&height=' + str(_WIN.getHeight()) + '&file=' + self.image
        listItem.setArt({'thumb': thumb, 'icon': thumb, 'fanart': fanart})
        url = self.buildUrl()
        
        return (url, listItem, False)
    
    def buildUrl(self):
        return _URL + '?show=play&tagList=' + self.tagList + '&mediaid=' + str(self.mediaid)


class WerderLiveVideo(WerderVideo):
    
    def __init__(self, json):

        self.title = 'LIVE: ' + json['title'] 
        self.image = json['image']
        self.primaryTagLabel = json['subTitle']
        self.description = json['subTitle']
        self.date = json['startDate']
        self.stream = 'https://' + json['stream']
    
    def buildUrl(self):
        return _URL + '?show=playDirect&stream=' + self.stream
    
class WerderGroup(object):
    
    def __init__(self, json):
        self.id = int(json['id'])
        self.title = json['titleDe']
        self.tags = []
        for tag in json['tags']:
            self.tags.append(WerderTag(tag))
    
    def toListItem(self):
        listItem = xbmcgui.ListItem(label=self.title)
        listItem.setInfo('video', {'title': self.title})
        url = _URL + '?show=group&group=' + str(self.id)
        
        return (url, listItem, True)
    
    
class WerderTag(object):
    
    def __init__(self, json):
        self.id = int(json['id'])
        self.title = json['titleDe']
    
    def toListItem(self):
        listItem = xbmcgui.ListItem(label=self.title)
        listItem.setInfo('video', {'title': self.title})
        url = _URL + '?show=tag&tag=' + str(self.id)
        
        return (url, listItem, True)
    
    
def toListItem(werderObject):
    return werderObject.toListItem()

    
def loadGroupList():
    
    url = _WERDER_URL + '/api/rest/tag/group/list'
    xbmc.log('WERDER.TV - groups url: ' + url)
    file = urllib.urlopen(url)
    results = json.load(file)
    
    listItems = dict()
    for group in results:
        group = WerderGroup(group)
        if group.tags:
            listItems[group.id] = group

    return listItems


def listGroups():
    
    listing = map(toListItem, loadGroupList().values())
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(_HANDLE)


def listTags(groupId):
    
    groups = loadGroupList()
    if groupId in groups:
        tags = groups[groupId].tags
        listing = map(toListItem, tags)
        xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
        xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(_HANDLE)


def loadVideoList(tagId = 0, limit = 0):
    
    tagParam = 'tagList=' + str(tagId) if tagId > 0 else ''
    limitParam = 'limit=' + str(limit) if limit > 0 else ''
    
    url = _WERDER_URL + '/api/rest/video/list/compact?' + limitParam  + '&orderBy=publishDateTime&orderByDesc=true&page=1&strict=true' + tagParam
    file = urllib.urlopen(url)
    results = json.load(file)
    
    listItems = []
    for item in results['items']:
        listItems.append(WerderVideo(item))

    return listItems

def loadLiveMatch():
    jsonUrl = _WERDER_URL + '/api/match/match/live'
    jsonFile = urllib.urlopen(jsonUrl)
    result = json.load(jsonFile)
    
    if result and result['title']:
        imageRegEx = re.compile(r"image\:.*file=(?P<image>[^']*)'\,")
        streamRegEx = re.compile(r"fallbackFile\: '(?P<stream>[^']*)'")
        htmlUrl = _WERDER_URL + '/de/werdertv/live/'
        htmlFile = urllib.urlopen(htmlUrl)
        for line in htmlFile.readlines():
            line = line.strip()
            imageRegExMatch = imageRegEx.match(line)
            if imageRegExMatch is not None:
                result['image'] = imageRegExMatch.group('image')       
                if 'stream' in result:
                    break
            else:
                streamRegExMatch = streamRegEx.match(line)
                if streamRegExMatch is not None:
                    result['stream'] = streamRegExMatch.group('stream')                
                    if 'image' in result:
                        break
        
        return WerderLiveVideo(result)
    else:
        return None


def listLatestVideos():
    liveItem = loadLiveMatch()
    if liveItem:
        listing = [liveItem.toListItem()]
    else:
        listing = []

    #archiveItem = xbmcgui.ListItem(label='Archiv')
    #archiveItem.setInfo('video', {'title': 'Archiv'})
    #archiveUrl = _URL + '?show=archive'   
    #listing = [(archiveUrl, archiveItem, True)] + listing
    
    listing = listing + map(toListItem, loadVideoList(0, 50))
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(_HANDLE)


def listVideos(tagId):
    
    listing = map(toListItem, loadVideoList(tagId))
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(_HANDLE)


def loadStreamUrl(tagList, mediaid):
    url = _WERDER_URL + '/api/rest/video/related/video.json?orderBy=publishDateTime&limit=10&tagList=' + tagList
    file = urllib.urlopen(url)
    results = json.load(file)
    for s in reversed(results):
        xbmc.log("s['mediaid']: "  + str(s['mediaid']))
        if s['mediaid'] == mediaid:
            return 'https:' + s['file'] + _STREAM_MANIFEST
    
    xbmc.log('WERDER.TV - video url: ' + url, xbmc.LOGINFO)
    xbmc.log('WERDER.TV - video mediaid: ' + str(mediaid), xbmc.LOGINFO)
    xbmc.log('WERDER.TV - video.json: ' + str(results), xbmc.LOGINFO)
    return None


def showVideo(tagList, mediaid):

    xbmc.log('WERDER.TV - tagList: ' + tagList)
    url = loadStreamUrl(tagList, mediaid)
    if not url:
        xbmc.log('WERDER.TV - Keine Stream URL gefunden für mediaid: ' + str(mediaid) + ' (tagList: ' + tagList + ')', xbmc.LOGERROR)
        dialog = xbmcgui.Dialog()
        dialog.notification('Fehler', 'Stream-URL nicht gefunden', xbmcgui.NOTIFICATION_ERROR, 5000, True)
    else:
        openStream(url)

def openStream(url):
    xbmc.log('WERDER.TV - stream url: ' + url, xbmc.LOGINFO)
    #siehe https://github.com/emilsvennesson/script.module.inputstreamhelper
    if _IS_HELPER.check_inputstream():
        playItem = xbmcgui.ListItem(path=url)
        playItem.setContentLookup(False)
        playItem.setMimeType(_STREAM_MIME_TYPE)
        playItem.setProperty('inputstream.adaptive.manifest_type', _STREAM_PROTOCOL)
        playItem.setProperty(_INPUTSTREAM_PROPERTY, _IS_HELPER.inputstream_addon)
        xbmcplugin.setResolvedUrl(_HANDLE, True, playItem)

def router(paramstring):

    params = dict(parse_qsl(paramstring))
    if params:
        if params['show'] == 'archive':
            listGroups()
        elif params['show'] == 'group':
            listTags(int(params['group']))
        elif params['show'] == 'tag':
            listVideos(int(params['tag']))
        elif params['show'] == 'play':
            showVideo(params['tagList'], int(params['mediaid']))
        elif params['show'] == 'playDirect':
            openStream(params['stream'])
    else:
        listLatestVideos()


if __name__ == '__main__':
    router(sys.argv[2][1:])
