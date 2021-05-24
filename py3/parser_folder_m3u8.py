import time
import re
import os
import sys
import signal
import glob

import parser_m3u8
from parser_uid_m3u8 import ParserUidM3U8File

class ParserFloderM3U8(object):
    def __init__(self, folder_name):
        self.path = folder_name
        self.meta_file_patten = r'(.*)__UserId_s_(.*)__UserId_e_([a-zA-Z]+)_([a-zA-Z]+).m3u8'

        '''
        self.all_uid_metadatafiles = {
        'uid1':ParserUidM3U8File(format)
        'uid2':ParserUidM3U8File(format)
        }
        '''
        self.all_uid_metadatafiles = {}
        
    def parser_all_files(self):
        os.chdir(self.path)
        all_files = sorted(glob.glob('*.m3u8'))
        filename_pat_reged = re.compile(self.meta_file_patten)

        for file in all_files:
            result = filename_pat_reged.match(file)
            if not result:
                continue
            prefix = result.group(1)
            uid = result.group(2)
            stream_type = result.group(3) + "_" + result.group(4)
            av_type = result.group(4)
            if uid not in self.all_uid_metadatafiles:
                self.all_uid_metadatafiles[uid] = ParserUidM3U8File(uid)

            self.all_uid_metadatafiles[uid].update_filename_dict(stream_type, file)

    def per_user_splited_metadata_dict_merged_in_one(self):
        # °Ñ»º´æµÄÒôÊÓÆµÐÅÏ¢ºÏ²¢
        for metadatafile_per_uid in self.all_uid_metadatafiles.values():
            metadatafile_per_uid.metadata_dict_merged_in_merged_dict()

    def per_user_merged_dict_splited_to_segment(self):
        # °ÑºÏ²¢µÄÐÅÏ¢°´SegmentÇÐ·Ö
        for metadatafile_per_uid in self.all_uid_metadatafiles.values():
            metadatafile_per_uid.merged_dict_splited_to_segment()
    
    def dispose(self):
        #stored in dict
        self.parser_all_files()
        #stored all corner case as one merged file
        self.per_user_splited_metadata_dict_merged_in_one()
        #split one merged file as segment per start key word
        self.per_user_merged_dict_splited_to_segment()
 
def help():
    help_str='''Help:
    ./script dispose path
    eg.
     %s dispose .
    ''' %(sys.argv[0])
    print(help_str)

# ÖÐ¼äÎÄ¼þÇåÀí
def clean_func(folder_name):
    if not os.path.isdir(folder_name[1]):
        print("Folder " + folder_name[1] + " does not exist")
        return

    os.chdir(folder_name[1])
    media_file = "media_file.mf"
    if os.path.exists(media_file):
        f = open(media_file, "r")
        lines = f.readlines()
        for line in lines:
            os.system('rm -f %s' % line)
        os.system('rm -f %s' % media_file)
    all_uid_file = sorted(glob.glob("uid_*.txt"))
    for uid_file in all_uid_file:
        os.system('rm -f %s' % uid_file)

# Ö´ÐÐºÏ²¢²Ù×÷
def cmds1_func(cmds):
    parser = ParserFloderM3U8(cmds[1])
    parser.dispose()


def cmds_parse(input_cmd):
    dirname=r'[^ ]+'  # ÕýÔò
    cmds_func_list =  [
            [['dispose',dirname], cmds1_func],
            [['clean', dirname], clean_func]
            ]
    try:
        found=False
        for cmds_func in cmds_func_list:
            flag=True

            #skip different cmds_len
            if len(cmds_func[0]) != len(input_cmd):
#                print(cmds_func[0], input_cmd)
                continue

            #cmds len equal, but need to check param legal or not
            for pat,cmd_part in zip(cmds_func[0],input_cmd):
#                print(pat,cmd_part)
                if re.match(pat,cmd_part) == None:
                    flag=False
                    break

            if flag:
                found = True
                print("cmd pattern:%s" %(cmds_func[0]))
                print("input cmd:%s" %(input_cmd))

                cmds_func[1](input_cmd)  #µ÷ÓÃÏàÓ¦µÄº¯Êý
                break

        if found == False:
            print("input cmds:%s" %input_cmd)
            help()
    except Exception as e:
        print("Error input:%s!" %e)
        print("input cmds:%s" %input_cmd)
        help()
        traceback.print_exc()



if '__main__' == __name__:
    import sys
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGQUIT, signal.SIG_IGN)
    cmds_parse(sys.argv[1:])

