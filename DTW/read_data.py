import os
import csv
import pandas as pd
import numpy as np
import json

test_person = 5
data_path = "data/5person"
df = pd.read_excel(os.path.join(data_path, 'no_skip.xlsx'), usecols=[2,3], header=None)

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

file_path = os.path.join(data_path, 'no_skip.json')

with open(file_path, 'w') as outfile:
    json.dump(data_dict, outfile, indent=4)

with open(file_path) as f:
    json_data = json.load(f)

print(json_data['1'])



# json_name = 'no_skip.json'
# data_path = 'data/' + json_name
#
# # Read json data
# with open(data_path) as f:
#     json_data = json.load(f)
#
# result_list = []
#
# for data_num in range(1,51):
#     test_case_dict = json_data[str(data_num)]
#
#     cam_name = ['ch01', 'ch02', 'ch03', 'ch04']
#     tar_name = ['tar1', 'tar2', 'tar3', 'delete']
#
#     # Create local mapping list with json data
#     tar_list = [[], [], []]
#
#     for cam in cam_name:
#         if cam == 'ch01':
#             start_id = 10000
#         elif cam == 'ch02':
#             start_id = 20000
#         elif cam == 'ch03':
#             start_id = 30000
#         elif cam == 'ch04':
#             start_id = 40000
#
#         for tar in tar_name:
#             if tar == 'delete':
#                 break
#             elif tar == 'tar1' and test_case_dict[cam][tar]:
#                 tar_list[0].append(start_id + test_case_dict[cam][tar][0])
#             elif tar == 'tar2' and test_case_dict[cam][tar]:
#                 tar_list[1].append(start_id + test_case_dict[cam][tar][0])
#             elif tar == 'tar3' and test_case_dict[cam][tar]:
#                 tar_list[2].append(start_id + test_case_dict[cam][tar][0])
#     result_list.append(tar_list)
#
# result_df = pd.DataFrame(result_list)
# result_df.to_excel('gt.xlsx')
