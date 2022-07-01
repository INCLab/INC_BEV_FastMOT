def confusion_matrix(gt_list, total_list, test_person_num, cam_list):

    '''
        1. index가 가장빠른 cam을 real(confusion matrix)로 선택(real_cam)
        2. 각각의 샘플에 i에 대해 gt list[i]에 포함된 matching ids list에 대해서 target1부터 차례대로 순회
        3. 해당 matching ids 중 real_cam의 id(rc_id) 선택 후 predict_maching list에서 rc_id를 포함하는 리스트 선택
        4. 만일 real_cam에서 해당 rc_id가 tracking이 안된경우 다음 index cam에 대한 rc_id 선택 후  predict_maching list에서 rc_id를 포함하는 리스트 선택
        5. 해당 리스트에서 각각의 cam에 대응 하는 아이디가 어느 target을 나타내고있는지 each cam target list에 표시
        6. 예를들어 총 target이 3명인 경우에 대해 target1_matching_list에서 cam2의 target3이 포함되어있다면
            cam2_target_list = [ sample1[ tar1[0, 0, 1], tar2[...], tar3[...] ],
                                sample2[...],
                                ...
                                ]
    '''

    '''
        total_list[0]: vector
        total_list[1]: unit
        total_list[2]: scalar
    '''
    for feature_idx, predict_matched_list in enumerate(total_list):

        # confusion matrix를 위한 카메라별 리스트를 딕셔너리형태로 생성(real_cam 제외)
        cam_dict = {}
        cam_list = sorted(cam_list)

        # 각 카메라 별로 0으로 초기화된 샘플별 타겟 매칭정보 리스트 생성
        for cam_idx in cam_list[1:]:
            cam_dict[cam_idx] = [[[0 for _ in range(0, test_person_num)]  # 타겟 수만큼 0으로 초기화
                                  for _ in range(0, test_person_num)]  # 타겟 수만큼 초기화된 리스트 생성
                                 for _ in range(0, len(gt_list))]  # 샘플수 만큼 리스트 생성

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

        # 카메라별 매칭 정보 리스트를 통해 confusion matrix 생성
        print(cam_dict)
        break
