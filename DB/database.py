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
                            "`x`, `y`) "
                            "values (%s, %s, %s, %s, %s)", trackingInfoList)
    mot_db.commit()
