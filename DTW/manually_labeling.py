import os
import cv2
import pyautogui as pag
#Todo: ID가 생성된 시점 frame으로 이동
'''
    1. 첫번째 프레임을 보고 아이디 하나 선택 (아이디 선택할때 'i' 누르기)
       - 첫번째 프레임에서 아이디가 안보이는 경우 키보드 'n'을 눌러 다음 프레임으로 이동
    2. 아이디를 선택한 경우 다음에 보여지는 프레임은 해당 아이디가 사라진 프레임
       - 육안으로 해당 타겟에게 새로 부여된 아이디 찾아서 다시 1번 과정
       
    <keyboard>
    'i': 아이디 입력창 띄우기 (id)
    'n': 다음 프레임 (next)
    'p': 이전 프레임 (previous)
    'r': 맨 처음 프레임으로 이동 (restart)
    'e': 맨 끝 프레임으로 이동 (end)
    'm': 특정 프레임으로 이동 (move)
    'f': 선택한 ID가 처음 생성된 frame으로 이동 (first generated)
    's': 종료 (stop)

'''

# 읽어올 비디오 프레임 경로
vf_path = '../output/paper_17person_byte/no_skip/1/frame/ch01'

# 해당 비디오에 대한 mot output txt 경로
txt_path = '../output/paper_17person_byte/no_skip/1/ch01.txt'

window_size = [1920, 1080]  # 너비, 높이  original size: 1920 1080 \\  4/3 size: 1440 810
window_loc = [900, 400]  # x, y

###########################################################################################

# mot 정보 읽어오기
with open(txt_path, 'r') as txt_f:
    mot_data = txt_f.read()
    mot_data = mot_data.split('\n')

id_list = []
fid_dict = {}  # frame&ID dictionary
for line in mot_data:
    fid = line.split(' ')[:2]

    if fid[0] != '':
        if int(fid[0]) - 1 in fid_dict:
            fid_dict[int(fid[0]) - 1].append(int(fid[1]))  # frame을 key값으로 id 정보 넣기
        else:
            fid_dict[int(fid[0]) - 1] = [int(fid[1])]
        id_list.append(int(fid[1]))

id_list = list(set(id_list))

frame_list = sorted(os.listdir(vf_path), key=lambda x: int(x[:-4]))

global selectedID, selectedFrame, selectedFID
selectedID = None
selectedFrame = None
selectedFID = None

id_start_fnum = -1

i = 0
while i < len(frame_list):
    # ID를 선택했고, 현재 프레임에서 등장하는 경우 다음 프레임으로 이동
    if selectedID != None and selectedID in fid_dict[i]:
        i += 1
        # 현재 마지막 프레임인 경우
        if i == len(frame_list):
            pag.alert('Target ID {}가 마지막 프레임까지 추적됐습니다.'.format(selectedID))
            selectedID = None
            id_start_fnum = -1
            i -= 1
        continue
    # ID 선택했지만 현재 프레임에서 등장하지 않는경우 다시 아이디 선택
    elif selectedID != None and selectedID not in fid_dict[i]:
        pag.alert('{}번 프레임부터 추적한 Target ID {}가 사라졌습니다.\n'
                  '새로운 아이디를 선택하세요'.format(id_start_fnum, selectedID))
        selectedID = None
        id_start_fnum = -1


    frame = frame_list[i]
    f_path = os.path.join(vf_path, frame)

    f = cv2.imread(f_path, -1)
    cv2.namedWindow(frame, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(frame, window_size[0], window_size[1])
    cv2.moveWindow(frame, window_loc[0], window_loc[1])

    while True:
        cv2.imshow(frame, f)

        k = cv2.waitKey(1)
        if k == ord('n'):
            break
        elif k == ord('p'):
            if i == 0:
                i = -1
            else:
                i -= 2
            break
        elif k == ord('r'):
            i = -1
            break
        elif k == ord('f'):
            while True:
                selectedFID = pag.prompt(title='Target ID', text='처음 생성된 프레임을 찾을 ID를 입력하세요')
                try:
                    if selectedFID == '' or selectedFID == None:
                        selectedFID = None
                        pag.alert('ID를 선택하지 않았습니다')
                        break
                    elif int(selectedFID) in id_list:
                        for key_frame in fid_dict.keys():
                            if int(selectedFID) in fid_dict[key_frame]:
                                i = key_frame - 1
                                break
                        pag.alert('Target ID {} 가 처음 생성된 프레임 {}로 이동합니다'.format(selectedID, i+1))
                        selectedFID = None
                        break
                    else:
                        pag.alert('해당 아이디는 이 영상에 등장하지 않습니다')
                        continue
                except:
                    pag.alert('해당 아이디는 이 영상에 등장하지 않습니다')
                    continue
            break
        elif k == ord('i'):
            while True:
                selectedID = pag.prompt(title='Target ID', text='타겟 ID를 입력하세요')
                try:
                    if selectedID == '' or selectedID == None:
                        selectedID = None
                        id_start_fnum = -1
                        pag.alert('Target ID를 선택하지 않았습니다')
                        break
                    elif int(selectedID) in fid_dict[i]:
                        selectedID = int(selectedID)
                        id_start_fnum = i
                        pag.alert('Target ID {} 선택됨\n시작 프레임 {}'.format(selectedID, id_start_fnum))
                        break
                    else:
                        pag.alert('해당 프레임에 없는 값입니다')
                        continue
                except:
                    pag.alert('해당 프레임에 없는 값입니다')
                    continue
            break
        elif k == ord('m'):
            while True:
                selectedFrame = pag.prompt(title='Frame number', text='이동할 프레임 번호를 입력하세요')
                try:
                    if selectedFrame == '' or selectedFrame == None:
                        selectedFrame = None
                        pag.alert('프레임을 선택하지 않았습니다')
                        break
                    elif int(selectedFrame) in fid_dict:
                        selectedFrame = int(selectedFrame)
                        pag.alert('{}번째 프레임으로 이동합니다'.format(selectedFrame))
                        break
                    else:
                        pag.alert('해당 프레임에 없는 값입니다')
                        continue
                except:
                    pag.alert('해당 프레임은 없는 값입니다')
                    continue
            break
        elif k == ord('e'):
            i = list(fid_dict.keys())[-1] - 1
            break
        elif k == ord('s'):
            exit()

    i += 1
    cv2.destroyAllWindows()
    if selectedFrame != None:
        i = selectedFrame
        selectedFrame = None
    if i == len(frame_list):
        pag.alert('끝!\n 처음 프레임으로 돌아갑니다.')
        i = 0


