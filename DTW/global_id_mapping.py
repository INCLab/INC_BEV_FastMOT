import pandas as pd
import dtwfunction as dfunc
import os
import json

# Select feature 1.unit(unit vector) 2.scalar(normalized scalar) 3.vector  (default: unit)
FEATURE_List = ['vector','unit','scalar']
json_name = 'skip10.json'
data_path = 'data/' + json_name


def start(output_path):
    # global mapping result list
    origin_output_path = output_path

    total_list = []
    for FEATURE in FEATURE_List:
        print("#################################################")
        print("##############      " + FEATURE + "      ##############")
        print("#################################################")
        result_list = list()
        for data_num in range(1, 51):
            if data_num == 9:
                result_list.append([[], [], []])
                continue
                
            output_path = origin_output_path
            output_path = output_path + str(data_num) + '/'
            flag = False
            result_path = os.path.join(output_path, 'global_result')
            output_path = os.path.join(output_path, 'bev_result')

            # Check result directory is exist
            if not os.path.isdir(result_path):
                os.mkdir(result_path)

            txt_name = []
            for file in os.listdir(output_path):
                if file.endswith(".txt") and "BEV_" in file:
                    if file == "BEV_ch01.txt" or file == "BEV_ch04.txt":
                        txt_name.append(file)

            # Sort files
            # Among the file names, you must specify a location indicating the order
            # e.g., 'BEV_ch01-....' -> [2:4]
            txt_name = strange_sort(txt_name, 6, 8)

            # ID correction을 위한 id grouping
            # local_id_group_list: [CAM1_Local_ID_groupList, CAM2_Local_ID_groupList, CAM3_Local_ID_groupList]
            # drop_list: [CAM1_id_dropList, CAM2_id_dropList, CAM3_id_dropList]
            total_file_num = 2

            # Read json data
            with open(data_path) as f:
                json_data = json.load(f)

            # Create dictionary by test case
            test_case_dict = json_data[str(data_num)]

            local_id_group_list = []
            drop_list = []

            cam_name = ['ch01', 'ch04']
            tar_name = ['tar1', 'tar2', 'tar3', 'delete']

            # Create local mapping list with json data
            for cam in cam_name:
                local_id_list = []
                for tar in tar_name:
                    if tar == 'delete':
                        drop_list.append(test_case_dict[cam][tar])
                    else:
                        if test_case_dict[cam][tar]:
                            local_id_list.append(test_case_dict[cam][tar])
                local_id_group_list.append(local_id_list)

            # Create Dataframes by id
            result_df_list = []
            total_id_list = []

            for i in range(total_file_num):
                if i == 0:
                    cam_num = 1
                elif i == 1:
                    cam_num = 4
                df_list, id_list = dfunc.make_df_list(os.path.join(output_path, txt_name[i]),
                                                      local_id_group_list[i],
                                                      cam_num)
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

            print('### ' + str(data_num) + ': Global Re-ID list ###')
            print(id_map_list[0])
            result_list.append(id_map_list[0])
        total_list.append(result_list)

    ############ Create GT List #######################
    gt_list = []
    # Read json data
    with open(data_path) as f:
        json_data = json.load(f)

    for data_num in range(1, 51):
        test_case_dict = json_data[str(data_num)]

        # Create local mapping list with json data
        tar_list = [[], [], []]

        cam_name = ['ch01', 'ch04']
        tar_name = ['tar1', 'tar2', 'tar3', 'delete']

        for cam in cam_name:

            if cam == 'ch01':
                start_id = 10000
            elif cam == 'ch04':
                start_id = 40000

            for tar in tar_name:
                if tar == 'delete':
                    break
                elif tar == 'tar1' and test_case_dict[cam][tar]:
                    tar_list[0].append(start_id + test_case_dict[cam][tar][0])
                elif tar == 'tar2' and test_case_dict[cam][tar]:
                    tar_list[1].append(start_id + test_case_dict[cam][tar][0])
                elif tar == 'tar3' and test_case_dict[cam][tar]:
                    tar_list[2].append(start_id + test_case_dict[cam][tar][0])
        gt_list.append(tar_list)
    #####################################################################################

    # GT, vector, unit, scalar result
    final_list = []
    for i in range(0, 50):
        final_list.append(gt_list[i])
        final_list.append(total_list[0][i])  # vector
        final_list.append(total_list[1][i])  # unit
        final_list.append(total_list[2][i])  # scalar

    result_df = pd.DataFrame(final_list)
    result_df.to_excel(origin_output_path + 'result_2cam14.xlsx')
    
    return flag


def strange_sort(strings, n, m):
    return sorted(strings, key=lambda element: element[n:m])

if __name__ == '__main__':
    start('../output/paper_eval_data/skip10/')
