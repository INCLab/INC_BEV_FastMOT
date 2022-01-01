import datetime
import os
import zipfile
import tempfile

import pymysql
from flask import Flask, jsonify, request, send_file
import werkzeug.utils
from server_config import *
import DB.database as Database

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Jsonify 한글 정상 출력되도록 처리
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024  # 5000MB (5GB)까지 업로드 가능하도록 처리


# 비디오 파일 업로드
# Todo : 비디오 업로드 시 DB에 등록 과정 추가 (개별 비디오 및 Group)
# Todo : 비디오 업로드 시 DB에 폴더 이름도 함께 올라가도록 수정하기
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

            # 업로드 폴더 생성
            uploadFolder = VIDEOFILE_LOCATION + '/' + datetime.today().strftime("%Y%m%d%H%M%S") + '/'
            os.mkdir(uploadFolder)

            for video in videoFiles:
                # Mimetype에 Video가 없으면
                if "video" not in video.mimetype:
                    # 생성한 폴더 지움
                    os.remove(uploadFolder)

                    # 에러 반환
                    return jsonify(
                        code=500,
                        success=False,
                        msg="File '{}' is not Video File!".format(video.filename),
                        data=[]
                    )

                # Secure FileName 적용
                fname = werkzeug.utils.secure_filename(video.filename)

                # 파일 저장
                video.save(os.path.join(uploadFolder, fname))

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
                msg='SQL Error!\n' + sqle,
                data=[]
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

            if 'mapName' not in request.form:
                # 에러 반환
                return jsonify(
                    code=500,
                    success=False,
                    msg='Please Write Map Name (Alias)',
                    data=[]
                )

            # 업로드된 파일 가져옴
            map = request.files['mapFile']

            # 맵 별칭 가져옴
            mapName = request.form['mapName']

            # 업로드 폴더 생성
            uploadFolder = MAP_LOCATION + '/' + datetime.today().strftime("%Y%m%d%H%M%S") + '/'
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
                msg='SQL Error!\n' + sqle,
                data=[]
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

# Base ID와 같이
@app.route('/search/nearby/<int:groupId>/<int:baseId>', methods=['GET'])
def get_nearby_list_with_base(groupId, baseId):
    if request.method == 'GET':
        try:
            minFrame = None
            maxFrame = None
            args = request.args.to_dict()

            if 'minFrame' in args.keys():
                minFrame = args['minFrame']

            if 'maxFrame' in args.keys():
                maxFrame = args['maxFrame']

            nearbyList = Database.getNearbyIdinSpecificFrame(groupId, baseId, minFrame, maxFrame)

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
