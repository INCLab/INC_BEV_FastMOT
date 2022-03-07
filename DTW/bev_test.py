from copy import copy

import cv2
import os
import sys
import shutil
import time

import pandas as pd
import numpy as np
import mimetypes

LOCAL_INIT_ID = 10000

select_id_list = []


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

    return


'''
id 라벨값에 맞춰 색깔을 지정하는 function
'''
def getcolor(idx):
    idx = idx * 3
    return (37 * idx) % 255, (17 * idx) % 255, (29 * idx) % 255


def strange_sort(strings, n, m):
    return sorted(strings, key=lambda element: element[n:m])


if __name__ == "__main__":
    start('../output/paper_eval_data/no_skip/10/', '../input/edu_map.png')