import os
import csv
import pandas as pd
import numpy as np
import json

test_person = 5
data_path = "data/5person"
skip = 'skip10'
df = pd.read_excel(os.path.join(data_path, skip + '.xlsx'), usecols=[2, 3], header=None)

# 빈 셀에는 -1로 채우기 -> 후처리 편하게 하기위해
df.fillna(-1, inplace=True)


data_dict = dict()
cam_dict = dict()
tar_dict = dict()

data_num = 1
tar = 1
cam = 1

# ## df[3].to_list -> local id list
for data in df[3].to_list():
    tar_name = 'tar'+str(tar)

    if type(data) is str:
        a = data.split(',')
        if a[-1] == '':
            a.remove('')
        a = list(map(int, a))

        if tar == test_person + 1:
            tar_dict['delete'] = a
        else:
            tar_dict[tar_name] = a
    else:
        tmp = []
        if data == -1:
            if tar == test_person + 1:
                tar_dict['delete'] = tmp
            else:
                tar_dict[tar_name] = tmp
        else:
            tmp.append(data)
            if tar == test_person + 1:
                tar_dict['delete'] = tmp
            else:
                tar_dict[tar_name] = tmp

    if tar == test_person + 1:
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

file_path = os.path.join(data_path, skip + '.json')

with open(file_path, 'w') as outfile:
    json.dump(data_dict, outfile, indent=4)

with open(file_path) as f:
    json_data = json.load(f)

print(json_data['1'])