from datetime import datetime
import os
import zipfile
import tempfile
import hashlib
import pymysql
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
            # 넘어온 새 Group 이름 정보가 없으면
            if 'groupName' not in request.form:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg="groupName Required",
                    data=[]
                )

            # 업로드 폴더 생성
            encode = hashlib.sha256(datetime.now().strftime("%Y%m%d%H%M%S").encode()).hexdigest()
            uploadFolder = VIDEOFILE_LOCATION + '/' + encode + '/'
            os.mkdir(uploadFolder)

            # DB에 그룹 생성
            videoGroupId = Database.newVideoGroup(request.form['groupName'], uploadFolder)

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
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': sqle}
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
                    uploadFolder = Database.getGroupFolderName(videoGroupId)
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

            for video in videoFiles:
                # Secure FileName 적용
                fname = werkzeug.utils.secure_filename(video.filename)

                # 파일 저장
                video.save(os.path.join(uploadFolder, fname))

                # DB에 비디오 정보 추가
                Database.addNewVideo("{}/{}".format(uploadFolder, fname), videoGroupId)

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
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': sqle}
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
            uploadFolder = MAP_LOCATION + '/' + encode + '/'
            os.mkdir(uploadFolder)

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
            Database.insertNewMap(mapName, uploadFolder + '/' + fname)

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
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error',
                data={'error': sqle}
            )


# Frame에 대한 BEV Mousepoint 정보 넣기
@app.route('/upload/map_point/frame/<int:videoId>')
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
                data={'error': sqle}
            )


# Map에 대한 BEV Mousepoint 정보 넣기
@app.route('/upload/point/map/<int:videoId>/<int:mapId>')
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
                data={'error': sqle}
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
            filePath = MOT_VIDEO_LOCATION + '/' + videoFolderName

            # 비디오 폴더에 있는 모든 파일 이름 가져오기
            fileList = os.listdir(filePath)

            # 임시 파일 생성
            with tempfile.TemporaryFile('w+') as tmpfile:
                # 임시 파일로 zip 파일 생성
                with zipfile.ZipFile(tmpfile, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 비디오를 압축 파일에 담기
                    for file in fileList:
                        zipf.write(filePath + '/' + file)

                # Client에 파일 전송
                return send_file(tmpfile, attachment_filename='MOTResultVideo_group{}.zip'.format(groupId),
                                 mimetype='application/zip',
                                 as_attachment=True)
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error!\n' + sqle,
                data=[]
            )


# 전체 지도 목록 가져오기
@app.route('/search/map', methods=['GET'])
def get_map_list():
    if request.method == 'GET':
        try:
            mapList = Database.getAllMapList()

            return jsonify(
                code=200,
                success=False,
                msg="success",
                data=mapList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error!\n' + sqle,
                data=[]
            )


# 전체 Video Group 목록 가져오기
@app.route('/search/videogroup', methods=['GET'])
def get_videogroup_list():
    if request.method == 'GET':
        try:
            groupList = Database.getAllVideoGroupList()

            return jsonify(
                code=200,
                success=False,
                msg="success",
                data=groupList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error!\n' + sqle,
                data=[]
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
                success=False,
                msg="success",
                data=nearbyList
            )
        # IO Error
        except IOError as ioe:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='IOError!\n' + ioe,
                data=[]
            )
        # pymysql Error
        except pymysql.err.Error as sqle:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='SQL Error!\n' + sqle,
                data=[]
            )


if __name__ == "__main__":
    app.run()
