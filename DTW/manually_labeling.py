import os
import cv2
import pyautogui as pag
# Todo: 특정 frame으로 이동하기
'''
    1. 첫번째 프레임을 보고 아이디 하나 선택 (아이디 선택할때 'i' 누르기)
       - 첫번째 프레임에서 아이디가 안보이는 경우 키보드 'n'을 눌러 다음 프레임으로 이동
    2. 아이디를 선택한 경우 다음에 보여지는 프레임은 해당 아이디가 사라진 프레임
       - 육안으로 해당 타겟에게 새로 부여된 아이디 찾아서 다시 1번 과정
       
    <keyboard>
    'i': 아이디 입력창 띄우기 (id)
    'n': 다음 프레임 (next)
    'p': 이전 프레임 (previous)
    'r': 맨 처음 프레임으로 (restart)
    's': 종료 (stop)

'''

# 읽어올 비디오 프레임 경로
vf_path = '../output/paper_17person/no_skip/1/frame/ch01'

# 해당 비디오에 대한 mot output txt 경로
txt_path = '../output/paper_17person/no_skip/1/ch01.txt'

###########################################################################################

# mot 정보 읽어오기
with open(txt_path, 'r') as txt_f:
    mot_data = txt_f.read()
    mot_data = mot_data.split('\n')

fid_dict = {}  # frame&ID dictionary
for line in mot_data:
    fid = line.split(' ')[:2]

    if fid[0] != '':
        if int(fid[0]) - 1 in fid_dict:
            fid_dict[int(fid[0]) - 1].append(int(fid[1]))  # frame을 key값으로 id 정보 넣기
        else:
            fid_dict[int(fid[0]) - 1] = [int(fid[1])]

frame_list = sorted(os.listdir(vf_path), key=lambda x: int(x[:-4]))

global selectedID
selectedID = None
id_start_fnum = -1

i = 0
while i < len(frame_list):
    # ID를 선택했고, 현재 프레임에서 등장하는 경우 다음 프레임으로 이동
    if selectedID != None and selectedID in fid_dict[i]:
        i += 1
        # Todo: i+1했을때 마지막 프레임인경우
        continue
    # Todo: ID 선택했지만 현재 프레임에서 등장하지 않는경우

    frame = frame_list[i]
    f_path = os.path.join(vf_path, frame)

    f = cv2.imread(f_path, -1)
    cv2.namedWindow(frame, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(frame, 1440, 810)
    cv2.moveWindow(frame, 80, 80)

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
        elif k == ord('s'):
            exit()
        elif k == ord('i'):
            while True:
                selectedID = pag.prompt(title='Target ID', text='타겟 ID를 입력하세요')
                try:
                    if selectedID == '':
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
    i += 1
    cv2.destroyAllWindows()
    if i == len(frame_list):
        pag.alert('끝!\n 처음 프레임으로 돌아갑니다.')
        i = 0


