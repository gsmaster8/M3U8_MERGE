import re
import os
import glob
import TRTC_M3u8_Parser
from TRTC_Uid_Parser import TRTCUidParser

class TRTCFloderParser(object):
    def __init__(self, folder_name):
        self.path = folder_name
        self.meta_file_patten = r'(.*)__UserId_s_(.*)__UserId_e__([a-zA-Z]+)_([a-zA-Z]+).m3u8'

        '''
        self.all_uid_metadatafiles = {
        'uid1':TRTCUidParser(format)
        'uid2':TRTCUidParser(format)
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
                self.all_uid_metadatafiles[uid] = TRTCUidParser(uid)

            self.all_uid_metadatafiles[uid].update_filename_dict(stream_type, file)

    def per_user_splited_metadata_dict_merged_in_one(self):
        for metadatafile_per_uid in self.all_uid_metadatafiles.values():
            metadatafile_per_uid.metadata_dict_merged_in_merged_dict()

    def per_user_merged_dict_splited_to_segment(self):
        for metadatafile_per_uid in self.all_uid_metadatafiles.values():
            metadatafile_per_uid.merged_dict_splited_to_segment()
    
    def dispose(self):
        #stored in dict
        self.parser_all_files()
        #stored all corner case as one merged file
        self.per_user_splited_metadata_dict_merged_in_one()
        #split one merged file as segment per start key word
        self.per_user_merged_dict_splited_to_segment()
 
    def clean(self):
        if not os.path.isdir(self.path):
            print("Folder %s does not exist" % self.path)
            return

        os.chdir(self.path)
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

