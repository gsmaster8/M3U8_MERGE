import re
import os
import TRTC_Helper
from sortedcontainers import SortedDict,SortedList

class TRTCM3u8File(object):
    def __init__(self, uid, m3u8file, stream_type):
        self.uid = uid
        self.m3u8file = m3u8file
        self.stream_type = stream_type
        self.middle_file = "media_file.mf"

        self.media_pat = r'.*__UserId_s_%s__UserId_e_%s_(\d+)\.([a-zA-Z0-9]+)' % (self.uid, self.stream_type)
        self.duration_pat = r'#EXTINF:(\d+(?:\.\d+)?)'
        self.resolution_pat = r'#EXT-X-TRTC-VIDEO-METADATA:WIDTH:(\d+) HEIGHT:(\d+)'

        self.media_dict = SortedDict()
        self.load()

    def get_media_dict(self):
        return self.media_dict

    def load(self):
        regex_media_pat = re.compile(self.media_pat)
        regex_duration_pat = re.compile(self.duration_pat)
        regex_resolution_pat = re.compile(self.resolution_pat)
        with open(self.m3u8file) as f:
            extinf = -0.1
            width = 0
            height = 0
            for line in f.readlines():
                result = regex_resolution_pat.match(line)
                if result:
                    width = int(result.group(1))
                    height = int(result.group(2))
                    continue
                result = regex_duration_pat.match(line)
                if result:
                    extinf = float(result.group(1))
                elif extinf > 0:
                    result = regex_media_pat.match(line)
                    if result:
                        if os.path.isfile(result.group(0)) and os.path.getsize(result.group(0)) > 0:
                            media = {}
                            media["name"] = result.group(0)
                            media["duration"] = extinf
                            if width > 0:
                                media["width"] = width
                            else:
                                media["width"] = 640
                            if height > 0:
                                media["height"] = height
                            else:
                                media["height"] = 360
                            self.media_dict[TRTC_Helper.utc_convert(result.group(1))] = media
                        extinf = -0.1

