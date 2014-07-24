# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import datetime

import sickbeard

import generic

from sickbeard.common import XML_NSMAP
from sickbeard import logger, exceptions, helpers
from sickbeard.exceptions import ex

from lib.tvdb_api import tvdb_api, tvdb_exceptions

import xml.etree.cElementTree as etree

class ATVMetadata(generic.GenericMetadata):
    """
    Metadata generation class for Apple TV.

    The following file structure is used:
    
    show_root/cover.jpg                                      (poster)
    show_root/Season 01/show - 1x01 - episode.avi            (existing video)
    show_root/Season 01/show - 1x01 - episode.avi.cover.jpg  (episode thumb)
    """
    
    def __init__(self,
                 show_metadata=False,
                 episode_metadata=False,
                 fanart=False,
                 poster=False,
                 banner=False,
                 episode_thumbnails=False,
                 season_posters=False,
                 season_banners=False,
                 season_all_poster=False,
                 season_all_banner=False):

        generic.GenericMetadata.__init__(self,
                                         show_metadata,
                                         episode_metadata,
                                         fanart,
                                         poster,
                                         banner,
                                         episode_thumbnails,
                                         season_posters,
                                         season_banners,
                                         season_all_poster,
                                         season_all_banner)
	

        self._ep_nfo_extension = 'xml'
        self.name = 'Apple TV'

        self.eg_show_metadata = "<i>not supported</i>"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.xml"
        self.eg_fanart = "<i>not supported</i>"
        self.eg_poster = "folder.jpg"
        self.eg_banner = "<i>not supported</i>"
        self.eg_episode_thumbnails = "<i>not supported</i>"
        self.eg_season_posters = "<i>not supported</i>"
        self.eg_season_banners = "<i>not supported</i>"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"
		
    # all of the following are not supported, so do nothing
    def create_show_metadata(self, show_obj):
        pass

    def get_show_file_path(self, show_obj):
        pass
		
    def create_fanart(self, show_obj):
        pass

    def create_banner(self, show_obj):
        pass

    def get_episode_thumb_path(self, ep_obj):
        pass

    def create_season_posters(self, show_obj):
        pass
    
    def create_season_banners(self, ep_obj):
        pass
		
    def create_season_all_poster(self, show_obj):
        pass
				
    def create_season_all_banner(self, show_obj):
        pass

    def retrieveShowMetadata(self, dir):
        return (None, None)

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a ATV style episode.xml
        and returns the resulting data object.
        
        show_obj: a TVEpisode instance to create the NFO for
        """
        eps_to_write = [ep_obj] + ep_obj.relatedEps
        
        tvdb_lang = ep_obj.show.lang
        # There's gotta be a better way of doing this but we don't wanna
        # change the language value elsewhere
        ltvdb_api_parms = sickbeard.TVDB_API_PARMS.copy()
        
        if tvdb_lang and not tvdb_lang == 'en':
            ltvdb_api_parms['language'] = tvdb_lang
        
        try:
            t = tvdb_api.Tvdb(actors=True, **ltvdb_api_parms)
            myShow = t[ep_obj.show.tvdbid]
        except tvdb_exceptions.tvdb_shownotfound, e:
            raise exceptions.ShowNotFoundException(e.message)
        except tvdb_exceptions.tvdb_error, e:
            logger.log(u"Unable to connect to TVDB while creating meta files - skipping - "+ex(e), logger.ERROR)
            return

        rootNode = etree.Element( "media" )
        
        rootNode.set("type", "TV Show");
        
        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:
            
            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (tvdb_exceptions.tvdb_episodenotfound, tvdb_exceptions.tvdb_seasonnotfound):
                logger.log(u"Unable to find episode " + str(curEpToWrite.season) + "x" + str(curEpToWrite.episode) + " on tvdb... has it been removed? Should I delete from db?")
                return None
            
            if not myEp["firstaired"]:
                myEp["firstaired"] = str(datetime.date.fromordinal(1))
            
            if not myEp["episodename"]:
                logger.log(u"Not generating xml because the ep has no title", logger.DEBUG)
                return None
            
            logger.log(u"Creating metadata for episode "+str(ep_obj.season)+"x"+str(ep_obj.episode))
            
            episode = rootNode
            
            title = etree.SubElement( episode, "title" )
            if curEpToWrite.name != None:
                title.text = curEpToWrite.name
            
            season = etree.SubElement( episode, "season" )
            season.text = str(curEpToWrite.season)
            
            episodenum = etree.SubElement( episode, "episode" )
            episodenum.text = str(curEpToWrite.episode)
            
            aired = etree.SubElement( episode, "published" )
            if curEpToWrite.airdate != datetime.date.fromordinal(1):
                aired.text = str(curEpToWrite.airdate)
            else:
                aired.text = ''
            
            plot = etree.SubElement( episode, "description" )
            if curEpToWrite.description != None:
                plot.text = curEpToWrite.description
            
            credits = etree.SubElement( episode, "writers" )
            credits_text = myEp['writer']
            if credits_text != None:
                etree.SubElement(credits, "name").text = credits_text
            
            director = etree.SubElement( episode, "directors" )
            director_text = myEp['director']
            if director_text != None:
                etree.SubElement(director, "name").text = director_text
            
            rating = etree.SubElement( episode, "rating" )
            rating_text = myEp['rating']
            if rating_text != None:
                rating.text = rating_text

            actors = etree.SubElement(episode, "cast")
            for actor in myShow['_actors']:
                etree.SubElement(actors, "name").text = actor['name']
        
        #
        # Make it purdy
        helpers.indentXML( rootNode )
        
        data = etree.ElementTree( rootNode )
        
        return data

# present a standard "interface"
metadata_class = ATVMetadata

