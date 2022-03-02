import csv
import pandas as pd
import numpy as np
import json

path = "data/"
df = pd.read_excel(path + 'no_skip.xlsx', usecols=[2,3], header=None)
df.fillna(-1, inplace=True)


data_dict = dict()
cam_dict = dict()
tar_dict = dict()

data_num = 1
tar = 1
cam = 1

for data in df[3].to_list():
    tar_name = 'tar'+str(tar)

    if type(data) is str:
        a = data.split(',')
        if a[-1] == '':
            a.remove('')
        a = list(map(int, a))

        if tar == 4:
            tar_dict['delete'] = a
        else:
            tar_dict[tar_name] = a
    else:
        tmp = []
        if data == -1:
            if tar == 4:
                tar_dict['delete'] = tmp
            else:
                tar_dict[tar_name] = tmp
        else:
            tmp.append(data)
            if tar == 4:
                tar_dict['delete'] = tmp
            else:
                tar_dict[tar_name] = tmp

    if tar == 4:
        tar = 1
        cam_dict['ch0' + str(cam)] = tar_dict
        tar_dict = dict()

        if cam == 4:
            data_dict[data_num] = cam_dict
            data_num += 1
            cam = 1
            cam_dict = dict()
        else:
            cam += 1
    else:
        tar += 1

file_path = 'data/2cam/no_skip.json'

with open(file_path, 'w') as outfile:
    json.dump(data_dict, outfile, indent=4)

# with open('data/no_skip.json') as f:
#     json_data = json.load(f)
#
# print(json_data['1'])