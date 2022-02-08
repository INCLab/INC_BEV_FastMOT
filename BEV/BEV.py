import math
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
    for i in list(map_point.keys()):
        globals()['BEV_Point{}'.format(idxforfile[i])] = dict()

    # Global Mapping Table
    globalmapping = {}

    # Last Global ID
    curid = 1000

    # Recent Tracking Infomation
    recent_trackings = {}

    total_txt = open(os.path.join(original_output_path, 'bev_result', 'BEV_Total.txt', 'w'))

    # 말 그대로 프레임 몇 번쨰인지
    for frames in range(1, int(globals()['frame{}'.format(0)])):
        current_frame_ids = []

        # 지도 이미지 복사
        tempmap = copy(map)

        # 파일명
        for i in list(map_point.keys()):

            # 현재 영상에 대한 Global Mapping 정보가 없다면
            if i not in globalmapping.keys():
                # 생성
                globalmapping[i] = {}

            # 영상 - 이미지간 픽셀 매핑
            pm = PixelMapper(quad_coords_list[i]["pixel"], quad_coords_list[i]["lonlat"])

            # 지금 영상에 지금 프레임에 대한 포인트 정보가 존재한다면
            if globals()['point{}'.format(idxforfile[i])].get(str(frames)) is not None:
                # Point 정보 가져오기
                # ID, X, Y
                for label in globals()['point{}'.format(idxforfile[i])].get(str(frames)):
                    uv = (label[1], label[2])
                    lonlat = list(pm.pixel_to_lonlat(uv))

                    # 아이디 변수 (기본은 MOT랑 동일)
                    id = label[0]

                    # 위치 (우선 현재 위치로)
                    pos = int(lonlat[0][0]), int(lonlat[0][1])

                    # 현재 MOT ID가 Global Mapping Table에 없다면
                    if label[0] not in globalmapping[i].keys():
                        # 새 아이디 찾기
                        newid = find_nearest_id(recent_trackings, frames, (int(lonlat[0][0]), int(lonlat[0][1])))

                        # 못 찾았으면
                        if newid == -1:
                            # 새 Global ID 부여
                            id = curid
                            print('[{}/{}] Added New Global ID ({}, {})'.format(i, frames, label[0], id))
                            curid += 1
                        # 찾았으면
                        else:
                            # 기존 아이디로 매핑
                            id = newid
                            print('[{}/{}] Mapping to Exists ID ({}, {})'.format(i, frames, label[0], id))

                        # Global Mapping 테이블 업데이트
                        globalmapping[i][label[0]] = id

                    # Mapping Table에 존재하면
                    else:
                        # Global Mapping 테이블 정보 활용
                        id = globalmapping[i][id]

                    # 해당 ID의 마지막 트래킹 정보를 동일한 프레임에서 찾은거라면
                    if id in recent_trackings.keys() and recent_trackings[id][0] == frames:
                        # 중간 점을 찾아서 해당 위치를 새로운 좌표로 설정
                        pos = get_midpoint(recent_trackings[id][1], pos)

                    # 최근 트래킹 정보 업데이트
                    recent_trackings[id] = [frames, pos]

                    # 그릴 아이디 추가
                    if id not in current_frame_ids:
                        current_frame_ids.append(id)

        # 추가된 아이디들 그리기
        for id in current_frame_ids:
            # 파일 내용 작성
            total_txt.write("{} {} {} {}"
                            .format(frames, id, recent_trackings[id][1][0], recent_trackings[id][1][1])
                            + '\n')

            # 이미지에 포인트 찍기
            color = getcolor(abs(id))
            cv2.circle(tempmap, recent_trackings[id][1], 10, color, -1)
            cv2.putText(tempmap,
                        str(id),
                        recent_trackings[id][1],
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255))

        # 이미지 저장
        src = os.path.join(output_path, str(frames) + '.jpg')
        cv2.imwrite(src, tempmap)

    # 파일 닫기
    total_txt.close()


# 매핑 거리 Threshold
mapping_dist_threshold = 50


# 가장 가까운 아이디 찾기
def find_nearest_id(recent_trackings: dict, currentframe: int, position: tuple):
    # 가장 가까운 거리
    near_distance = sys.maxsize

    # 가장 가까운 거리를 가지는 ID
    near_id = -1

    # 모든 최근 추적 정보에 대해 Loop
    for key in recent_trackings.keys():
        # 해당 추적 정보가 현재 프레임 내에 있는 경우
        if currentframe == recent_trackings[key][0]:
            # 거리 측정
            dist = distance.euclidean(position, recent_trackings[key][1])
            # Threshold 안쪽이고, 마지막으로 가장 가까운 거리보다 더 가깝다면
            if dist <= mapping_dist_threshold and dist < near_distance:
                # 가까운 거리 정보와 ID 변경
                near_id = key
                near_distance = dist

    return near_id


# 두 점 사이의 중간 점 찾기
def get_midpoint(p1, p2):
    return int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2)


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
