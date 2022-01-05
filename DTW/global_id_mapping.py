import dtwfunction_DB_ver as dfunc

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import DB.database as Database

LOCAL_INIT_ID = 1000
GLOBAL_INIT_ID = 10000


# 정익:6 / 13 / 21 민재:3 / 15 / 22 찬영:7 / 18 / 23

def start(video_names):
    flag = False

    video_id_list = []
    for name in video_names:
        video_id_list.append(Database.getVideoId(name))

    print("========= Get MOT data =========\n")

    total_mot_list = []
    for video_id in video_id_list:
        mot_list = Database.getBEVDatabyVideoId(video_id)
        print(mot_list)
        total_mot_list.append(mot_list)

    video_num = len(total_mot_list)

    print("OK\n")

    # ID correction을 위한 id grouping
    # local_id_group_list: [CAM1_Local_ID_groupList, CAM2_Local_ID_groupList, CAM3_Local_ID_groupList]
    # drop_list: [CAM1_id_dropList, CAM2_id_dropList, CAM3_id_dropList]
    # Todo: frame display를 통해 보여줄지, 직접확인하고 입력값만 받을지
    local_id_group_list = [[[5, 7]], [[1, 8]], [[]]]
    drop_list = [[2], [9], [4]]

    print("========= Create DF list =========\n")

    # Create Dataframes by id
    result_df_list = []
    v_result_df_list = []  # Add 'video_id' column in front of result_df_list
    total_id_list = []
    for i in range(0, video_num):
        df_list, id_list, v_df_list = dfunc.make_df_list(total_mot_list[i], local_id_group_list[i], drop_list[i], LOCAL_INIT_ID, video_id_list[i])
        result_df_list.append(df_list)
        total_id_list.append(id_list)
        v_result_df_list.append(v_df_list)

    print("OK\n")

    # Create id info list
    result_info_list = []

    # Select feature 1.unit(unit vector) 2.scalar(normalized scalar) 3.vector  (default: unit)
    # and generate result_info_list
    dfunc.select_feature(result_df_list, result_info_list, feature='vector')


    # Create high similarity ID list
    # ToDo: 현재는 result0를 기준으로 result1,2를 비교한 결과만 사용, overlap MTMCT task이므로 비디오 중 가장 많은 target이
    id_map_list = [[], []]
    for i in range(0, len(result_info_list)-1):
        result_dist_list = dfunc.check_similarity(result_info_list[i], result_info_list[i+1:])
        dfunc.id_mapping(result_dist_list, id_map_list[i])  # id_mapping에서 todo 처리

    print("====== Global mapping result ======\n")
    print(id_map_list[0])

    # Assign global id
    global_id_set = []

    for i in range(1, len(id_map_list[0]) + 1):
        global_id_set.append(GLOBAL_INIT_ID + i)

    dfunc.change_to_global(result_df_list, id_map_list[0], global_id_set)

    total_list = list()
    for T in result_df_list:
        for id_info in T:
            total_list += id_info.values.tolist()

    total_list.sort()

    global_I = dfunc.generate_global_info(total_list)

    print("========= Create Global table =========\n")
    mappingInfo_df_list = dfunc.generate_mapping_df(v_result_df_list, id_map_list[0], global_id_set)

    if mappingInfo_df_list:
        mappingInfo = dfunc.generate_mappingInfo(mappingInfo_df_list)
        group_id = Database.getGroupIDbyVideoID(video_id_list[0])
        Database.insertGlobalTrackingInfo(group_id, mappingInfo, global_I)
        flag = True
        print("OK\n")
        return flag
    else:
        print("Warning: Global mapping info is not exist.\n")
        return flag



    # global_df = pd.DataFrame(global_I)
    # global_df.columns = ['frame', 'id', 'x', 'y']
    #
    # print(global_df)
    #
    # # Create Global information txt file
    # global_df.to_csv('global_result.txt', sep=' ', header=None, index=None)



