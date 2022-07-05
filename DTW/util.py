'''
   1. index가 가장빠른 cam을 real(confusion matrix)로 선택(real_cam)
   2. 각각의 샘플에 i에 대해 gt list[i]에 포함된 matching ids list에 대해서 target1부터 차례대로 순회
   3. 해당 matching ids 중 real_cam의 id(rc_id) 선택 후 predict_maching list에서 rc_id를 포함하는 리스트 선택
   4. 만일 real_cam에서 해당 rc_id가 tracking이 안된경우 다음 index cam에 대한 rc_id 선택 후  predict_maching list에서
      rc_id를 포함하는 리스트 선택
   5. 해당 리스트에서 각각의 cam에 대응 하는 아이디가 어느 target을 나타내고있는지 each cam target list에 표시
   6. 예를들어 총 target이 3명인 경우에 대해 target1_matching_list에서 cam2의 target3이 포함되어있다면
       cam2_target_list = [ sample1[ tar1[0, 0, 1], tar2[...], tar3[...] ],
                           sample2[...],
                           ...
                           ]
'''

from operator import add


def confusion_matrix(gt_list, total_list, test_person_num, cam_list):
    '''
        total_list[0]: vector
        total_list[1]: unit
        total_list[2]: scalar
    '''
    samples = len(gt_list)  # number of samples

    for feature_idx, predict_matched_list in enumerate(total_list):

        # confusion matrix를 위한 카메라별 리스트를 딕셔너리형태로 생성(real_cam 제외)
        cam_dict = {}
        cam_list = sorted(cam_list)

        # 각 카메라 별로 0으로 초기화된 샘플별 타겟 매칭정보 리스트 생성
        for cam_idx in cam_list[1:]:
            cam_dict[cam_idx] = [[[0 for _ in range(0, test_person_num)]  # 타겟 수만큼 0으로 초기화
                                  for _ in range(0, test_person_num)]  # 타겟 수만큼 초기화된 리스트 생성
                                 for _ in range(0, samples)]  # 샘플수 만큼 리스트 생성

        for sample_idx, sample_gt in enumerate(gt_list):
            for tar_idx, tar in enumerate(sample_gt):

                # 현재 샘플에서 해당 타겟에 대한 매칭 리스트가 존재하는 경우
                # 현재 샘플에서 해당 타겟에 대한 매칭 리스트가 존재하지 않는 경우는 초기화 상태 그대로 두기 때문에 무시
                if tar:
                    rc_id = min(tar)  # matching id에서 가장 빠른 cam의 아이디 선택

                    for match_list in predict_matched_list[sample_idx]:
                        # rc_id가 포함된 리스트 선택 (rc_id가 존재할때 rc_id를 포함하는 리스트는 무조건 존재)
                        if rc_id in match_list:
                            for id in match_list:
                                if id == rc_id:
                                    continue
                                else:
                                    # 해당 아이디가 어떤 캠의 로컬아이디인지
                                    id_from_cam = int(id / 10000)
                                    # gt에서 어느 타겟에 속하는지
                                    for gt_idx, gt in enumerate(sample_gt):
                                        if id in gt:
                                            # 해당 cam 리스트에서 샘플번호에 맞게 정보 추가
                                            cam_dict[id_from_cam][sample_idx][tar_idx][gt_idx] += 1
                                            break
                            break

        c_mat = [[0 for _ in range(0, 3)] for _ in range(0, test_person_num)]  # confusion matrix

        # 각각의 샘플에 대해서 real_target별로 Precision, Recall 계산
        # real_target에 대한 TP와 FN, FP 만 계산하면됨
        # 초기화된 2D confusion matrix에 값 채워넣기
        for smp in range(0, samples):

            # real target index
            for real_tar_idx in range(0, test_person_num):
                tar_info_map = [0 for _ in range(0, test_person_num)]

                # 각각의 cam에서 matching된 타겟 정보를 다 다해서 비교
                for key in cam_dict.keys():
                    tar_info_map = list(map(add, tar_info_map, cam_dict[key][smp][real_tar_idx]))

                # 카메라 별 타겟 매칭 정보의 합에서 real_target을 제외한 다른 target에 매칭된 정보가 없을 경우
                if sum([j for i, j in enumerate(tar_info_map) if i != real_tar_idx]) == 0:
                    c_mat[real_tar_idx][real_tar_idx] += 1

                # 기준 카메라를 제외한 모든 카메라들이 동일한 target에 대해 매칭되었지만 !real_target
                # 나머지 상황에 대해서는 무시
                else:
                    for i, tar_info in enumerate(tar_info_map):
                        if i == real_tar_idx:
                            continue
                        if tar_info == len(cam_dict):
                            c_mat[real_tar_idx][i] += 1

        ft_name = ''
        if feature_idx == 0:
            ft_name = 'Vector'
        elif feature_idx == 1:
            ft_name = 'Unit'
        elif feature_idx == 2:
            ft_name = 'Scalar'

        # Calculate f1 score
        print('\n\n#### {} f1-score ####'.format(ft_name))
        fsc = f1_score(c_mat)
        print('\nF1-Score: {}\n'.format(fsc))


def f1_score(cf_matrix):
    tar_num = len(cf_matrix)

    # 각각의 real target 별로 TP, FN, FP 초기화 정보가 담긴 dictionary 생성
    cf_dict = {}
    for idx in range(0, tar_num):
        cf_dict[idx] = {
            'TP': 0,
            'FN': 0,
            'FP': 0,
            'PC': 0.,  # Precision
            'RC': 0.   # Recall
        }

    for real_idx in range(0, tar_num):
        for pred_idx in range(0, tar_num):
            if real_idx == pred_idx:
                cf_dict[real_idx]['TP'] += cf_matrix[real_idx][pred_idx]
            else:
                cf_dict[real_idx]['FP'] += cf_matrix[pred_idx][real_idx]
                cf_dict[real_idx]['FN'] += cf_matrix[real_idx][pred_idx]

    sum_pc = 0.
    sum_rc = 0.

    for key in cf_dict.keys():
        cf_dict[key]['PC'] += cf_dict[key]['TP'] / (cf_dict[key]['TP'] + cf_dict[key]['FP'])
        cf_dict[key]['RC'] += cf_dict[key]['TP'] / (cf_dict[key]['TP'] + cf_dict[key]['FN'])

        sum_pc += cf_dict[key]['PC']
        sum_rc += cf_dict[key]['RC']

    avg_pc = sum_pc / tar_num
    avg_rc = sum_rc / tar_num

    print('\nPrecision: {} / Recall: {}'.format(avg_pc, avg_rc))

    return 2.0 / (1 / avg_pc + 1 / avg_rc)
