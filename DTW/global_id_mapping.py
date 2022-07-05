import pandas as pd
import dtwfunction as dfunc
import os
import json

# ############## User config params #################
'''
    * no_skip
    * skip5
    * skip10
'''
skip_list = ['no_skip',
             #'skip5',
             #'skip10'
             ]
'''
    * '../output/paper_3person'  testset: 50
    * '../output/paper_5person'  testset: 20
    * '../output/paper_10person' testset: 20 
'''
start_path = '../output/paper_3person'

test_person = '3person'
test_person_num = 3
test_start = 1
test_end = 50

SHOW_PROCESS = True
SAVE_FINAL_LIST = False
######################################################
SELECT_CAMERA = True
# If SELECT_CAMERA is True
select_list = [1, 4]

bev_list = []
if SELECT_CAMERA:
    if not select_list or len(select_list) == 1:
        print('Error: Select camera(>= 2)')
        exit()
    for idx in select_list:
        bev_list.append('BEV_ch0' + str(idx) + '.txt')

######################################################

# Select feature 1.unit(unit vector) 2.scalar(normalized scalar) 3.vector  (default: unit)
FEATURE_List = ['vector', 'unit', 'scalar']
############################################################


def start(output_path, skip):
    # Select json file by skip
    json_name = skip + '.json'
    data_path = os.path.join('data', test_person, json_name)

    # global mapping result list
    origin_output_path = output_path

    total_list = []
    for FEATURE in FEATURE_List:
        if SHOW_PROCESS:
            print("#################################################")
            print("##############      " + FEATURE + "      ##############")
            print("#################################################")
        result_list = list()

        for data_num in range(test_start, test_end + 1):
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
                    if SELECT_CAMERA:
                        if file in bev_list:
                            txt_name.append(file)
                    else:
                        txt_name.append(file)

            # Sort files
            # Among the file names, you must specify a location indicating the order
            # e.g., 'BEV_ch01-....' -> [2:4]
            txt_name = strange_sort(txt_name, 6, 8)

            # ID correction을 위한 id grouping
            # local_id_group_list: [CAM1_Local_ID_groupList, CAM2_Local_ID_groupList, CAM3_Local_ID_groupList]
            # drop_list: [CAM1_id_dropList, CAM2_id_dropList, CAM3_id_dropList]
            total_file_num = len(txt_name)

            # Read json data
            with open(data_path) as f:
                json_data = json.load(f)

            # Create dictionary by test case
            test_case_dict = json_data[str(data_num)]

            local_id_group_list = []
            drop_list = []

            cam_name = []
            if SELECT_CAMERA:
                for idx in select_list:
                    cam_name.append('ch0' + str(idx))
            else:
                for idx in range(1, total_file_num + 1):
                    cam_name.append('ch0' + str(idx))

            tar_name = ['tar' + str(i) for i in range(1, test_person_num+1)] + ['delete']

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

            for i in range(0, total_file_num):
                if SELECT_CAMERA:
                    cam_num = select_list[i]
                else:
                    cam_num = i+1

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
            result_dist_list = dfunc.check_similarity(result_info_list[0], result_info_list[1:])
            mapped_ids, not_mapped_ids = dfunc.id_mapping(result_dist_list, total_id_list)

            # 첫 매핑에서 매핑이 안된 아이디가 있고, 카메라가 3대 이상인 경우 나머지 카메라들끼리 비교하여
            # 매핑이 안된 아이디들에 대해 다시 매핑
            if total_file_num > 2 and not_mapped_ids:
                for i in range(1, len(result_info_list)-1):
                    result_dist_list = dfunc.check_similarity(result_info_list[i], result_info_list[i+1:])
                    tmp_mapped_ids, _ = dfunc.id_mapping(result_dist_list, total_id_list)

                    tmp_not_mapped_ids = not_mapped_ids.copy()
                    for ids in tmp_mapped_ids:
                        already_append = False
                        for n_id in tmp_not_mapped_ids:
                            if n_id in ids:
                                if already_append is False:
                                    is_in_mapped_set = False
                                    for mapped in mapped_ids:
                                        if is_in_mapped_set is True:
                                            break
                                        for id in ids:
                                            if id in mapped:
                                                is_in_mapped_set = True
                                                break
                                    if is_in_mapped_set is False:
                                        mapped_ids.append(ids)
                                    already_append = True
                                not_mapped_ids.remove(n_id)

            if not_mapped_ids:
                mapped_ids += not_mapped_ids

            if SHOW_PROCESS:
                print('### ' + str(data_num) + ': Global Re-ID list ###')
                print(mapped_ids)
            result_list.append(mapped_ids)

        total_list.append(result_list)

    ############ Create GT List #######################
    gt_list = []
    # Read json data
    with open(data_path) as f:
        json_data = json.load(f)

    for data_num in range(test_start, test_end + 1):
        test_case_dict = json_data[str(data_num)]

        # Create local mapping list with json data
        tar_list = [[] for i in range(0, test_person_num)]

        cam_name = []
        if SELECT_CAMERA:
            for idx in select_list:
                cam_name.append('ch0' + str(idx))
        else:
            for idx in range(1, total_file_num + 1):
                cam_name.append('ch0' + str(idx))

        tar_name = ['tar' + str(i) for i in range(1, test_person_num+1)] + ['delete']

        for cam in cam_name:

            if cam == 'ch01':
                start_id = 10000
            elif cam == 'ch02':
                start_id = 20000
            elif cam == 'ch03':
                start_id = 30000
            elif cam == 'ch04':
                start_id = 40000

            for idx, tar in enumerate(tar_name):
                if tar == 'delete':
                    break
                elif test_case_dict[cam][tar]:
                    tar_list[idx].append(start_id + test_case_dict[cam][tar][0])

        gt_list.append(tar_list)
    #####################################################################################

    # f1-score
    # import util
    # util.confusion_matrix(gt_list, total_list, test_person_num, select_list)

    # GT, vector, unit, scalar result
    final_list = []
    for i in range(0, test_end - test_start + 1):
        final_list.append(gt_list[i])
        final_list.append(total_list[0][i])  # vector
        final_list.append(total_list[1][i])  # unit
        final_list.append(total_list[2][i])  # scalar

    # Save final list
    if SAVE_FINAL_LIST:
        result_df = pd.DataFrame(final_list)

        if SELECT_CAMERA:
            result_df.to_excel(origin_output_path + 'result_' + str(len(select_list)) + 'cam' + str(select_list) + '.xlsx')

    eval(final_list, skip)
    
    return flag


def strange_sort(strings, n, m):
    return sorted(strings, key=lambda element: element[n:m])

'''
    gt_ids = [local_id1, local_id2, ...]
    cp_ids = [matched_id1, matched_id2, ...]
'''
def compare_list(gt_ids, cp_ids):
    flag = True

    if cp_ids:
        for cp in cp_ids:
            # GT와 묶인 id수가 같지 않을 경우 False
            if len(gt_ids) != len(cp_ids):
                flag = False
                break
            # 비교하는 local id 리스트에서 하나라도 GT와 다를경우 False
            if cp not in gt_ids:
                flag = False
                break
    else:
        flag = False

    return flag


def eval(f_list, skip):
    # Number of matching correctly
    vec_corr = 0
    unit_corr = 0
    scal_corr = 0

    # Number of matching correctly by each target
    vec_tar_score = [0 for i in range(0, len(f_list[0]))]
    unit_tar_score = [0 for i in range(0, len(f_list[0]))]
    scal_tar_score = [0 for i in range(0, len(f_list[0]))]

    # List of false matching index
    vec_false_list = []
    unit_false_list = []
    scal_false_list = []

    # Count test case
    total_case = 1

    for i in range(0, len(f_list)):
        if i % 4 != 3:
            continue

        list_gt = f_list[i - 3]
        list_vec = f_list[i - 2]
        list_unit = f_list[i - 1]
        list_scal = f_list[i]

        vec_result = [0 for i in range(0, len(list_gt))]
        unit_result = [0 for i in range(0, len(list_gt))]
        scal_result = [0 for i in range(0, len(list_gt))]

        for j in range(0, len(list_gt)):
            # Check vector feature
            vec_flag = False
            for vec in list_vec:
                match_result = compare_list(list_gt[j], vec)
                if match_result is True:
                    vec_flag = True
                    vec_tar_score[j] += 1
                    break

            # Check unit vector feature
            unit_flag = False
            for unit in list_unit:
                match_result = compare_list(list_gt[j], unit)
                if match_result is True:
                    unit_flag = True
                    unit_tar_score[j] += 1
                    break

            # Check scalar feature
            scal_flag = False
            for scal in list_scal:
                match_result = compare_list(list_gt[j], scal)
                if match_result is True:
                    scal_flag = True
                    scal_tar_score[j] += 1
                    break

            if vec_flag is True:
                vec_result[j] += 1
            if unit_flag is True:
                unit_result[j] += 1
            if scal_flag is True:
                scal_result[j] += 1

        if sum(vec_result) == len(vec_result):
            vec_corr += 1
        else:
            vec_false_list.append(total_case)

        if sum(unit_result) == len(unit_result):
            unit_corr += 1
        else:
            unit_false_list.append(total_case)

        if sum(scal_result) == len(scal_result):
            scal_corr += 1
        else:
            scal_false_list.append(total_case)


        total_case += 1

    total_case -= 1

    print('====== {}: Total Accuarcy ======'.format(skip))
    print('Vector: {} / {}'.format(vec_corr, total_case))
    print('Unit Vector: {} / {}'.format(unit_corr, total_case))
    print('Scalar: {} / {}'.format(scal_corr, total_case))
    print('\n')
    print('====== {}: Target Accuracy ======'.format(skip))
    print('Vector: {}'.format(vec_tar_score))
    print('Unit Vector: {}'.format(unit_tar_score))
    print('Scalar: {}'.format(scal_tar_score))
    print('\n')
    print('====== {}: False Matching Index ======'.format(skip))
    print('Vector: {}'.format(vec_false_list))
    print('Unit: {}'.format(unit_false_list))
    print('Scalar: {}'.format(scal_false_list))
    print('\n')


if __name__ == '__main__':
    for skip in skip_list:
        start(os.path.join(start_path, skip) + '/', skip)
