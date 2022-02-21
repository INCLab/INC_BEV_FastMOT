import math
import sys
from copy import copy

import cv2
import os
import shutil

import numpy
import numpy as np
import mimetypes

from matplotlib import pyplot as plt
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
    temp_path = "../temp"

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
    drawfunc = {}
    for inputfile in list(map_point.keys()):
        ##############변경해야하는 부분#######################
        # 좌표값을 받아야함(하나씩)
        drawfunc[inputfile] = idx
        file = open(original_output_path / (inputfile + '.txt'), 'r')

        idxforfile[inputfile] = idx
        globals()['frame{}'.format(idx)], globals()['point{}'.format(idx)] = save_dict(file)
        idx += 1

    # #### Create BEV_Result txt files
    # Check the directory already exist
    if not os.path.isdir(os.path.join(original_output_path, 'bev_result')):
        os.mkdir(os.path.join(original_output_path, 'bev_result'))

    # 지도 읽어와서 Grid 그리기
    map = draw_grid(cv2.imread(str(map_path), -1))
    for i in list(map_point.keys()):
        globals()['BEV_Point{}'.format(idxforfile[i])] = dict()

    # 파일마다 Loop
    for filename in list(map_point.keys()):
        print('\n[BEV] Start {}..'.format(filename))
        # ID 간 매핑 테이블
        mapping_table = {}

        # 최근 트래킹 정보 테이블
        recent_trackings = {}

        # 지도 - 영상 좌표 간 Mapping
        pm = PixelMapper(quad_coords_list[filename]["pixel"], quad_coords_list[filename]["lonlat"])
        # 파일 기록을 위해 파일 열기
        with open(os.path.join(original_output_path, 'bev_result', 'BEV_{}.txt'.format(filename)), 'w') as f:
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
                    # 프레임 포인트 정보들 가져오고, 순서 뒤집기
                    # 뒤집는 이유 -> 맨 뒤에 있는 포인트가 최근 생성된 포인트들이기 때문
                    pointData = list(reversed(globals()['point{}'.format(idxforfile[filename])].get(str(frames))))

                    # 파일의 특정 프레임에 대한 좌표 정보들 가져오기
                    # 0 : ID
                    # 1 : X
                    # 2 : Y
                    for positiondata in pointData:
                        # X/Y 좌표를 Tuple에 담기
                        uv = (positiondata[1], positiondata[2])

                        # 영상 좌표를 지도 좌표로 변환
                        lonlat = list(pm.pixel_to_lonlat(uv))

                        # 현재 아이디를 담을 변수
                        current_id = positiondata[0]

                        # 현재 ID가 매핑 테이블에 이미 존재한다면
                        if current_id in mapping_table.keys():
                            # 매핑 테이블 ID와 현재 ID가 다르다면
                            if mapping_table[current_id] != current_id:
                                # ID를 매핑 테이블 ID 정보로 사용
                                current_id = mapping_table[current_id]
                        # 존재하지 않으면 (새로운 ID)
                        else:
                            # 이전 Tracking 정보에서 가장 가까운 ID 찾기
                            nearest_id, dist = find_nearest_id(pointData, recent_trackings, frames,
                                                               (int(lonlat[0][0]), int(lonlat[0][1])))

                            # 발견하지 못했다면
                            if nearest_id == -1:
                                # 현재 ID에 대한 매핑 ID로 본인 기록
                                mapping_table[current_id] = current_id

                                # 가장 최근에 저장된 추적 정보 제거

                            # 발견했다면
                            else:
                                # Point Data에서 Nearest ID와 동일한 아이디 찾기(같은 frame)
                                sameid_filter = list(filter(lambda x: x[0] == nearest_id, pointData))

                                # 같은 아이디가 발견되었다면
                                if len(sameid_filter) > 0:
                                    # 현재 ID에 대한 매핑 ID로 본인 기록
                                    mapping_table[current_id] = current_id

                                    print('[{}] {} nearest {}, but same detected, ignore.'.format(frames, current_id,
                                                                                                  nearest_id))
                                else:
                                    # 현재 ID에 대한 매핑 ID로 발견한 ID 기록
                                    mapping_table[current_id] = nearest_id

                                    print('[{}] {} mapping to {} dist: {}'.format(frames, current_id, nearest_id, dist))

                                    # 현재 ID 업데이트
                                    current_id = nearest_id

                        # 최근 추적 정보 저장
                        recent_trackings[current_id] = [frames, (int(lonlat[0][0]), int(lonlat[0][1]))]
                        # 마지막으로 저장된 추적정보 아이디 저장

                        # 각 파일에 Text 작성
                        f.write("{} {} {} {}\n".format(
                            frames,  # 프레임 번호
                            current_id,  # ID
                            int(lonlat[0][0]),  # 매핑 X
                            int(lonlat[0][1])))  # 매핑 Y

                        # 색상
                        color = getcolor(abs(current_id))

                        if drawfunc[filename] == 0:
                            # 원 찍기
                            cv2.circle(img_file,
                                       (int(lonlat[0][0]), int(lonlat[0][1])),
                                       10,
                                       color,
                                       -1)
                        elif drawfunc[filename] == 1:
                            cv2.fillPoly(img_file,
                                         [get_triangle_points((int(lonlat[0][0]), int(lonlat[0][1])))],
                                         color,
                                         cv2.LINE_AA)
                        elif drawfunc[filename] == 2:
                            draw_points = get_rectangle_points((int(lonlat[0][0]), int(lonlat[0][1])))
                            cv2.rectangle(img_file,
                                          draw_points[0],
                                          draw_points[1],
                                          color,
                                          -1)
                        elif drawfunc[filename] == 3:
                            cv2.fillPoly(img_file,
                                         [get_reverse_triangle_points((int(lonlat[0][0]), int(lonlat[0][1])))],
                                         color,
                                         cv2.LINE_AA)

                        cv2.putText(img_file,
                                    str(current_id),
                                    (int(lonlat[0][0]) - 5, int(lonlat[0][1])),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (255, 255, 255))

                # 프레임 저장
                src = os.path.join(output_path, str(frames) + '.jpg')
                cv2.imwrite(src, img_file)


# 매핑 프레임 Threshold
mapping_frame_threshold = 300

# 매핑 거리 Threshold
mapping_dist_threshold = 200

graph_dict = {}

# 가장 가까운 아이디 찾기
def find_nearest_id(pointData: tuple, recent_trackings: dict, currentframe: int, position: tuple):
    # 가장 가까운 거리
    near_distance = sys.maxsize

    # 가장 가까운 거리를 가지는 ID
    near_id = -1

    # 모든 최근 추적 정보에 대해 Loop
    for key in recent_trackings.keys():

        # 현재 프레임 내가 아니고, 지도를 벗어나지 않으면서 Frame Threshold 내에 있던 추적 결과인 경우
        if currentframe != recent_trackings[key][0] and \
                (recent_trackings[key][1][0] >= 0 and recent_trackings[key][1][1] >= 0) and \
                (currentframe - recent_trackings[key][0]) <= mapping_frame_threshold:

            # 거리 측정
            dist = distance.euclidean(position, recent_trackings[key][1])

            # 거리 Threshold 안쪽이고, 마지막으로 가장 가까운 거리보다 더 가깝다면
            if dist <= mapping_dist_threshold and dist < near_distance:
                # 가까운 거리 정보와 ID 변경
                near_id = key
                near_distance = dist
            # else:
            #     # 거리가 threshold를 넘어가고,
            #     # 현재 프레임에서 최근 추적 정보에 담긴 아이디가 없는 경우
            #     # 그 아이디 정보는 최근 추적 정보에서 지우고 다른 아이디와 매핑되지 않도록 하는것이 좋다
            #     # (보수적으로 매핑하기 위해)
            #     # Todo: 이 방법이 적합한지 확인과정 필요
            #     if list(filter(lambda x: x[0] == key, pointData))

    if near_id != -1:
        graph_dict['{}-{}'.format(currentframe, near_id)] = near_distance

    return near_id


# 두 점 사이의 중간 점 찾기
def get_midpoint(p1, p2):
    return int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2)


def get_triangle_points(midpoint):
    return np.array([[midpoint[0], midpoint[1] + 10],
                     [midpoint[0] - 10, midpoint[1] - 10],
                     [midpoint[0] + 10, midpoint[1] - 10]])


def get_rectangle_points(midpoint):
    return [(midpoint[0] - 10, midpoint[1] + 10), (midpoint[0] + 10, midpoint[1] - 10)]


def get_reverse_triangle_points(midpoint):
    return np.array([[midpoint[0], midpoint[1] - 10],
                     [midpoint[0] - 10, midpoint[1] + 10],
                     [midpoint[0] + 10, midpoint[1] + 10]])


def draw_grid(image: numpy.ndarray, row_lines=1, column_lines=1):
    """ Draw Grid in Image

    :param image: Image (numpy.ndarray)
    :param row_lines Number of Row Lines
    :param column_lines Number of Column Lines
    :return: Image with Grid
    """
    height, width, channel = image.shape

    last_height = 0
    for row in range(row_lines):
        cv2.line(image,
                 (0, last_height + int(height / (row_lines + 1))),
                 (width, last_height + int(height / (row_lines + 1))),
                 (0, 255, 0),
                 3)
        last_height = int(height / (row_lines + 1))

    last_width = 0
    for row in range(column_lines):
        cv2.line(image,
                 (last_width + int(width / (column_lines + 1)), 0),
                 (last_width + int(width / (column_lines + 1)), height),
                 (0, 255, 0),
                 3)
        last_width = int(height / (column_lines + 1))

    return image

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

if __name__ == "__main__":
    print(distance.euclidean([1274, 773], [1146, 940]))
    start('../input/edu_test1/', '../output/edu_test1/', '../input/edu_map.png')
