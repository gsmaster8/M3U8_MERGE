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

        self.media_dict = SortedDict()
        self.load()

    def get_media_dict(self):
        return self.media_dict

    def load(self):
        regex_media_pat = re.compile(self.media_pat)
        regex_duration_pat = re.compile(self.duration_pat)
        with open(self.m3u8file) as f:
            extinf = -0.1
            for line in f.readlines():
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
                            self.media_dict[TRTC_Helper.utc_convert(result.group(1))] = media
                        extinf = -0.1

