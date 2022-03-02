import pandas as pd
from DTW import dtwfunction as dfunc
import os

GLOBAL_INIT_ID = 0

# Select feature 1.unit(unit vector) 2.scalar(normalized scalar) 3.vector  (default: unit)
FEATURE = 'vector'


def start(output_path):
    flag = False
    result_path = os.path.join(output_path, 'global_result')
    output_path = os.path.join(output_path, 'bev_result')

    # Check result directory is exist
    if not os.path.isdir(result_path):
        os.mkdir(result_path)

    txt_name = []
    for file in os.listdir(output_path):
        if file.endswith(".txt") and "BEV_" in file:
            txt_name.append(file)

    # Sort files
    # Among the file names, you must specify a location indicating the order
    # e.g., 'BEV_ch01-....' -> [2:4]
    txt_name = strange_sort(txt_name, 6, 8)

    # ID correction을 위한 id grouping
    # local_id_group_list: [CAM1_Local_ID_groupList, CAM2_Local_ID_groupList, CAM3_Local_ID_groupList]
    # drop_list: [CAM1_id_dropList, CAM2_id_dropList, CAM3_id_dropList]
    total_file_num = 4
    local_id_group_list = [[[1,5]],  # video1
                           [[3,9], [5,7,11], [4,6,8]],  # video2
                           [[3,7,10,12], [6,13,15], [5,14]],  # video3
                           [[2,10,12,13], [4,10,17], [3,11]]]  # video4
    drop_list = [[3,6],  # video1
                 [1,2,10],  # video2
                 [1,2,9,17],  # video3
                 [1,5,6,18]]  # video4

    # Create Dataframes by id
    result_df_list = []
    total_id_list = []

    for i in range(total_file_num):
        df_list, id_list = dfunc.make_df_list(os.path.join(output_path, txt_name[i]),
                                              local_id_group_list[i],
                                              drop_list[i], i+1)
        result_df_list.append(df_list)
        total_id_list.append(id_list)

    # Create id info list
    result_info_list = []

    # Select feature 1.unit(unit vector) 2.scalar(normalized scalar) 3.vector  (default: unit)
    # and generate result_info_list
    dfunc.select_feature(result_df_list, result_info_list, feature=FEATURE)

    # Create high similarity ID list
    # ToDo: 현재는 result0를 기준으로 나머지를 비교한 결과만 사용, 후에 나머지를 기준으로 구한 값도 고려해야함
    id_map_list = [[], [], [], []] # length of file
    for i in range(0, len(result_info_list)-1):
        result_dist_list = dfunc.check_similarity(result_info_list[i], result_info_list[i+1:])
        dfunc.id_mapping(result_dist_list, id_map_list[i])  # id_mapping에서 todo 처리

    print('### Global Re-ID list ###\n')
    print(id_map_list[0])

    # Assign global id
    global_id_set = []

    for i in range(1, len(id_map_list[0]) + 1):
        global_id_set.append(GLOBAL_INIT_ID + i)

    if global_id_set:
        flag = True

    dfunc.change_to_global(result_df_list, id_map_list[0], global_id_set)

    total_list = list()
    for T in result_df_list:
        for id_info in T:
            total_list += id_info.values.tolist()

    total_list.sort()

    global_I = dfunc.generate_global_info(total_list)
    global_df = pd.DataFrame(global_I)
    global_df.columns = ['frame', 'id', 'x', 'y']

    print(global_df)

    # Create Global information txt file
    global_df.to_csv(os.path.join(result_path, 'global_result.txt'),
                     sep=' ', header=None, index=None)

    return flag


def strange_sort(strings, n, m):
    return sorted(strings, key=lambda element: element[n:m])

if __name__ == '__main__':
    start('../output/edu_test1/')
