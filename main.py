# -*- coding: utf-8 -*-
# Module: default
# Author: NaZo

import sys
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import urllib
import json

_URL = sys.argv[0]
_HANDLE = int(sys.argv[1])
_WIN = xbmcgui.Window()
_WERDER_URL = 'http://www.werder.de'

class WerderVideo(object):
    
    def __init__(self, title, image, page, primaryTagLabel, description, date):

        self.title = title
        self.image = image.lstrip('/')
        self.page = page
        self.primaryTagLabel = primaryTagLabel
        self.description = description
        self.date = date
    
    def toListItem(self):
        list_item = xbmcgui.ListItem(label=self.title)
        list_item.setInfo('video', {'title': self.title, 'genre': self.primaryTagLabel, 'date': self.date, 'plot': self.description, 'plotoutline': self.description})
        list_item.setProperty('IsPlayable', 'true')
        thumb = _WERDER_URL + '/?eID=crop&width=400&height=300&file=' + self.image
        fanart = _WERDER_URL + '/?eID=crop&width=' + str(_WIN.getWidth()) + '&height=' + str(_WIN.getHeight()) + '&file=' + self.image
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': fanart})
        page = _WERDER_URL + self.page
        url = 'plugin://plugin.program.chrome.launcher/?url=' + page + '&mode=showSite&stopPlayback=no'
        
        return (url, list_item, False)

def loadVideoList(tagId = 0, limit = 0):
    
    tagParam = 'tagList=' + str(tagId) if tagId > 0 else ''
    limitParam = 'limit=' + str(limit) if limit > 0 else ''
    
    url = _WERDER_URL + '/api/rest/video/list/compact?' + limitParam  + '&orderBy=publishDateTime&orderByDesc=true&page=1&strict=true' + tagParam
    file = urllib.urlopen(url)
    results = json.load(file)
    
    listItems = []
    for item in results['items']:
        video = WerderVideo(item['title'], item['image'], item['videoInformation']['detailPage'], item['videoInformation']['primaryTag'], item['description'], item['publishDateTime'])
        listItems.append(video.toListItem())

    return listItems


def listLatestVideos():
    
    listing = loadVideoList(0, 20)
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(_HANDLE)
    

def get_categories():
    """
    Get the list of video categories.
    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.

    :return: list
    """
    url = 'http://www.werder.de/api/rest/tag/group/list'
    file = urllib.urlopen(url)
    results = json.load(file)
    
    groups = {'0': 'Neueste Videos'}
    for group in results:
        groups[group['id']] = group['titleDe']
            
    return groups


def get_videos():
    """
    Get the list of videofiles/streams.
    Here you can insert some parsing code that retrieves
    the list of videostreams in a given category from some site or server.

    :param category: str
    :return: list
    """
    win = xbmcgui.Window()
    width = win.getWidth()
    height = win.getHeight()
    limit = 64
    
    url = 'http://www.werder.de/api/rest/video/list/compact?limit=' + str(limit)  + '&orderBy=publishDateTime&orderByDesc=true&page=1&strict=true'
    file = urllib.urlopen(url)
    results = json.load(file)
    
    videos = []
    for item in results['items']:
        name = item['title']
        thumb = 'http://www.werder.de/?eID=crop&width=400&height=300&file=' + item['image'].lstrip('/')
        fanart = 'http://www.werder.de/?eID=crop&width=' + str(width) + '&height=' + str(height) + '&file=' + item['image'].lstrip('/')
        page = 'http://www.werder.de' + item['videoInformation']['detailPage']
        genre = item['videoInformation']['primaryTag']
        date = item['publishDateTime']
        description = item['description']
        videos.append({'name': name, 'thumb': thumb, 'fanart': fanart, 'page': page, 'genre': genre, 'date': date, 'description': description})

    return videos


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    categories = get_categories()
    # Create a list for our items.
    listing = []
    # Iterate through categories
    for id, name in categories.iteritems():
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=name)
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', {'title': name})
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = '{0}?action=listing&category={1}'.format(_URL, id)
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def list_videos():
    """
    Create the list of playable videos in the Kodi interface.

    :param category: str
    """
    # Get the list of videos in the category.
    videos = get_videos()
    # Create a list for our items.
    listing = []
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre'], 'date': video['date'], 'plot': video['description'], 'plotoutline': video['description']})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['fanart']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for the plugin recursive callback.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
        url = 'plugin://plugin.program.chrome.launcher/?url=' + video['page'] + '&mode=showSite&stopPlayback=no'
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(_HANDLE, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def show_video(path):
    """
    Play a video by the provided path.

    :param path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
#     if params:
#         if params['show'] == 'latest':
#             # Display the list of videos in a provided category.
#             listLatestVideos()
#         elif params['show'] == 'archive':
#             # Display the list of videos in a provided category.
#             list_archive(params['group'])
#         elif params['show'] == 'tag':
#             # Display the list of videos in a provided category.
#             list_tag_videos(params['tag'])
#         elif params['show'] == 'play':
#             # Play a video from a provided URL.
#             show_video(params['video'])
#     else:
#         # If the plugin is called from Kodi UI without any parameters,
#         # display the list of video categories
#         list_videos()

    listLatestVideos()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
