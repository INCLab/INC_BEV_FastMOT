# Video에서 Frame 추출하기 (신규 Framework인 FastMOT와의 호환용)

import cv2
import sys
import os

print('Video Frame Extracting.....')

if len(sys.argv) != 2:
    print("Invalid Parameter")
    sys.exit()

videos_dir = sys.argv[1]


# 폴더 내 모든 파일에 대해 Loop
for f in os.listdir(videos_dir):
    # OpenCV로 Video File Open 
    videofile = cv2.VideoCapture(videos_dir + '/' + f)

    frameNum = 0

    # Video File이 열렸으면
    while videofile.isOpened():
        # Frame Load 
        ret, frame = videofile.read()
        
        if not ret:
            print('Invaild Frame')
            sys.exit()

        # Frame 저장 - 기존 형태와 동일하게 저장
        # ./output/frame/ch01/00001.jpg
        if not os.path.exists('./output/frame/' + os.path.splitext(f)[0]):
            os.makedirs('./output/frame/' + os.path.splitext(f)[0])

        imgfilename = './output/frame/' + os.path.splitext(f)[0] + '/' + str(frameNum).zfill(5) + '.jpg'

        cv2.imwrite(imgfilename, frame)
        print('Saved to ' + imgfilename)

    # Release
    videofile.release()
