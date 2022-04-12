import math
import numpy as np
import dtw
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
# ############## User config params #################
FRAME_THRESHOLD = 1000

'''
    Window type for DTW distance
    1. none
    2. itakura (best)
'''
WIN_TYPE = 'none'


'''
    Feature scaler
    Default: Min-Max Normalizaton
    ZS_SCALER = True: Z-Score Normalization
'''
ZS_SCALER = False

# For data sampling & Sequence length tuning
USE_SAMPLING_INTERVAL = False
SAMPLING_INTERVAL = 2

SHOW_DTW_DIST = False  # DTW 거리값 리스트 출력
SHOW_LOCAL_ID_LIST = False  # 카메라마다 Tracking된 Local ID List(Local ID mapping 후) 출력
NORMALIZE_DTW_DIST = True
############################################################

LOCAL_INIT_ID = 10000

# ########### Preprocessing: ID Correction
'''
 If user choose IDs in single camera,
 those IDs are assigned to new same local ID(Start at 1000)
 <Input param>
 e.g., id_list = [[id1, id2],[id4, id5, id9],...] 
'''
def id_correction(id_list, mot_df, file_idx):
    # For changed ID by files
    # e.g., file1 -> Start id: 1xLOCAL_INIT_ID + 1 = 10001
    init_id = file_idx * LOCAL_INIT_ID

    if id_list[0]:
        for id_group in id_list:
            base_id = id_group[0]
            base_id = init_id + base_id
            for id in id_group:
                id = init_id + id
                mot_df['id'][(mot_df['id'] == id)] = base_id

        return mot_df
    else:
        return mot_df


'''
    Drop the incorrectly detected targets (e.g., Not a person)
'''
def id_drop(drop_list, mot_df, file_idx):
    init_id = file_idx * LOCAL_INIT_ID

    if drop_list:
        for id in drop_list:
            id = init_id + id
            mot_df.drop(mot_df[mot_df['id'] == id].index, inplace=True)
        return mot_df
    else:
        return mot_df


def make_df_list(filepath, cor_id_list, file_idx):
    result = pd.read_csv(filepath, delimiter=' ', header=None)
    result.columns = ['frame', 'id', 'x', 'y']

    # drop list 생성하기
    init_id = file_idx * LOCAL_INIT_ID
    id_list = list(set(result['id'].to_list()))

    total_id_list = []
    for ids in cor_id_list:
        total_id_list += ids

    drop_list = []
    if total_id_list:
        for i in range(0, len(total_id_list)):
            total_id_list[i] += init_id

        for id in id_list:
            if id in total_id_list:
                continue
            else:
                id -= init_id
                drop_list.append(id)

    if cor_id_list:
        result = id_correction(cor_id_list, result, file_idx)
    if drop_list:
        result = id_drop(drop_list, result, file_idx)

    id_df = result.drop_duplicates(['id'])
    id_list = id_df['id'].tolist()

    df_list = []

    for id in id_list:
        df = result[result['id'] == id]
        df.reset_index(drop=True, inplace=True)

        # Data Sampling
        if USE_SAMPLING_INTERVAL:
            sample_list = list(np.arange(0, len(df), SAMPLING_INTERVAL+1))
            df = df.iloc[sample_list, :]

        df_list.append(df)

    if SHOW_LOCAL_ID_LIST:
        print(id_list)

    return df_list, id_list


# ########## Create Feature for DTW #################
def create_unit_vec(df, threshold):
    # Normalization
    scaler = MinMaxScaler()

    if ZS_SCALER:
        scaler = StandardScaler()

    scaler.fit(df.iloc[:, 2:])
    scaled_df = scaler.transform(df.iloc[:, 2:])
    df.iloc[:, 2:] = scaled_df

    frame_list = df['frame'].to_list()
    id = df['id'].iloc[0]
    x_list = df['x'].to_list()
    y_list = df['y'].to_list()

    # return form : [frame_list[:-1], id, [dist_list]]
    info_list = [frame_list[:-1], id]
    unit_vec_list = []

    # calculate unit vector
    for i in range(0, len(x_list) - 1):
        if frame_list[i+1] - frame_list[i] > threshold:
            continue
        vec = np.array([x_list[i + 1] - x_list[i], y_list[i + 1] - y_list[i]])

        # For divide by 0
        if np.linalg.norm(vec) == 0:
            unit_vec = vec
        else:
            unit_vec = vec / np.linalg.norm(vec)
        unit_vec_list.append(unit_vec)

    unit_vec_list = np.array(unit_vec_list)
    info_list.append(unit_vec_list)

    return info_list


def create_scalar(df, threshold):
    # Normalization
    scaler = MinMaxScaler()

    if ZS_SCALER:
        scaler = StandardScaler()

    scaler.fit(df.iloc[:, 2:])
    scaled_df = scaler.transform(df.iloc[:, 2:])
    df.iloc[:, 2:] = scaled_df

    frame_list = df['frame'].to_list()
    id = df['id'].iloc[0]
    x_list = df['x'].to_list()
    y_list = df['y'].to_list()

    # return form : [frame_list[:-1], id, [dist_list]]
    info_list = [frame_list[:-1], id]
    scalar_list = []

    # calculate distance
    # for i in range(0, len(x_list) - 1):
    #     if frame_list[i+1] - frame_list[i] > threshold:
    #         continue
    #     dist = math.sqrt((x_list[i + 1] - x_list[i]) ** 2 + (y_list[i + 1] - y_list[i]) ** 2)
    #     scalar_list.append(dist)

    for i in range(0, len(x_list)):
        val = np.array([x_list[i], y_list[i]])
        scalar_list.append(val)

    info_list.append(scalar_list)

    return info_list


def create_vec(df, threshold):
    # Normalization
    scaler = MinMaxScaler()

    if ZS_SCALER:
        scaler = StandardScaler()

    scaler.fit(df.iloc[:, 2:])
    scaled_df = scaler.transform(df.iloc[:, 2:])
    df.iloc[:, 2:] = scaled_df

    frame_list = df['frame'].to_list()
    id = df['id'].iloc[0]
    x_list = df['x'].to_list()
    y_list = df['y'].to_list()

    # return form : [frame_list[:-1], id, [dist_list]]
    info_list = [frame_list[:-1], id]
    vec_list = []

    # calculate unit vector
    for i in range(0, len(x_list) - 1):
        if frame_list[i+1] - frame_list[i] > threshold:
            continue
        vec = np.array([x_list[i + 1] - x_list[i], y_list[i + 1] - y_list[i]])
        vec_list.append(vec)

    vec_list = np.array(vec_list)
    info_list.append(vec_list)

    return info_list
#########################################################################


# Select 1.unit vector or 2. normalized scalar or 3. vector
# Default: unit vector
def select_feature(result_df_list, info_list, feature='unit'):
    if feature == 'unit':
        for df_list in result_df_list:
            info = []
            for df in df_list:
                info.append(create_unit_vec(df, FRAME_THRESHOLD))

            info_list.append(info)
    elif feature == 'scalar':
        for df_list in result_df_list:
            info = []
            for df in df_list:
                info.append(create_scalar(df, FRAME_THRESHOLD))

            info_list.append(info)
    elif feature == 'vector':
        for df_list in result_df_list:
            info = []
            for df in df_list:
                info.append(create_vec(df, FRAME_THRESHOLD))

            info_list.append(info)

    return


def check_similarity(info_list, compare_list):
    '''
        기준 아이디에 대해 다른 result 파일에서 나온 모든 아이디들과 케이스별로 유사도 측정(혹은 제외) 후,
        DTW distance를 모두 저장
    '''
    # list of total dtw distance info
    result_list = []
    for _ in range(0, len(compare_list)):
        result_list.append([])

    # Loop for each result file
    for info in info_list:
        for i in range(0, len(compare_list)):
            for k in compare_list[i]:

                # vector값이 없는 경우 제외 (예를들어 포인트가 한번만 찍힌경우)
                if len(k[0]) == 0 or len(info[0]) == 0:
                    continue

                # *** 겹치지 않는경우: 일단 제외한다
                elif info[0][0] > k[0][-1] or info[0][-1] < k[0][0]:
                    continue

                # *** 포함하는 경우 : DTW로 유사도 측정
                # case 1
                elif info[0][0] <= k[0][0] and info[0][-1] >= k[0][-1]:
                    dist = dtw_overlap_frames(info, k, 1)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]
                # case 2
                elif info[0][0] >= k[0][0] and info[0][-1] <= k[0][-1]:
                    dist = dtw_overlap_frames(info, k, 2)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]

                # *** 절반이상 겹치는 경우 : DTW로 유사도 측정
                # case 3
                elif info[0][0] >= k[0][0] and info[0][int(len(info[0]) / 2)] <= k[0][-1] <= info[0][-1]:
                    dist = dtw_overlap_frames(info, k, 3)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]
                # case 4
                elif info[0][0] <= k[0][0] and k[0][int(len(k[0]) / 2)] <= info[0][-1] <= k[0][-1]:
                    dist = dtw_overlap_frames(info, k, 4)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]

                # *** 절반이하로 겹치는 경우: 제외?(포함하려면 위 코드와 합치기)
                elif k[0][0] <= info[0][0] < k[0][-1] < info[0][int(len(info[0]) / 2)]:
                    dist = dtw_overlap_frames(info, k, 3)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]
                elif info[0][0] <= k[0][0] < info[0][-1] < k[0][int(len(k[0]) / 2)]:
                    dist = dtw_overlap_frames(info, k, 4)
                    if dist != -1:
                        result_list[i].append([info[1], k[1], dist])  # [compare_id, compared_id, DTW_dist]
                else:
                    print('Not matching case!!!!')

    return result_list


'''
    이동경로를 비교할때 overlap 되는 frame에 해당하는 feature들만 골라서 DTW 적용 
'''
def dtw_overlap_frames(x_id_info, y_id_info, case):
    dist = -1
    x_frame_list = x_id_info[0]
    y_frame_list = y_id_info[0]

    x_vec_list = x_id_info[2]
    y_vec_list = y_id_info[2]

    start_idx = 0
    end_idx = 0

    # Case 1,2: 포함하는 경우

    # 비교타겟이 기준타겟에 포함
    if case == 1:
        try:
            start_idx = x_frame_list.index(y_frame_list[0])
        except:
            min = 99999
            for i in range(0, len(x_frame_list)):
                if abs(x_frame_list[i] - y_frame_list[0]) < min:
                    min = abs(x_frame_list[i] - y_frame_list[0])
                    start_idx = i
        try:
            end_idx = x_frame_list.index(y_frame_list[-1])
        except:
            min = 99999
            for i in range(0, len(x_frame_list)):
                if abs(x_frame_list[i] - y_frame_list[-1]) < min:
                    min = abs(x_frame_list[i] - y_frame_list[-1])
                    end_idx = i

        # If vector length == 1, it accur dimension mismatch error
        try:
            dist = dtw.dtw(x_vec_list[start_idx:end_idx + 1], y_vec_list, keep_internals=True, window_type=WIN_TYPE).distance
            if NORMALIZE_DTW_DIST:
                dist = dist / (len(x_vec_list[start_idx:end_idx + 1]) + len(y_vec_list))
        except:
            dist = -1

    # 기준타겟이 비교타겟에 포함
    elif case == 2:
        try:
            start_idx = y_frame_list.index(x_frame_list[0])
        except:
            min = 99999
            for i in range(0, len(y_frame_list)):
                if abs(y_frame_list[i] - x_frame_list[0]) < min:
                    min = abs(y_frame_list[i] - x_frame_list[0])
                    start_idx = i
        try:
            end_idx = y_frame_list.index(x_frame_list[-1])
        except:
            min = 99999
            for i in range(0, len(y_frame_list)):
                if abs(y_frame_list[i] - x_frame_list[-1]) < min:
                    min = abs(y_frame_list[i] - x_frame_list[-1])
                    end_idx = i

        # If vector length == 1, it accur dimension mismatch error
        try:
            dist = dtw.dtw(x_vec_list, y_vec_list[start_idx:end_idx + 1], keep_internals=True, window_type=WIN_TYPE).distance
            if NORMALIZE_DTW_DIST:
                dist = dist / (len(x_vec_list) + len(y_vec_list[start_idx:end_idx + 1]))
        except:
            dist = -1

    # Case 3,4: 겹치는 경우
    elif case == 3:
        try:
            start_idx = y_frame_list.index(x_frame_list[0])
        except:
            min = 99999
            for i in range(0, len(y_frame_list)):
                if abs(y_frame_list[i] - x_frame_list[0]) < min:
                    min = abs(y_frame_list[i] - x_frame_list[0])
                    start_idx = i
        try:
            end_idx = x_frame_list.index(y_frame_list[-1])
        except:
            min = 99999
            for i in range(0, len(x_frame_list)):
                if abs(x_frame_list[i] - y_frame_list[-1]) < min:
                    min = abs(x_frame_list[i] - y_frame_list[-1])
                    end_idx = i

        # If vector length == 1, it accur dimension mismatch error
        try:
            dist = dtw.dtw(x_vec_list[:end_idx + 1], y_vec_list[start_idx:], keep_internals=True, window_type=WIN_TYPE).distance
            if NORMALIZE_DTW_DIST:
                dist = dist / (len(x_vec_list[:end_idx + 1]) + len(y_vec_list[start_idx:]))
        except:
            dist = -1

    elif case == 4:
        try:
            start_idx = x_frame_list.index(y_frame_list[0])
        except:
            min = 99999
            for i in range(0, len(x_frame_list)):
                if abs(x_frame_list[i] - y_frame_list[0]) < min:
                    min = abs(x_frame_list[i] - y_frame_list[0])
                    start_idx = i
        try:
            end_idx = y_frame_list.index(x_frame_list[-1])
        except:
            min = 99999
            for i in range(0, len(y_frame_list)):
                if abs(y_frame_list[i] - x_frame_list[-1]) < min:
                    min = abs(y_frame_list[i] - x_frame_list[-1])
                    end_idx = i

        # If vector length == 1, it accur dimension mismatch error
        try:
            dist = dtw.dtw(x_vec_list[start_idx:], y_vec_list[:end_idx + 1], keep_internals=True, window_type=WIN_TYPE).distance
            if NORMALIZE_DTW_DIST:
                dist = dist / (len(x_vec_list[start_idx:]) + len(y_vec_list[:end_idx + 1]))
        except:
            dist = -1

    return dist


def id_mapping(distance_list, total_id_list):
    mapping_list = []
    for dist_list in distance_list:
        sorted_list = sorted(dist_list, key=lambda x: (x[2], x[0]))

        if SHOW_DTW_DIST is True:
            print(sorted_list)

        while sorted_list:
            compare_id = sorted_list[0][0]
            compared_id = sorted_list[0][1]

            check = 0
            for ids in mapping_list:
                if compare_id in ids:
                    if compared_id not in ids:
                        ids.append(compared_id)
                    check = 1
                    break
                if compared_id in ids:
                    if compare_id not in ids:
                        ids.append(compare_id)
                    check = 1
                    break

            if check == 0:
                mapping_list.append([compare_id, compared_id])

            # Delete duplicate id list
            sorted_list = [i for i in sorted_list if not compare_id in i]
            sorted_list = [i for i in sorted_list if not compared_id in i]

    # local ID mapping이 되지 않은 local ID는 단독으로 mapping list에 추가
    not_mapped_ids = []
    for v_ids in total_id_list:
        for id in v_ids:
            flag = False
            for map_ids in mapping_list:
                if id in map_ids:
                    flag = True
            if flag is False:
                not_mapped_ids.append([id])

    return mapping_list, not_mapped_ids


# Input: dataframe list by camera & id
# Output: Same as input but id == global_id
def change_to_global(T_set, id_set, gid_set):
    for T in T_set:
        for id_info in T:
            for i in range(0, len(id_set)):
                if id_info['id'].iloc[0] in id_set[i]:
                    id_info['id'] = gid_set[i]
                    break
    return


# Input: total_info = [[frame, id, x, y], ...]
def generate_global_info(total_info):
    I_G = list()

    accum_x = [0, 0]  # [accumulative x, number of target]
    accum_y = [0, 0]

    for i in range(0, len(total_info)):
        if i != len(total_info) - 1 and total_info[i][0] == total_info[i + 1][0] and total_info[i][1] == \
                total_info[i + 1][1]:
            accum_x[0] += total_info[i][2]
            accum_y[0] += total_info[i][3]

            accum_x[1] += 1
            accum_y[1] += 1
        else:
            if accum_x[1] != 0:
                accum_x[0] += total_info[i][2]
                accum_y[0] += total_info[i][3]

                accum_x[1] += 1
                accum_y[1] += 1

                avg_x = int(accum_x[0] / accum_x[1])
                avg_y = int(accum_y[0] / accum_y[1])

                I_G.append([total_info[i][0], total_info[i][1], avg_x, avg_y])

                # init
                accum_x = [0, 0]
                accum_y = [0, 0]
            else:
                I_G.append(total_info[i])

    return I_G