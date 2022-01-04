from datetime import datetime
import os
import zipfile
import tempfile
import hashlib

import cv2
import pymysql
import json

import fastmot
from fastmot.utils import ConfigDecoder, Profiler
from types import SimpleNamespace

from flask import Flask, jsonify, request, send_file
import werkzeug.utils

from server_config import *
import DB.database as Database

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Jsonify 한글 정상 출력되도록 처리
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024  # 5000MB (5GB)까지 업로드 가능하도록 처리


# 비디오 파일 업로드
@app.route('/create/videogroup', methods=['POST'])
def create_videogroup():
    if request.method == 'POST':
        try:
            # Request 데이터가 JSON이 아니면
            if not request.is_json:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Body needs data in the form of JSON',
                    data=[]
                )

            # Json 받아오기
            jsonReq = request.get_json()

            print(jsonReq)

            # 넘어온 새 Group 이름 정보가 없으면
            if 'groupName' not in jsonReq:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg="groupName Required",
                    data=[]
                )

            # 업로드 폴더 생성
            encode = hashlib.sha256(datetime.now().strftime("%Y%m%d%H%M%S").encode()).hexdigest()
            uploadFolder = encode
            os.mkdir(FILE_UPLOAD_LOCATION + '/' + uploadFolder)
            os.mkdir(RESULT_LOCATION + '/' +  uploadFolder)

            # DB에 그룹 생성
            videoGroupId = Database.newVideoGroup(jsonReq['groupName'], uploadFolder)

            # 새 Video Group ID와 성공 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data={'videoGroup': videoGroupId}
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# 비디오 파일 업로드
@app.route('/upload/videos', methods=['POST'])
def upload_videos():
    if request.method == 'POST':
        try:
            # 업로드된 파일이 없을 경우
            if 'videoFiles' not in request.files:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Please Upload Files',
                    data=[]
                )

            # 업로드된 파일 목록 가져옴
            videoFiles = request.files.getlist('videoFiles')

            # 가져온 파일들의 Mimetype 확인
            for video in videoFiles:
                # Mimetype에 Video가 없으면
                if "video" not in video.mimetype:
                    # 에러 반환
                    return jsonify(
                        code=500,
                        success=False,
                        msg="File '{}' is not Video File!".format(video.filename),
                        data=[]
                    )

            # 넘어온 Video Group 정보가 있으면
            if 'videoGroup' in request.form:
                # 해당 Group이 존재하는 그룹이면
                if not Database.getGroupFolderName(request.form['videoGroup']) is None:
                    # 해당 Video Group을 정보로 사용
                    videoGroupId = request.form['videoGroup']
                    uploadFolder = FILE_UPLOAD_LOCATION + '/video/' + Database.getGroupFolderName(videoGroupId) + '/'
                    print(uploadFolder)
                else:
                    # 에러 반환
                    return jsonify(
                        code=500,
                        success=False,
                        msg="VideoGroup {} is Not Exist!".format(request.form['videoGroup']),
                        data=[]
                    )
            # 넘어온 정보가 없으면
            else:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg="VideoGroup Required",
                    data=[]
                )

            # 폴더 없으면
            if not os.path.exists(uploadFolder):
                # 만들기
                os.makedirs(uploadFolder)

            for video in videoFiles:
                # Secure FileName 적용
                fname = werkzeug.utils.secure_filename(video.filename)

                # 파일 저장
                video.save(os.path.join(uploadFolder, fname))

                # DB에 비디오 정보 추가
                Database.addNewVideo("{}".format(fname), videoGroupId)

            # 성공 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data={}
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# 지도 업로드
@app.route('/upload/map', methods=['POST'])
def upload_map():
    if request.method == 'POST':
        try:
            # 업로드된 파일이 없을 경우
            if 'mapFile' not in request.files:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Please Upload Files',
                    data=[]
                )
            else:
                # 있으면 해당 파일을 가져옴
                map = request.files['mapFile']

            # 맵 이름이 지정되지 않은 경우
            if 'mapName' not in request.form:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Please Write Map Name (Alias)',
                    data=[]
                )
            else:
                # 있으면 해당 이름을 가져옴
                mapName = request.form['mapName']

            # 업로드 폴더 생성
            encode = hashlib.sha256(datetime.now().strftime("%Y%m%d%H%M%S").encode()).hexdigest()
            uploadFolder = FILE_UPLOAD_LOCATION + '/map/' + encode + '/'

            # 폴더 없으면
            if not os.path.exists(uploadFolder):
                # 만들기
                os.makedirs(uploadFolder)

            # Mimetype에 image가 없으면
            if "image" not in map.mimetype:
                # 생성한 폴더 지움
                os.remove(uploadFolder)

                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg="File '{}' is not Image File!".format(map.filename),
                    data=[]
                )

            # Secure FileName 적용
            fname = werkzeug.utils.secure_filename(map.filename)

            # 파일 저장
            map.save(os.path.join(uploadFolder, fname))

            # DB에 맵 별명 및 경로 저장
            Database.insertNewMap(mapName, uploadFolder + fname)

            # 성공 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data=[]
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# Video에 대한 BEV Mousepoint 정보 넣기
@app.route('/upload/point/video/<int:videoId>', methods=['POST'])
def insert_mousepoint_frame(videoId):
    if request.method == 'POST':
        try:
            # Request 데이터가 JSON이 아니면
            if not request.is_json:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Body needs data in the form of JSON',
                    data=[]
                )

            # Json 받아오기
            jsonReq = request.get_json()

            # 포인트 정보가 하나라도 없으면
            if not 'lefttop' in jsonReq or not 'righttop' in jsonReq or not 'leftbottom' in jsonReq or not 'rightbottom' in jsonReq:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Incomplete Point Infomation',
                    data=[]
                )

            # 포인트 Tuple 목록 작성해서 DB에 쓰기
            lefttop = (jsonReq['lefttop']['x'], jsonReq['lefttop']['y'])
            righttop = (jsonReq['righttop']['x'], jsonReq['righttop']['y'])
            leftbottom = (jsonReq['leftbottom']['x'], jsonReq['leftbottom']['y'])
            rightbottom = (jsonReq['rightbottom']['x'], jsonReq['rightbottom']['y'])
            Database.insertFrameMousePoint(videoId, (lefttop, righttop, leftbottom, rightbottom))

            # 성공 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# Map에 대한 BEV Mousepoint 정보 넣기
@app.route('/upload/point/map/<int:videoId>/<int:mapId>', methods=['POST'])
def insert_mousepoint_map(videoId, mapId):
    if request.method == 'POST':
        try:
            # Request 데이터가 JSON이 아니면
            if not request.is_json:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Body needs data in the form of JSON',
                    data=[]
                )

            # Json 받아오기
            jsonReq = request.get_json()

            # 포인트 정보가 하나라도 없으면
            if not 'lefttop' in jsonReq or not 'righttop' in jsonReq or not 'leftbottom' in jsonReq or not 'rightbottom' in jsonReq:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Incomplete Point Infomation',
                    data=[]
                )

            # 포인트 Tuple 목록 작성해서 DB에 쓰기
            lefttop = (jsonReq['lefttop']['x'], jsonReq['lefttop']['y'])
            righttop = (jsonReq['righttop']['x'], jsonReq['righttop']['y'])
            leftbottom = (jsonReq['leftbottom']['x'], jsonReq['leftbottom']['y'])
            rightbottom = (jsonReq['rightbottom']['x'], jsonReq['rightbottom']['y'])
            Database.insertMapMousePoint(videoId, mapId, (lefttop, righttop, leftbottom, rightbottom))

            # 성공 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )

# MOT 결과 비디오 (그룹 전체) 다운로드
@app.route('/download/mot/group/<int:groupId>', methods=['GET'])
def download_mot_group(groupId):
    if request.method == 'GET':
        try:
            # 데이터베이스에서 해당하는 group ID의 폴더 이름 받기
            videoFolderName = Database.getGroupFolderName(groupId)

            # 해당하는 폴더 이름을 못 받거나 비어있는 Str이 반환되면
            if videoFolderName is None or videoFolderName == "":
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg="Group ID {} is Not Found!".format(groupId),
                    data=[]
                )

            # 비디오가 있는 폴더 경로
            filePath = RESULT_LOCATION + '/' + videoFolderName + '/video'

            # 비디오 폴더에 있는 모든 파일 이름 가져오기
            fileList = os.listdir(filePath)

            with zipfile.ZipFile('MOTResultVideo_group{}.zip'.format(groupId), 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 비디오를 압축 파일에 담기
                for file in fileList:
                    zipf.write(filePath + '/' + file)

            # Client에 파일 전송
            return send_file('MOTResultVideo_group{}.zip'.format(groupId), attachment_filename='MOTResultVideo_group{}.zip'.format(groupId),
                             mimetype='application/zip',
                             as_attachment=True)
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# MOT 결과 요청
@app.route('/mot/<int:groupId>', methods=['GET'])
def run_mot_group(groupId):
    if request.method == 'GET':
        try:
            # 비디오 정보 목록 가져옴
            videoList = Database.getGroupVideoList(groupId)

            # 목록이 비었으면
            if len(videoList) == 0:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Empty Group',
                    data=[]
                )

            # Group 저장 폴더명 가져오기
            groupFolder = Database.getGroupFolderName(groupId)

            # 필요한 폴더 경로 String + 필요한 폴더 생성
            videoInputFolder = FILE_UPLOAD_LOCATION + '/video/' + groupFolder + '/'
            videoOutputFolder = RESULT_LOCATION + '/' + groupFolder + '/video'
            frameOutputFolder = RESULT_LOCATION + '/' + groupFolder + '/video/frames'

            # 폴더 없으면 폴더 생성
            if not os.path.exists(videoOutputFolder):
                os.makedirs(videoOutputFolder)

            if not os.path.exists(frameOutputFolder):
                os.makedirs(frameOutputFolder)

            # load config file
            with open(FASTMOT_CFG_FILE) as cfg_file:
                config = json.load(cfg_file, cls=ConfigDecoder, object_hook=lambda d: SimpleNamespace(**d))

                # For BEV param
                # tracking_info: [[VideoName1, VideoID_1, tracking_list_1],[VideoName2, VideoID_2, tracking_list_2], ...]
                tracking_info = []

                # 평균 FPS 목록
                avg_fps_list = {}

                # Skip된 목록 (이미 MOT 자료 존재)
                already_list = []

                # 모든 File 읽기 위해 Loop
                for videoFile in videoList:
                    # 이미 MOT가 돌아간 경우가 아니라면
                    if not Database.isAlreadyMOT(videoFile['id']):
                        # 이름과 확장자 분리
                        name, ext = os.path.splitext(videoFile['videoFileName'])

                        # FastMOT 실행
                        stream = fastmot.VideoIO(config.resize_to,
                                                 videoInputFolder + videoFile['videoFileName'],
                                                 videoOutputFolder + "/mot_{}".format(videoFile['videoFileName']),
                                                 **vars(config.stream_cfg))
                        mot = fastmot.MOT(config.resize_to, **vars(config.mot_cfg), draw=True)
                        mot.reset(stream.cap_dt)

                        # Frame Number List
                        frameList = []

                        # Each Frame Tracking Data
                        # [[VideoID, FrameID, ID, X, Y], [VideoID, FrameID, ID, X, Y]..]
                        trackingList = []

                        framecount = 0

                        stream.start_capture()

                        try:
                            if not os.path.exists(frameOutputFolder + '/' + videoFile['videoFileName']):
                                os.makedirs(frameOutputFolder + '/' + videoFile['videoFileName'])

                            with Profiler('app') as prof:
                                while True:
                                    frame = stream.read()
                                    if frame is None:
                                        break

                                    mot.step(frame)

                                    # New Frame Info
                                    frameList.append([mot.frame_count])

                                    for track in mot.visible_tracks():
                                        tl = track.tlbr[:2] / config.resize_to * stream.resolution
                                        br = track.tlbr[2:] / config.resize_to * stream.resolution
                                        w, h = br - tl + 1

                                        # New Tracking Info
                                        trackingList.append([
                                            mot.frame_count,
                                            track.trk_id,
                                            int(tl[0] + w / 2),
                                            int((tl[1] + h) - 10)
                                        ])

                                    cv2.imwrite("{}/{}.jpg".format(frameOutputFolder + '/' + videoFile['videoFileName'], framecount), frame)
                                    framecount += 1
                                    stream.write(frame)
                        finally:
                            try:
                                stream.release()
                                # Add Frame List
                                if len(frameList) > 0:
                                    Database.insertVideoFrames(videoFile['id'], frameList)

                                # Add Tracking Info
                                if len(trackingList) > 0:
                                    Database.insertTrackingInfos(videoFile['id'], trackingList)

                                    # For BEV param
                                    tracking_info.append([name, videoFile['id'], trackingList])
                            except Exception as e:
                                # 에러 반환
                                return jsonify(
                                    code=500,
                                    success=False,
                                    msg='MOT Error',
                                    data={'error': e}
                                )
                            except pymysql.err.Error as sqle:
                                # 에러 반환
                                return jsonify(
                                    code=500,
                                    success=False,
                                    msg='SQL Error',
                                    data={'error': str(sqle)}
                                )

                            avg_fps = round(mot.frame_count / prof.duration)
                            avg_fps_list[videoFile['videoFileName']] = avg_fps
                    else:
                        already_list.append(videoFile['id'])

            # 완료 반환
            return jsonify(
                code=200,
                success=True,
                msg='success',
                data={'avg_fps': avg_fps_list,
                      'already': already_list}
            )
        # IO Error
        except IOError as ioe:
            print(ioe)
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# 전체 지도 목록 가져오기
@app.route('/search/map', methods=['GET'])
def get_map_list():
    if request.method == 'GET':
        try:
            mapList = Database.getAllMapList()

            return jsonify(
                code=200,
                success=True,
                msg="success",
                data=mapList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# 전체 Video Group 목록 가져오기
@app.route('/search/videogroup', methods=['GET'])
def get_videogroup_list():
    if request.method == 'GET':
        try:
            groupList = Database.getAllVideoGroupList()

            return jsonify(
                code=200,
                success=True,
                msg="success",
                data=groupList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


# Base ID와 일정 거리 내에 존재하는 사용자 구하기
# ex. /search/nearby/1/12?minFrame=10&maxFrame=500&distance=10
@app.route('/search/nearby/<int:groupId>/<int:baseId>', methods=['GET'])
def get_nearby_list_with_base(groupId, baseId):
    if request.method == 'GET':
        try:
            minFrame = None
            maxFrame = None
            distance = None
            args = request.args.to_dict()

            if 'minFrame' in args.keys():
                minFrame = args['minFrame']

            if 'maxFrame' in args.keys():
                maxFrame = args['maxFrame']

            if 'distance' in args.keys():
                distance = args['distance']
            else:
                distance = 10

            nearbyList = Database.getNearbyIdinSpecificFrame(groupId, baseId, distance, minFrame, maxFrame)

            return jsonify(
                code=200,
                success=True,
                msg="success",
                data=nearbyList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IO Error',
                data={'error': str(ioe)}
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': str(sqle)}
            )


if __name__ == "__main__":
    app.run()
