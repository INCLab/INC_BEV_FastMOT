from copy import copy

import cv2
import os
import sys
import shutil
import time
import re
import subprocess

import pandas as pd
import numpy as np
import mimetypes

LOCAL_INIT_ID = 10000

select_id = True
select_id_list = [[10002,40001,40005],[10001,10004,40002,40008,40010]]

skip = 'skip10'
test_case = 2


def start(output_path, map_path):
    original_output_path = output_path
    output_path = os.path.join(output_path, 'bev_result')
    map_output_path = os.path.join(original_output_path, 'map_frame')

    txt_name = []
    for file in os.listdir(output_path):
        if file.endswith(".txt") and "BEV_" in file:
            if file == "BEV_ch01.txt" or file == "BEV_ch04.txt":
                txt_name.append(file)

    if not os.path.exists(map_output_path):
        os.makedirs(map_output_path)
    else:
        shutil.rmtree(map_output_path)
        os.makedirs(map_output_path)


    # Sort files
    # Among the file names, you must specify a location indicating the order
    # e.g., 'ch01-....' -> [2:4], 'BEV_ch01-....' -> [6:8]
    txt_name = strange_sort(txt_name, 6, 8)

    file_num = len(txt_name)

    frame_list = []
    id_list = []
    x_list = []
    y_list = []

    for file in txt_name:
        filepath = os.path.join(output_path, file)
        df = pd.read_csv(filepath, delimiter=' ', header=None)
        df.columns = ['frame', 'id', 'x', 'y']

        frame_list.append(df['frame'].to_list())
        id_list.append(df['id'].to_list())
        x_list.append(df['x'].to_list())
        y_list.append(df['y'].to_list())

    max_frame = 0
    for frames in frame_list:
        if frames[-1] > max_frame:
            max_frame = frames[-1]

    map = cv2.imread(str(map_path), -1)

    print("Create BEV map_frame...")
    for idx in range(1, max_frame + 1):
        for num in range(0, file_num):
            f_idx = 0
            for frame in frame_list[num]:

                if idx == frame:
                    if select_id is True:
                        id = id_list[num][f_idx]
                        x = x_list[num][f_idx]
                        y = y_list[num][f_idx]

                        for i in range(0, len(select_id_list)):
                            if id in select_id_list[i]:
                                color = getcolor(abs(i+1))
                                cv2.circle(map, (int(x), int(y)), 5, color, -1)
                    else:
                        id = id_list[num][f_idx]
                        x = x_list[num][f_idx]
                        y = y_list[num][f_idx]

                        color = getcolor(abs(id))
                        cv2.circle(map, (int(x), int(y)), 5, color, -1)

                    f_idx += 1
                elif idx < frame:
                    break
                else:
                    f_idx += 1

            src = os.path.join(map_output_path, str(idx) + '.jpg')

            cv2.imwrite(src, map)
    print("Done")


    ## Create BEV Video
    print("Start create BEV_Video")
    paths = [os.path.join(map_output_path, i) for i in os.listdir(map_output_path) if re.search(".jpg$", i)]

    ## 정렬 작업
    store1, store2, store3, store4 = [], [], [], []
    for i in paths:
        if len(i.split('\\')[-1]) == 8:
            store4.append(i)
        elif len(i.split('\\')[-1]) == 7:
            store3.append(i)
        elif len(i.split('\\')[-1]) == 6:
            store2.append(i)
        elif len(i.split('\\')[-1]) == 5:
            store1.append(i)

    paths = list(np.sort(store1)) + list(np.sort(store2)) + list(np.sort(store3)) + list(np.sort(store4))
    # len('ims/2/a/2a.2710.png')

    fps = 30
    frame_array = []
    size = None
    output_idx = 1

    for idx, path in enumerate(paths):
        img = cv2.imread(path)
        height, width, layers = img.shape
        size = (width, height)
        frame_array.append(img)

        if len(frame_array) >= 4500 or idx == len(paths) - 1:
            writer = cv2.VideoWriter(os.path.join(original_output_path, str(output_idx) + 'output.mp4'),
                                     cv2.CAP_GSTREAMER,
                                     fps,
                                     (1920, 1080))
            for i in range(len(frame_array)):
                #frame_array[i] = cv2.resize(frame_array[i], dsize=(1280, 720), interpolation=cv2.INTER_LINEAR)
                writer.write(frame_array[i])

            writer.release()
            frame_array.clear()
            output_idx += 1

    print(size)
    print('Done')

    return


'''
id 라벨값에 맞춰 색깔을 지정하는 function
'''
def getcolor(idx):
    idx = idx * 3
    return (37 * idx) % 255, (17 * idx) % 255, (29 * idx) % 255


def strange_sort(strings, n, m):
    return sorted(strings, key=lambda element: element[n:m])


def _gst_write_pipeline(output_uri):
    gst_elements = str(subprocess.check_output('gst-inspect-1.0'))
    # use hardware encoder if found
    if 'omxh264enc' in gst_elements:
        h264_encoder = 'omxh264enc'
    elif 'x264enc' in gst_elements:
        h264_encoder = 'x264enc'
    else:
        raise RuntimeError('GStreamer H.264 encoder not found')
    pipeline = (
            'appsrc ! autovideoconvert ! %s ! mp4mux ! filesink location=%s '
            % (
                h264_encoder,
                output_uri
            )
    )
    return pipeline


if __name__ == "__main__":
    start('../output/paper_eval_data/' + os.path.join(skip, str(test_case)) + '/', '../input/edu_map.png')