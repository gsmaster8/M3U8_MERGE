import os
import glob
import subprocess
import TRTC_Helper

HOME = os.path.dirname(os.path.realpath(__file__))
pathEnv=os.getenv('PATH')
os.environ['PATH']= "%s" %(HOME) + ":" + pathEnv 
dest_fps = 15
target_width = 0
target_height = 0
black_frame_mode = False

class TRTCAudioClip:
    def __init__(self):
        self.num = 0
        self.filename = []
        self.start_time = []
        self.end_time = []

    def update_audio_info(self, i, stime, etime):
        self.start_time[i] = stime
        self.end_time[i] = etime

    def put_file(self, name):
        if not (name in self.filename):
            self.filename.append(name)
            self.start_time.append(0.0)
            self.end_time.append(0.0)
            self.num = self.num + 1
        return self.filename.index(name)

    def max_length(self):
        return max(self.end_time)

    def print_filename(self, offset_time):
        str = ""
        for i in range(self.num):
            if i > 0:
                len = self.start_time[i] - self.end_time[i-1]
            else:
                len = self.start_time[0] - offset_time
            if len < 0.001:
                len = 0.001
            str = str + ("-f lavfi -t %.3f -i anullsrc=channel_layout=mono:sample_rate=48000 " % len)
            str = str + ("-i %s " % self.filename[i])
        return str

    def print_audio_info(self, i):
        print("Audio Clip %d: %s: start_time=%.3f, end_time=%.3f" % (i, self.filename[i], self.start_time[i], self.end_time[i]))

    def print_ffmpeg(self, output_file, tmp_audio_file, offset_time):
        cmd = "cat "
        for a in self.filename:
            cmd += a + " "
        cmd += ">> " + tmp_audio_file
        subprocess.Popen(cmd, shell=True, env=None).wait()
        str = "ffmpeg -copyts -i %s -af aresample=48000:async=1 -c:a aac %s" % (tmp_audio_file, output_file)
        str = str + " 2>&1 | tee -a convert.log"
        print("==============================audio ffmpeg=====================================")
        print(str)
        return str

class TRTCVideoClip:
    def __init__(self):
        self.num = 0
        self.filename = []
        self.start_time = []
        self.end_time = []
        self.width = []
        self.height = []
        self.audio_file = ""
        self.audio_start_time = 0.0
        self.audio_end_time = 0.0
        self.overlay_str = ""

    def update_audio_info(self, audio_stime, audio_etime):
        self.audio_start_time = audio_stime
        self.audio_end_time = audio_etime

    def update_video_info(self, i, video_stime, video_etime):
        self.start_time[i] = video_stime
        self.end_time[i] = video_etime

    def put_file(self, name):
        if not (name in self.filename):
            self.filename.append(name)
            self.start_time.append(0.0)
            self.end_time.append(0.0)
            self.width.append(0)
            self.height.append(0)
            self.num = self.num + 1
        return self.filename.index(name)

    def get_max_width(self):
        return max(self.width)

    def get_max_height(self):
        return max(self.height) 
    
    def max_length(self):
        if self.num > 0:
            return max(max(self.end_time), self.audio_end_time)
        else:
            return self.audio_end_time
    
    def audio_delay_needed(self, offset_time):
        return self.audio_file != "" and (self.audio_start_time - offset_time) > 0.05
    def audio_apad_needed(self):
        return self.audio_file != "" and self.max_length() > self.audio_end_time
   
    def print_filter(self, offset_time):
        str = "" 
        if self.audio_delay_needed(offset_time):
            audio_delay = int((self.audio_start_time - offset_time)*1000)
            str = "[0]adelay=%d" % audio_delay
            if self.audio_apad_needed():
                str = str + ",apad"
            str = str + "[audio];"
        elif self.audio_apad_needed():
                str = str + "[0]apad[audio];"

        source = "1"
        sink = "out2"

        if not black_frame_mode:
            self.overlay_str = "overlay=eof_action=repeat"
        else:
            self.overlay_str = "overlay=eof_action=repeat:repeatlast=0"

        for i in range(self.num):
            src = "%d" % (i+2)

            sink = "out%d" % (i+2)
            if i == self.num - 1:
                sink = "video"

            tmp = "[%s]scale=%dx%d,setpts=PTS-STARTPTS+%.3f/TB[scale%s];[%s][scale%s]%s[%s];" % \
                    ( src, target_width, target_height, self.start_time[i] - offset_time, src, source, src, self.overlay_str, sink )
            str = str + tmp
            source = sink
        return str[:-1]
   
    def print_filename(self):
        str = ""
        for i in range(self.num):
            str = str + ("-i %s " % self.filename[i])
        return str
   
    def print_ffmpeg(self, output_file, offset_time):
        if self.audio_file == "":
            str = "ffmpeg -f lavfi -i anullsrc "
        else:
            str = "ffmpeg -i %s " % self.audio_file

        str = str + "-f lavfi -i \"color=black:s=%dx%d:r=15\" "% (target_width, target_height)
        str = str + self.print_filename()
        str = str + "-filter_complex \"%s\" " % self.print_filter(offset_time)
        if self.audio_file == "":
            map_option = "-map \"[video]\""
        else:
            if self.audio_delay_needed(offset_time) or self.audio_apad_needed():
                map_option = "-map \"[audio]\" -map \"[video]\" -c:a aac"
            else:
                map_option = "-map 0:a:0 -map \"[video]\" -c:a copy"
        str = str + " %s -c:v libx264 -r %d -preset veryfast -shortest -to %f -y %s" % (map_option, dest_fps, self.max_length() - offset_time, output_file)
        str = str + " 2>&1 | tee -a convert.log"
        print("=================================video ffmpeg ========================")
        print(str)
        return str

    def print_audio_info(self):
        print("Audio Clip: %s: start_time=%.3f, end_time=%.3f" % (self.audio_file, self.audio_start_time, self.audio_end_time))
    
    def print_video_info(self, i):
        print("Video Clip %d: %s: start_time=%.3f, end_time=%.3f, width=%d, height=%d" % (i, self.filename[i], self.start_time[i], self.end_time[i], target_width, target_height))
    
def convert_per_uid(folder_name, uid_file, suffix, offset_time):
        global target_height
        global target_width  
        print("Offset_time : " + str(offset_time))
        child_env = os.environ.copy()

        uid = os.path.splitext(uid_file)[0][4:]
        print("UID:"+uid)
            
        clip = TRTCVideoClip()
        audio_clip = TRTCAudioClip()

        with open(uid_file) as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip('\n')
                items = line.split(" ")
                if items[0] == "audio":
                    index = audio_clip.put_file(items[2])
                    if items[3] == "create":
                        audio_clip.start_time[index] = float(items[1])
                    elif items[3] == "close":
                        audio_clip.end_time[index] = float(items[1])
                        
                if items[0] == "video":
                    index = clip.put_file(items[2])
                    if items[3] == "create":
                        clip.start_time[index] = float(items[1])
                        clip.width[index] = int(items[4])
                        clip.height[index] = int(items[5])
                    elif items[3] == "close":
                        clip.end_time[index] = float(items[1])

            for i in range(audio_clip.num):
                audio_clip.print_audio_info(i)
            for i in range(clip.num):
                clip.print_video_info(i)

        if audio_clip.num == 0 and clip.num == 0:
            return ""
                    
        if audio_clip.num >= 1:
            print("Generate Audio File")
            tmp_file_prefix = folder_name.strip() + '/' + uid + "_tmp"
            tmp_audio = tmp_file_prefix + ".m4a"
            middle_audio_file = tmp_file_prefix + '.ts'
            ffmpeg_args_file = folder_name.strip() + '/' + uid + '_ffmpeg_args.sh'
            command = audio_clip.print_ffmpeg(tmp_audio, middle_audio_file, offset_time)
            clip.audio_file = tmp_audio
            clip.audio_start_time = audio_clip.start_time[0]
            clip.audio_end_time = audio_clip.max_length()
            print(command)
            
            f = open(ffmpeg_args_file, 'w') 
            f.write(command)
            f.close()
            
            command = "chmod a+x %s" % ffmpeg_args_file
            subprocess.Popen(command, shell=True, env=child_env).wait()
            subprocess.Popen(ffmpeg_args_file, shell=True, env=child_env).wait()
            os.system('rm -f %s' % middle_audio_file)
    
        if clip.num > 0:
            print("Generate MP4 file:")
            output_file = uid + suffix + ".mp4"
            if target_width == 0:
                target_width = clip.get_max_width()
            if target_height == 0:
                target_height = clip.get_max_height()
            command =  clip.print_ffmpeg(output_file, offset_time)
        else:
            tmp_audio = uid+"_tmp.m4a"
            output_file = uid+".m4a"
            if audio_clip.num >= 1:
                command = "mv %s %s" % (tmp_audio, output_file)
            elif audio_clip.num == 1:
                command = "ffmpeg -i %s -c:a copy -y %s" % (clip.audio_file, output_file)

        print(command)
        subprocess.Popen(command, shell=True, env=child_env).wait()
        print("\n\n")
        #remove tmp files
        os.system('rm -f *_tmp.m4a')
        os.system('rm -f *_ffmpeg_args.sh')
        return output_file   

def convert_middlefile(folder_name):
    child_env = os.environ.copy()
    if not os.path.isdir(folder_name):
        print("Folder " + folder_name + " does not exist")
        return

    os.chdir(folder_name)
    all_uid_file = sorted(glob.glob("uid_*.txt"))
    for uid_file in all_uid_file:
        # offset_time = float(uid_file.split("_")[2][0:-4])
        offset_time = float(TRTC_Helper.utc_convert(uid_file.split("_")[-1][0:-4]))
        convert_per_uid(folder_name, uid_file, "_av", offset_time)

def start_convert(options):
    global target_width
    global target_height
    global dest_fps
    global black_frame_mode

    if not options.folder:
        parser.print_help()
        parser.error("Not set folder")
    if options.mode < 0 or options.mode > 1:
        parser.error("Invalid mode")
    if options.fps <= 0:
        parser.error("Invalid fps")

    if options.resolution[0] < 0 or options.resolution[1] < 0:
        parser.error("Invalid resolution width/height")
    else:
        target_width = options.resolution[0]
        target_height = options.resolution[1]

    if options.fill_black:
        black_frame_mode = True

    os.system("rm -f " + options.folder + "/convert.log")

    if options.fps < 5:
        print("fps < 5, set to 5")
        dest_fps = 5
    elif options.fps > 120:
        print("fps > 120, set to 120")
        dest_fps = 120
    else:
        dest_fps = options.fps

    convert_middlefile(options.folder)

if __name__ == '__main__':
    start_convert()
