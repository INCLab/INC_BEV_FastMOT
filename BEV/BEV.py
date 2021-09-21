import cv2
import os
import sys
import shutil

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

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

    num = 0
    for filename in os.listdir(input_path):
        name, ext = os.path.splitext(filename)
        if ext == '.mp4':
            num += 1

    f = open(os.path.join(temp_path, 'points.txt'), 'r')
    data = f.read()
    data = data.split('\n')

    point = []
    frame_point = []
    map_point = []

    for i in data:
        point.append(i.split(' '))

    for i in point:
        if i[0] == 'map':
            map_point.append(i)
        elif i[0] == 'frame':
            frame_point.append(i)

    if not(len(map_point) % 4 == 0 and len(frame_point) % 4 == 0):
        print('Point Error')
        sys.exit()

    quad_coords_list = []

    for i in range(num):
        quad_coords = {
            "pixel": np.array([
                [frame_point[i*4][1]  ,   frame_point[i*4][2]],  # Third lampost top right
                [frame_point[i*4+1][1], frame_point[i*4+1][2]],  # Corner of white rumble strip top left
                [frame_point[i*4+2][1], frame_point[i*4+2][2]],  # Corner of rectangular road marking bottom left
                [frame_point[i*4+3][1], frame_point[i*4+3][2]]  # Corner of dashed line bottom right
            ]),
            "lonlat": np.array([
                [map_point[i*4][1]  ,   map_point[i*4][2]],  # Third lampost top right
                [map_point[i*4+1][1], map_point[i*4+1][2]],  # Corner of white rumble strip top left
                [map_point[i*4+2][1], map_point[i*4+2][2]],  # Corner of rectangular road marking bottom left
                [map_point[i*4+3][1], map_point[i*4+3][2]]  # Corner of dashed line bottom right
            ])
        }
        quad_coords_list.append(quad_coords)

    print(quad_coords_list)
    #PixelMapper로 값 전달


    fileidx = 0
    for inputfile in os.listdir(input_path):
        name, ext = os.path.splitext(inputfile)

        # 확장자가 .mp4인 경우
        if ext == ".mp4":
            # Output Folder에 저장된 MOT Result Text 읽기
            print('read', original_output_path / (name + '.txt'))

            ##############변경해야하는 부분#######################
            # 좌표값을 받아야함(하나씩)
            file = open(original_output_path / (name + '.txt'), 'r')
            globals()['frame{}'.format(fileidx)], globals()['point{}'.format(fileidx)] = save_dict(file)
            fileidx += 1

    map = cv2.imread(str(map_path), -1)

    for i in range(num):
        globals()['BEV_Point{}'.format(i)] = dict()

    for frames in range(1, int(globals()['frame{}'.format(0)])):
        for i in range(num):
            pm = PixelMapper(quad_coords_list[i]["pixel"], quad_coords_list[i]["lonlat"])
            if globals()['point{}'.format(i)].get(str(frames)) != None:
                for label in globals()['point{}'.format(i)].get(str(frames)) :
                    uv = (label[1], label[2])
                    lonlat = list(pm.pixel_to_lonlat(uv))
                    li = [label[0], int(lonlat[0][0]), int(lonlat[0][1])]
                    if frames in globals()['BEV_Point{}'.format(i)]:
                        line = globals()['BEV_Point{}'.format(i)].get(frames)
                        line.append(li)
                    else:
                        globals()['BEV_Point{}'.format(i)][frames] = [li]

                    color = getcolor(abs(label[0]))
                    cv2.circle(map, (int(lonlat[0][0]), int(lonlat[0][1])), 3, color, -1)

            src = os.path.join(output_path, str(frames) + '.jpg')
            cv2.imwrite(src, map)

    ## HeatMap ##

    # df = pd.DataFrame(index=range(0, 10), columns=range(0, 13))
    df = [[0 for col in range(13)] for row in range(10)]

    # df = df.fillna(0)

    print(type(map.shape))
    print(map.shape[1])

    for frames in range(1, int(globals()['frame{}'.format(0)])):

        for i in range(num):

            if globals()['BEV_Point{}'.format(i)].get(frames) is not None:

                for label in globals()['BEV_Point{}'.format(i)].get(frames):
                    if label[2] < 0 or label[1] < 0 or label[1] > map.shape[1] or label[2] > map.shape[0] :

                        continue

                    x = round(int(label[2]) / map.shape[0] * 9)
                    y = round(int(label[1]) / map.shape[1] * 12)
                    df[x][y] += 1

    print(df)

    sns.heatmap(df, linewidths=0.1, linecolor="black")

    plt.savefig(heatmap_path)

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

    #실제 공간을 도면으로 바꿈
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
    #도면 공간을 실제 공간으로 바꿈
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
def save_lonlat_frame(point, pm,frame_num ,input_dir, output_dir):
    map = cv2.imread(input_dir, -1)

    #1541
    for frames in range(1, frame_num): #object ID마다 색깔바꿔서 점찍기
        if point.get(str(frames)) != None:
            for label in point.get(str(frames)) :
                uv = (label[1], label[2])
                lonlat = list(pm.pixel_to_lonlat(uv))
                color = getcolor(abs(label[0]))
                cv2.circle(map, (int(lonlat[0][0]), int(lonlat[0][1])), 3, color, -1)

        src = os.path.join(output_dir, str(frames)+'.jpg')
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
