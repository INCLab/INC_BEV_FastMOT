import pymysql

mot_db = pymysql.connect(
    user='',
    passwd='',
    host='localhost',
    db='inc_mot',
    charset='utf8mb4'
)

# Get DB Cursor
def getCursor():
    cursor = mot_db.cursor(pymysql.cursors.DictCursor)
    return cursor

# Insert New Video
def insertVideoList(videoList):
    getCursor().executemany("insert into `video`(`video_id`) videoFileName (%s)", videoList)
    insertVideoGroup(videoList)
    mot_db.commit()

# Insert New Video Group
def insertVideoGroup(videoList):
    # First Video First Insert
    getCursor().execute("insert into `videoGroup`(`video_id`) values (%s)", videoList.pop(0))

    # Get New ID
    groupId = getCursor().lastrowid

    # Insert Other Video to Same Group
    getCursor().executemany("insert into `videoGroup`(`id`, `video_id`) values (%s, %s)", groupId, videoList)
    mot_db.commit()

# Get Video ID by File Name
def getVideoId(videoFileName):
    getCursor().execute("SELECT `id` from `video` where `videoFileName` = (%s)", videoFileName)
    return getCursor().fetchall()

# Insert Video Frame
def insertVideoFrame(videoId, frameList):
    getCursor().executemany("insert into `frameinfo`(`frame_id`, `video_id`) values (%s, %s)", videoId, frameList)
    mot_db.commit()

# Insert Tracking Info
# [[ID, FrameID, VideoID, X, Y], [ID, FrameID, VideoID, X, Y]..]
def insertTrackingInfo(trackingInfoList):
    getCursor().executemany("insert into `trackinginfo`("
                            "`identifyID`, "
                            "`frameinfo_frame_id`, "
                            "`frameinfo_video_id`, "
                            "`x`, `y`) "
                            "values (%s, %s, %s, %s, %s)", trackingInfoList)
    mot_db.commit()
