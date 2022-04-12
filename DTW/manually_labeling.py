import os
import cv2
import pyautogui as pag
'''
    1. 첫번째 프레임을 보고 아이디 하나 선택
       - 첫번째 프레임에서 아이디가 안보이는 경우 키보드 'n'을 눌러 다음 프레임으로 이동
    2. 아이디를 선택한 경우 다음에 보여지는 프레임은 해당 아이디가 사라진 프레임
       - 육안으로 해당 타겟에게 새로 부여된 아이디 찾아서 다시 1번 과정
       
    <keyboard>
    'n': 다음 프레임 (next)
    'p': 이전 프레임 (previous)
    'r': 맨 처음 프레임으로 (restart)
    's': 종료 (stop)

'''

# 읽어올 비디오 프레임 경로
vf_path = '../output/paper_17person/no_skip/1/frame/ch01'

# 해당 비디오에 대한 mot output txt 경로
txt_path = '../output/paper_17person/no_skip/1/ch01.txt'

frame_list = sorted(os.listdir(vf_path), key=lambda x: int(x[:-4]))
# ID = pag.prompt(title='Target ID', text='타겟 ID를 입력하세요')
# print(ID)
# pag.alert('요호!')

i = 0
while i < len(frame_list):
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
    i += 1
    cv2.destroyAllWindows()


