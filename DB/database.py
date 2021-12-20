import pymysql

mot_db = pymysql.connect(
    user='inc',
    passwd='1q2w3e4r!',
    host='127.0.0.1',
    db='inc_mot',
    charset='utf8mb4'
)

# Get DB Cursor
def getCursor():
    cursor = mot_db.cursor()
    return cursor

# Create New Video Group
# Return : New Group ID
def newVideoGroup():
    cursor = getCursor()
    cursor.execute("insert into `videoGroup` VALUES ()")
    mot_db.commit()
    return cursor.lastrowid

# Add New Video
# Return : New Video ID
def addNewVideo(fileName, groupID):
    data = [fileName, groupID]
    cursor = getCursor()

    cursor.execute("insert into `video`(`videoFileName`, `videoGroup_id`) VALUES (%s, %s)", data)
    mot_db.commit()
    return cursor.lastrowid

# Get Video ID by File Name
def getVideoId(videoFileName):
    data = [videoFileName]

    cursor = getCursor()
    cursor.execute("SELECT `id` from `video` where `videoFileName` = %s", data)
    return cursor.fetchall()

# Insert Video Frames
def insertVideoFrames(videoId, frameList):
    getCursor().executemany("insert into `frameinfo`(`frame_id`, `video_id`) VALUES (%s, {})".format(videoId),
                            frameList)
    mot_db.commit()

# Insert Tracking Infos
# [[ID, FrameID, VideoID, X, Y], [ID, FrameID, VideoID, X, Y]..]
def insertTrackingInfos(trackingInfoList):
    getCursor().executemany("insert into `trackinginfo`("
                            "`identifyID`, "
                            "`frameinfo_frame_id`, "
                            "`frameinfo_video_id`, "
                            "`position`) "
                            "values (%s, %s, %s, POINT(%s, %s))", trackingInfoList)
    mot_db.commit()

# Insert New Space Info
# [[0, 0], [1, 1], [2, 2]...]
def insertNewSpace(pointList):
    cursor = getCursor()
    pointCvt = []

    for pIdx in range(len(pointList)):
        print(pIdx, len(pointList) - 1)
        if pIdx != len(pointList) - 1:
            pointCvt.append("{} {},".format(pointList[pIdx][0], pointList[pIdx][1]))
        else:
            pointCvt.append("{} {},{} {}".format(pointList[pIdx][0], pointList[pIdx][1], pointList[0][0], pointList[0][1]))

    cursor.execute("insert into `spaceinfo`(`space`) "
                   "values (ST_GeomFromText('POLYGON(({}))'))".format(''.join(pointCvt)))
    mot_db.commit()
    return cursor.lastrowid

# Get Single Video MOT Data (From All Frame)
# Return ID & Frame ID & Position
def getMOTDatas(videoId):
    cursor = getCursor()
    cursor.execute("SELECT identifyID, frameinfo_frame_id, ST_AsText(position) "
                   "from `trackinginfo` "
                   "where `frameinfo_video_id` = {}".format(videoId))
    return cursor.fetchall()

# Get Single Video MOT Data (From Specific Frame)
# Return ID & Position
def getMOTDatabyFrame(videoId, frameId):
    cursor = getCursor()
    cursor.execute("SELECT identifyID, ST_AsText(position) "
                   "from `trackinginfo` "
                   "where `frameinfo_video_id` = {} and `frameinfo_frame_id` = {}".format(videoId, frameId))
    return cursor.fetchall()