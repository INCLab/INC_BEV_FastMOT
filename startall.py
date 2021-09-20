# FastMOT 작업 후 바로 BEV 실행
# Frame 저장 위치는 ./output/frame으로 설정해야 함

import argparse
import json
import logging
import os
import fastmot
import cv2
from fastmot.utils import ConfigDecoder, Profiler
from pathlib import Path
from types import SimpleNamespace

def start():
    #### Arguments Setting ####
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    group = parser.add_mutually_exclusive_group()
    required.add_argument('-i', '--input-uri', metavar="URI", required=True,
                          help='Input Video Folder')
    required.add_argument('-o', '--output-uri', metavar="URI",
                          help='Output File (Video, Text, Frame) Folder')
    required.add_argument('-m', '--map-uri', metavar="URI",
                          help='Map Image File URI')
    optional.add_argument('-c', '--config', metavar="FILE",
                          default=Path(__file__).parent / 'cfg' / 'mot.json',
                          help='path to JSON configuration file')
    optional.add_argument('-s', '--show', action='store_true', help='show visualizations')
    group.add_argument('-q', '--quiet', action='store_true', help='reduce output verbosity')
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser._action_groups.append(optional)
    args = parser.parse_args()

    # set up logging
    logging.basicConfig(format='%(asctime)s [%(levelname)8s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("INC_BEV_FastMOT")
    if args.quiet:
        logger.setLevel(logging.WARNING)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


    # load config file
    with open(args.config) as cfg_file:
        config = json.load(cfg_file, cls=ConfigDecoder, object_hook=lambda d: SimpleNamespace(**d))

    #### Run FastMOT ####

    # Input 경로에 있는 모든 파일 읽기
    videolist = os.listdir(args.input_uri)

    # 모든 File 읽기 위해 Loop
    for videofile in videolist:
        # 이름과 확장자 분리
        name, ext = os.path.splitext(videofile)

        # 확장자가 .mp4인 경우
        if ext == ".mp4":
            # FastMOT 실행

            stream = fastmot.VideoIO(config.resize_to, args.input_uri + '/' + videofile, args.output_uri, **vars(config.stream_cfg))
            mot = fastmot.MOT(config.resize_to, **vars(config.mot_cfg), draw=True)
            mot.reset(stream.cap_dt)

            Path(args.output_uri).parent.mkdir(parents=True, exist_ok=True)
            txt = open(args.output_uri + '/' + name + '.txt', 'w')

            Path(args.output_uri + '/frame/' + name + '/').mkdir(parents=True, exist_ok=True)
            framecount = 0

            if args.show:
                cv2.namedWindow('Video', cv2.WINDOW_AUTOSIZE)

            logger.info('Starting video capture... ({})'.format(videofile))
            stream.start_capture()
            try:
                with Profiler('app') as prof:
                    while not args.show or cv2.getWindowProperty('Video', 0) >= 0:
                        frame = stream.read()
                        if frame is None:
                            break

                        mot.step(frame)

                        for track in mot.visible_tracks():
                            tl = track.tlbr[:2] / config.resize_to * stream.resolution
                            br = track.tlbr[2:] / config.resize_to * stream.resolution
                            w, h = br - tl + 1

                            # New Text Format
                            txt.write(
                                f'{mot.frame_count} {track.trk_id} {int(tl[0] + w / 2)} {int((tl[1] + h) - 10)}\n')

                        if args.show:
                            cv2.imshow('Video', frame)
                            if cv2.waitKey(1) & 0xFF == 27:
                                break

                        cv2.imwrite("{}/{}.jpg".format(Path(args.output_uri + '/frame/' + name + '/'), framecount), frame)
                        framecount += 1
                        stream.write(frame)
            finally:
                # clean up resources
                if txt is not None:
                    txt.close()
                stream.release()
                cv2.destroyAllWindows()

                avg_fps = round(mot.frame_count / prof.duration)
                logger.info('Average FPS: %d', avg_fps)
                mot.print_timing_info()

        #### Run BEV ####

if __name__ == '__main__':
    start()

