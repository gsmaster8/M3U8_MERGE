import os
import signal
import parser_folder_m3u8
import convert_phase
import traceback
from optparse import OptionParser

if '__main__' == __name__:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGQUIT, signal.SIG_IGN)

    parser = OptionParser()
    parser.add_option("-f", "--folder", type="string", dest="folder", help="Folder of files to be merged", default="")
    parser.add_option("-m", "--mode", type="int", dest="mode", help="Convert merge mode.\n[0: segment merge A/V(Default);\n 1: uid merge A/V]", default=0)
    parser.add_option("-p", "--fps", type="int", dest="fps", help="Convert fps, default 15", default=15)
    parser.add_option("-s", "--saving", action="store_true", dest="saving", help="Convert Do not time sync", default=False)
    parser.add_option("-a", "--aux_use", type="int", dest="aux_use", help="aux stream mode", default=False)
    parser.add_option("-r", "--resolution", type="int", dest="resolution", nargs=2, help="Specific resolution to convert '-r width height' \nEg:'-r 640 360', default 640x360", default=(640, 360))
    parser.add_option("-b", "--fill_black", action="store_true", dest="fill_black", help="Show black frame when there is no video file", default=False)

    (options, args) = parser.parse_args()
    if not options.folder:
        parser.print_help()
        parser.error("Not set folder")

    options.folder = os.path.abspath(options.folder)
    try:
        os.environ['FPSARG'] = "%s" % options.fps
        os.environ['USEAUX'] = "%d" % options.aux_use
        os.environ['MERGEMODE'] = "%d" % options.mode
        os.environ['MERGEGAP'] = "%d" % options.saving
        parser = parser_folder_m3u8.ParserFloderM3U8(options.folder)
        parser.dispose()
        convert_phase.do_work(options)
        parser.clean()
    except Exception as e:
        traceback.print_exc()

