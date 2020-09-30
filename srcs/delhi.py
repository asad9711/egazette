import datetime
import urllib.request, urllib.parse, urllib.error
import re
import os

from .central import CentralBase
from ..utils import utils

class DelhiWeekly(CentralBase):
    def __init__(self, name, storage):
        CentralBase.__init__(self, name, storage)
        self.baseurl     = 'http://www.egazette.nic.in/DelhiGazette.aspx'
        self.search_endp = 'SG_DL_Search.aspx'
        self.result_table = 'dgGeneralUser'
        self.start_date   = datetime.datetime(2016, 5, 1)

    def get_search_results(self, search_url, dateobj, cookiejar):
        referer_url = urllib.parse.urljoin(search_url, self.search_endp)
        response = self.download_url(search_url, savecookies = cookiejar, \
                                  loadcookies=cookiejar, referer = referer_url)

        postdata = self.get_form_data(response.webpage, dateobj)
        if postdata == None:
            return None

        newdata = []
        for k, v in postdata:
            if k == '__EVENTTARGET':
                v = 'ddlcate'
            elif k == 'ddlcate':
                v = self.gztype

            newdata.append((k, v))

        response = self.download_url(search_url, savecookies = cookiejar, \
                                   referer = search_url, \
                                   loadcookies = cookiejar, postdata = newdata)

        postdata = self.get_form_data(response.webpage, dateobj)
        if postdata == None:
            return None
        response = self.download_url(search_url, savecookies = cookiejar, \
                                   referer = search_url, \
                                   loadcookies = cookiejar, postdata = postdata)
        return response

    def get_post_data(self, tags, dateobj):
        datestr  = utils.get_egz_date(dateobj)

        postdata = []
        for tag in tags:
            name  = None
            value = None

            if tag.name == 'input':
                name  = tag.get('name')
                value = tag.get('value')
                t     = tag.get('type')
                if t == 'image' or name  == 'btn_Reset':
                    continue

                if name == 'btnstd':
                    value = 'Search' 

                if name == 'txtDateIssueF' or name == 'txtDateIssueT':
                    value = datestr
            elif tag.name == 'select':        
                name = tag.get('name')
                if name == 'ddlcate':
                    value = self.gztype
                elif name == 'ddlPartSection':
                    value = 'Select Part & Section'
                elif name == 'ddlSubMinistry':
                    value = 'Select Department'
            if name:
                if value == None:
                    value = ''
                postdata.append((name, value))

        return postdata

    def download_gazette(self, relpath, search_url, postdata, \
                         metainfo, cookiejar):

        if 'gazetteid' not in metainfo:
            return None

        gazetteid = metainfo['gazetteid']
        reobj = re.search('(?P<num>\d+)\s*$', gazetteid)
        if not reobj:
            return None

        filename = reobj.groupdict()['num']
        relurl   = os.path.join(relpath, filename)

        if self.save_gazette(relurl, search_url, metainfo, validurl = False, \
                             postdata = postdata, cookiefile = cookiejar):
            return relurl

        return None     

class DelhiExtraordinary(DelhiWeekly):
    def __init__(self, name, storage):
        DelhiWeekly.__init__(self, name, storage)
        self.gztype   = 'Extra Ordinary'


