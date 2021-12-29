import datetime
import os

from flask import Flask, jsonify, request
import werkzeug.utils
from server_config import *
#import DB.database as Database

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # Jsonify 한글 정상 출력되도록 처리
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024 # 5000MB (5GB)까지 업로드 가능하도록 처리

# 비디오 파일 업로드
# Todo : 비디오 업로드 시 DB에 등록 과정 추가 (개별 비디오 및 Group)
@app.route('/upload_videos', methods=['POST'])
def upload_videos():
    if request.method == 'POST':

        # 업로드된 파일이 없을 경우
        if 'videoFiles' not in request.files:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='Please Upload Files'
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
                    msg="File '{}' is not Video File!".format(video.filename)
                )

            # Secure FileName 적용
            fname = werkzeug.utils.secure_filename(video.filename)

            # 파일 저장
            video.save(os.path.join(uploadFolder, fname))

# 지도 업로드
# Todo : 지도 정보 Database에 업로드 가능하도록 하기
@app.route('/upload_map', methods=['POST'])
def upload_map():
    if request.method == 'POST':

        # 업로드된 파일이 없을 경우
        if 'mapFile' not in request.files:
            # 에러 반환
            return jsonify(
                code=500,
                success=False,
                msg='Please Upload Files'
            )

        # 업로드된 파일 가져옴
        map = request.files['mapFile']

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
                msg="File '{}' is not Image File!".format(map.filename)
            )

        # Secure FileName 적용
        fname = werkzeug.utils.secure_filename(map.filename)

        # 파일 저장
        map.save(os.path.join(uploadFolder, fname))


if __name__ == "__main__":
    app.run()
