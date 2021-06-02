import os
import sys
import copy
from TRTC_M3u8_Parser import TRTCM3u8File
from sortedcontainers import SortedDict,SortedList

def is_duration_zero(self, file_name):
    cmd = "ffmpeg -i %s 2>&1 | grep Duration | awk '{print $2}' | tr -d ," % file_name
    result = subprocess.check_output(cmd, shell=True).strip()
    return result == "00:00:00.00"

class TRTCUidParser(object):
    def __init__(self, uid):
        self.uid = uid
        self.segment_limit_gap = 15.0

        # 0 disable aux stream
        # 1 repalce mode, if main stream not exist, use aux stream
        # 2 disable main stream
        self.aux_use = 0
        if os.environ.get('USEAUX') is not None:
            self.aux_use = int(os.environ['USEAUX'])

        self.merge_segments = 0
        if os.environ.get('MERGEMODE') is not None:
            self.merge_segments = int(os.environ.get('MERGEMODE'))

        self.merge_gap = 0
        if os.environ.get('MERGEGAP') is not None:
            self.merge_gap = int(os.environ.get('MERGEGAP'))

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
        if self.aux_use > 0:
            if self.aux_use == 2:
                self.media_dict['main_video'].clear()
            aux_key_list = SortedList(self.media_dict['aux_video'])
            previous = sys.float_info.max
            last = -1.0
            if len(aux_key_list) > 0:
                previous = aux_key_list[0]
                last = aux_key_list[-1]

            aux_merged = {}
            for key,value in self.media_dict['main_video'].items():
                if key - previous > self.segment_limit_gap:
                    aux_range = aux_key_list.irange(previous, key-1)
                    for v in aux_range:
                        aux_value = self.media_dict['aux_video'][v]
                        if v + aux_value['duration'] < key:
                            aux_merged[v] = aux_value
                previous = key + value['duration']

            if last > previous:
                aux_range = aux_key_list.irange(previous, last)
                for v in aux_range:
                    aux_value = self.media_dict['aux_video'][v]
                    aux_merged[v] = aux_value
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
            av_ordered_list.append(['video', v, v+itemv['duration'], itemv['name'], itemv['width'], itemv['height']])

        while ia < len(audio_key_list):
            a = audio_key_list[ia]
            itema = self.media_dict['main_audio'][a]
            av_ordered_list.append(['audio', a, a+itema['duration'], itema['name']])
            ia += 1
        previous = -0.1
        segments = []
        segment = []
        for av in av_ordered_list:
            if previous > 0 and av[1] - previous > self.segment_limit_gap:
                segments.append(copy.deepcopy(segment))
                segment.clear()
            segment.append(av)
            previous = av[2]
        if segment:
            segments.append(copy.deepcopy(segment))
        if self.merge_segments:
            final_segment = []
            for i in range(len(segments)):
                gap = 0.0
                if i > 0 and self.merge_gap:
                    cur = segments[i]
                    prev = segments[i-1]
                    gap = cur[0][1] - prev[-1][2]
                for v in segments[i]:
                    v[1] = v[1] - gap
                    v[2] = v[2] - gap
                    final_segment.append(v)
            segments.clear()
            segments.append(final_segment)
        for s in segments:
            self.create_middlefile_of_segments(s)

    def create_middlefile_of_segments(self, segment):
        #utc = str(segment[0][1])
        utc = segment[0][3][-20:-3]
        segment_filename = 'uid_' + self.uid + "_" + utc + ".txt"
        lines = []
        for av in segment:
            if len(av) < 5:
                create = '%s %.3f %s create' % (av[0], av[1], av[3])
            else:
                create = '%s %.3f %s create %d %d' % (av[0], av[1], av[3], av[4], av[5])
            close = '%s %.3f %s close' % (av[0], av[2], av[3])
            lines.append(create)
            lines.append(close)
        def sort_by(line):
            items = line.split(" ")
            return float(items[1])
        lines.sort(key=sort_by)

        with open(segment_filename, 'w') as f:
            f.write('\n'.join(lines));

    def update_filename_dict(self, stream_type, filename):
        self.filename_dict[stream_type].append(TRTCM3u8File(self.uid, filename, stream_type))

