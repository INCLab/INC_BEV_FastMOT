import sys
from copy import copy

import cv2
import os
import shutil
import numpy as np
import mimetypes
from scipy.spatial import distance

##############################################################################

'''
pixel : 실제 공간
lonloat : 도면 공간
실제 mapping 되는 곳에 좌표를 입력 @@@.py 사용
오른쪽 위, 왼쪽 위, 왼쪽 아래, 오른쪽 아래 순서
'''


def start(input_path, output_path, map_path):
    heatmap_path = os.path.join(output_path, 'heatmap.png')
    original_output_path = output_path
    output_path = os.path.join(output_path, 'map_frame')
    temp_path = "./temp"

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        shutil.rmtree(output_path)
        os.makedirs(output_path)

    filelist = list(filter(
        lambda filename: mimetypes.guess_type(filename)[0] is not None and mimetypes.guess_type(filename)[0].find(
            'video') is not -1, os.listdir(input_path)))

    f = open(os.path.join(temp_path, 'points.txt'), 'r')
    data = f.read()
    data = data.split('\n')

    point = []
    frame_point = {}
    map_point = {}

    for i in data:
        point.append(i.split(' '))

    crtfile = None
    for i in point:
        if crtfile is not None and (i[0].startswith("map") or i[0].startswith("frame")):
            if i[0] == 'map':
                map_point[crtfile].append([i[1], i[2]])
            elif i[0] == 'frame':
                frame_point[crtfile].append([i[1], i[2]])
        else:
            if not i[0] == '' and not i[0].isspace():
                crtfile = i[0]
                map_point[crtfile] = []
                frame_point[crtfile] = []

    # if not(len(map_point) % 4 == 0 and len(frame_point) % 4 == 0):
    #     print('Point Error')
    #     sys.exit()

    quad_coords_list = {}

    for i in list(map_point.keys()):
        quad_coords = {
            "pixel": np.array([
                [frame_point[i][0][0], frame_point[i][0][1]],  # Third lampost top right
                [frame_point[i][1][0], frame_point[i][1][1]],  # Corner of white rumble strip top left
                [frame_point[i][2][0], frame_point[i][2][1]],  # Corner of rectangular road marking bottom left
                [frame_point[i][3][0], frame_point[i][3][1]]  # Corner of dashed line bottom right
            ]),
            "lonlat": np.array([
                [map_point[i][0][0], map_point[i][0][1]],  # Third lampost top right
                [map_point[i][1][0], map_point[i][1][1]],  # Corner of white rumble strip top left
                [map_point[i][2][0], map_point[i][2][1]],  # Corner of rectangular road marking bottom left
                [map_point[i][3][0], map_point[i][3][1]]  # Corner of dashed line bottom right
            ])
        }
        quad_coords_list[i] = quad_coords

    # PixelMapper로 값 전달

    idxforfile = {}
    idx = 0
    for inputfile in list(map_point.keys()):
        ##############변경해야하는 부분#######################
        # 좌표값을 받아야함(하나씩)
        file = open(original_output_path / (inputfile + '.txt'), 'r')
        idxforfile[inputfile] = idx
        globals()['frame{}'.format(idx)], globals()['point{}'.format(idx)] = save_dict(file)
        idx += 1

    # #### Create BEV_Result txt files
    # Check the directory already exist
    if not os.path.isdir(os.path.join(original_output_path, 'bev_result')):
        os.mkdir(os.path.join(original_output_path, 'bev_result'))

    # 지도 읽기
    map = cv2.imread(str(map_path), -1)
    # for i in list(map_point.keys()):
    #     globals()['BEV_Point{}'.format(idxforfile[i])] = dict()

    mapping_frame_threshold = 50
    mapping_threshold = 10

    # 파일마다 Loop
    for filename in list(map_point.keys()):
        # 지도 - 영상 좌표 간 Mapping
        pm = PixelMapper(quad_coords_list[filename]["pixel"], quad_coords_list[filename]["lonlat"])
        # 파일 기록을 위해 파일 열기
        with open(os.path.join(original_output_path, 'bev_result', 'BEV_{}.txt'.format(filename)), 'w') as f:
            last_list = {}
            id_mapping_list = {}

            # 프레임 수만큼 Loop - 'frame' Dict에는 영상 별 프레임 갯수가 들어가 있음
            # 0을 쓰는 이유는 첫 영상과 프레임 수를 동일하게 맞추기 위해서로 추정
            for frames in range(1, int(globals()['frame{}'.format(0)])):
                # 이미 해당 프레임에 대해 저장된 이미지가 있다면
                if os.path.isfile(os.path.join(output_path, str(frames) + '.jpg')):
                    # 해당 이미지에 그림을 그리도록 함
                    img_file = cv2.imread(os.path.join(output_path, str(frames) + '.jpg'), -1)
                # 그렇지 않다면
                else:
                    # 지도 자체에 그림 그리기
                    img_file = copy(map)

                # Point에 프레임 정보가 있으면
                # 'Point' Dict에는 좌표가 들어가 있음 (Key -> File Idx)
                if globals()['point{}'.format(idxforfile[filename])].get(str(frames)) is not None:
                    # 파일의 특정 프레임에 대한 좌표 정보들 가져오기
                    # 0 : ID
                    # 1 : X
                    # 2 : Y
                    for positiondata in globals()['point{}'.format(idxforfile[filename])].get(str(frames)):
                        # X/Y 좌표를 Tuple에 담기
                        uv = (positiondata[1], positiondata[2])

                        # 영상 좌표를 지도 좌표로 변환
                        lonlat = list(pm.pixel_to_lonlat(uv))

                        # ID 저장용 변수 값 체크
                        # 현재 ID가 이전 리스트에 있다면
                        if positiondata[0] in id_mapping_list.keys():
                            # 지금 ID를 해당 ID로
                            newid = id_mapping_list[positiondata[0]]
                        # 없다면
                        else:
                            # 현재 ID를 새 ID로
                            id_mapping_list[positiondata[0]] = positiondata[0]
                            newid = positiondata[0]


                        # ID가 사라진 경우
                        if newid not in last_list.keys():
                            # 최소 거리
                            sdistance = sys.maxsize
                            # 최소 거리 키
                            skey = positiondata[0]

                            # Loop
                            for key in last_list.keys():
                                # 현재 Frame에서 나타나지 않았고, Threshold 내에서 사라진 ID라면
                                if frames != last_list[key][0] and frames - last_list[key][0] <= mapping_frame_threshold:
                                    # 현재 사용자와 거리 비교
                                    dis = distance.euclidean(last_list[key][1], (int(lonlat[0][0]), int(lonlat[0][1])))
                                    # 거리 Threshold 안쪽이고, 이전 가장 짧은 거리보다 더 짧다면
                                    if dis < mapping_threshold and dis < sdistance:
                                        # 최소 거리 및 키 업데이트
                                        sdistance = dis
                                        skey = key

                            # 최종 ID 저장
                            print(positiondata[0], 'changed to', skey, 'distance', sdistance)
                            last_list[skey] = [frames, (int(lonlat[0][0]), int(lonlat[0][1]))]
                            id_mapping_list[newid] = skey
                            newid = skey
                        else:
                            print(newid, 'id already exists')
                            # 최종 프레임, (X, Y)
                            last_list[newid] = [frames, (int(lonlat[0][0]), int(lonlat[0][1]))]

                        # 각 파일에 Text 작성
                        f.write("{} {} {} {}\n".format(
                            frames,  # 프레임 번호
                            newid,  # ID
                            int(lonlat[0][0]),  # 매핑 X
                            int(lonlat[0][1])))  # 매핑 Y

                        # 색상
                        color = getcolor(abs(newid))

                        # 원 찍기
                        cv2.circle(img_file, (int(lonlat[0][0]), int(lonlat[0][1])), 10, color, -1)
                        cv2.putText(img_file,
                                    str(newid),
                                    (int(lonlat[0][0]), int(lonlat[0][1])),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (255, 255, 255))

                # 프레임 저장
                src = os.path.join(output_path, str(frames) + '.jpg')
                cv2.imwrite(src, img_file)

    # # 말 그대로 프레임 몇 번쨰인지
    # for frames in range(1, int(globals()['frame{}'.format(0)])):
    #     tempmap = copy(map)
    #     # 파일명
    #     for i in list(map_point.keys()):
    #         pm = PixelMapper(quad_coords_list[i]["pixel"], quad_coords_list[i]["lonlat"])
    #         if globals()['point{}'.format(idxforfile[i])].get(str(frames)) is not None:
    #             # ID랑 X/Y
    #             for label in globals()['point{}'.format(idxforfile[i])].get(str(frames)):
    #                 uv = (label[1], label[2])
    #                 lonlat = list(pm.pixel_to_lonlat(uv))
    #                 li = [label[0], int(lonlat[0][0]), int(lonlat[0][1])]
    #                 if frames in globals()['BEV_Point{}'.format(idxforfile[i])]:
    #                     line = globals()['BEV_Point{}'.format(idxforfile[i])].get(frames)
    #                     line.append(li)
    #                 else:
    #                     globals()['BEV_Point{}'.format(idxforfile[i])][frames] = [li]
    #
    #                 tlabel = tuple(label)
    #                 if tlabel not in pointset:
    #                     # 각 파일에 Text 작성
    #                     txtfilelist[i].write("{} {} {} {}"
    #                                          .format(frames, label[0], int(lonlat[0][0]), int(lonlat[0][1]))
    #                                          + '\n')
    #                     color = getcolor(abs(label[0]))
    #                     cv2.circle(tempmap, (int(lonlat[0][0]), int(lonlat[0][1])), 10, color, -1)
    #                     pointset.add(tlabel)
    #
    #     src = os.path.join(output_path, str(frames) + '.jpg')
    #     cv2.imwrite(src, tempmap)

    # # 파일 닫기
    # for filekey in txtfilelist.keys():
    #     txtfilelist[filekey].close()


# ## HeatMap ##
#
# # df = pd.DataFrame(index=range(0, 10), columns=range(0, 13))
# df = [[0 for col in range(13)] for row in range(10)]
#
# # df = df.fillna(0)
#
# for frames in range(1, int(globals()['frame{}'.format(0)])):
#
#     for i in list(map_point.keys()):
#
#         if globals()['BEV_Point{}'.format(idxforfile[i])].get(frames) is not None:
#
#             for label in globals()['BEV_Point{}'.format(idxforfile[i])].get(frames):
#                 if label[2] < 0 or label[1] < 0 or label[1] > map.shape[1] or label[2] > map.shape[0]:
#                     continue
#
#                 x = round(int(label[2]) / map.shape[0] * 9)
#                 y = round(int(label[1]) / map.shape[1] * 12)
#                 df[x][y] += 1
#
# print(df)
#
# sns.heatmap(df, linewidths=0.1, linecolor="black")
#
# plt.savefig(heatmap_path)

'''
id 라벨값에 맞춰 색깔을 지정하는 function
'''


def getcolor(idx):
    idx = idx * 3
    return (37 * idx) % 255, (17 * idx) % 255, (29 * idx) % 255


'''
실제공간과 도면을 mapping해주는 class
'''


class PixelMapper(object):
    """
    Create an object for converting pixels to geographic coordinates,
    using four points with known locations which form a quadrilteral in both planes
    Parameters
    ----------
    pixel_array : (4,2) shape numpy array
        The (x,y) pixel coordinates corresponding to the top left, top right, bottom right, bottom left
        pixels of the known region
    lonlat_array : (4,2) shape numpy array
        The (lon, lat) coordinates corresponding to the top left, top right, bottom right, bottom left
        pixels of the known region
    """

    def __init__(self, pixel_array, lonlat_array):
        assert pixel_array.shape == (4, 2), "Need (4,2) input array"
        assert lonlat_array.shape == (4, 2), "Need (4,2) input array"
        self.M = cv2.getPerspectiveTransform(np.float32(pixel_array), np.float32(lonlat_array))
        self.invM = cv2.getPerspectiveTransform(np.float32(lonlat_array), np.float32(pixel_array))

    # 실제 공간을 도면으로 바꿈
    def pixel_to_lonlat(self, pixel):
        """
        Convert a set of pixel coordinates to lon-lat coordinates
        Parameters
        ----------
        pixel : (N,2) numpy array or (x,y) tuple
            The (x,y) pixel coordinates to be converted
        Returns
        -------
        (N,2) numpy array
            The corresponding (lon, lat) coordinates
        """
        if type(pixel) != np.ndarray:
            pixel = np.array(pixel).reshape(1, 2)
        assert pixel.shape[1] == 2, "Need (N,2) input array"
        pixel = np.concatenate([pixel, np.ones((pixel.shape[0], 1))], axis=1)
        lonlat = np.dot(self.M, pixel.T)

        return (lonlat[:2, :] / lonlat[2, :]).T

    # 도면 공간을 실제 공간으로 바꿈
    def lonlat_to_pixel(self, lonlat):
        """
        Convert a set of lon-lat coordinates to pixel coordinates
        Parameters
        ----------
        lonlat : (N,2) numpy array or (x,y) tuple
            The (lon,lat) coordinates to be converted
        Returns
        -------
        (N,2) numpy array
            The corresponding (x, y) pixel coordinates
        """
        if type(lonlat) != np.ndarray:
            lonlat = np.array(lonlat).reshape(1, 2)
        assert lonlat.shape[1] == 2, "Need (N,2) input array"
        lonlat = np.concatenate([lonlat, np.ones((lonlat.shape[0], 1))], axis=1)
        pixel = np.dot(self.invM, lonlat.T)

        return (pixel[:2, :] / pixel[2, :]).T


"""
lonlat에 frame을 한번에 저장하는 function
"""


def save_lonlat_frame(point, pm, frame_num, input_dir, output_dir):
    map = cv2.imread(input_dir, -1)

    # 1541
    for frames in range(1, frame_num):  # object ID마다 색깔바꿔서 점찍기
        if point.get(str(frames)) != None:
            for label in point.get(str(frames)):
                uv = (label[1], label[2])
                lonlat = list(pm.pixel_to_lonlat(uv))
                color = getcolor(abs(label[0]))
                cv2.circle(map, (int(lonlat[0][0]), int(lonlat[0][1])), 3, color, -1)

        src = os.path.join(output_dir, str(frames) + '.jpg')
        cv2.imwrite(src, map)


def save_dict(file):
    ##################################################
    frame = 0
    point = dict()
    while True:
        line = file.readline()

        if not line:
            break

        info = line[:-1].split(" ")

        frame = info[0]

        if info[0] in point:
            line = point.get(info[0])
            line.append(list(map(int, info[1:])))
        else:
            point[info[0]] = [list(map(int, info[1:]))]

    file.close()

    return frame, point
    ###########################################################################
