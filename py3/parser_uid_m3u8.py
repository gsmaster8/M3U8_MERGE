import time
import re
import os
import sys
import traceback
from parser_m3u8 import M3u8File
from sortedcontainers import SortedDict,SortedList

def is_duration_zero(self, file_name):
    cmd = "ffmpeg -i %s 2>&1 | grep Duration | awk '{print $2}' | tr -d ," % file_name
    result = subprocess.check_output(cmd, shell=True).strip()
    return result == "00:00:00.00"

class ParserUidM3U8File(object):
    def __init__(self, uid):
        self.uid = uid
        self.segment_limit_gap = 15
        self.aux_use = 0
        if os.environ.get('USEAUX') is not None:
            self.aux_use = int(os.environ['USEAUX'])

        self.filename_dict = {}
        self.filename_dict['main_audio'] = []
        self.filename_dict['main_video'] = []
        self.filename_dict['aux_video'] = []

        self.media_dict = {}
        self.media_dict['main_audio'] = SortedDict()
        self.media_dict['main_video'] = SortedDict()
        self.media_dict['aux_video'] = SortedDict()

        self.segments = {}
    
    def metadata_dict_merged_in_merged_dict(self):   
        for key, value in self.filename_dict.items():
            for m3u8 in value:
                self.media_dict[key].update(m3u8.get_media_dict())
                
    def merged_dict_splited_to_segment(self):
        if self.aux_use:
            previous = -1
            aux_key_list = SortedList(self.media_dict['aux_video'])
            aux_merged = {}
            for key,value in self.media_dict['main_video'].items():
                if previous > 0 and key - previous > self.segment_limit_gap:
                    aux_range = aux_key_list.irange(previous, key-1)
                    for i in aux_range:
                        aux_value = self.media_dict['aux_video'][i]
                        if i + aux_value['duration'] < key:
                            aux_merged[i] = aux_value
                previous = key + value['duration']
            self.media_dict['main_video'].update(aux_merged)

        video_key_list = SortedList(self.media_dict['main_video'])
        audio_key_list = SortedList(self.media_dict['main_audio'])
        av_ordered_list = []

        ia = 0
        for v in video_key_list:
            while ia < len(audio_key_list) and audio_key_list[ia] <= v:
                a = audio_key_list[ia]
                itema = self.media_dict['main_audio'][a]
                av_ordered_list.append(['audio', a, a+itema['duration'], itema['name']])
                ia += 1
            itemv = self.media_dict['main_video'][v]
            av_ordered_list.append(['video', v, v+itemv['duration'], itemv['name']])

        previous = -0.1
        segment = []
        for av in av_ordered_list:
            if previous > 0 and av[1] - previous > self.segment_limit_gap:
                self.create_middlefile_of_segments(segment)
                segment.clear()
            segment.append(av)
            previous = av[1] + av[2]
        if segment:
            self.create_middlefile_of_segments(segment)

    def create_middlefile_of_segments(self, segment):
        utc = str(segment[0][1])
        segment_filename = 'uid_' + self.uid + "_" + utc + ".txt"
        lines = SortedDict()
        for av in segment:
            create = '%s %.3f %s create' % (av[0], av[1], av[3])
            close = '%s %.3f %s close' % (av[0], av[2], av[3])
            lines[av[1]] = create
            lines[av[2]] = close
        with open(segment_filename, 'w') as f:
            for line in lines.values():
                f.write(line+'\n');
            # f.writelines('\n'.join(lines.values())

    def update_filename_dict(self, stream_type, filename):
        self.filename_dict[stream_type].append(M3u8File(self.uid, filename, stream_type))

