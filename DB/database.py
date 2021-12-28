import pymysql

mot_db = pymysql.connect(
    user='inc',
    passwd='1q2w3e4r!',
    host='192.9.85.204',
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
    return cursor.fetchall()[0][0]

# Insert Video Frames
def insertVideoFrames(videoId, frameList):
    getCursor().executemany("insert into `frameinfo`(`video_id`, `frame_id`)  VALUES ({}, %s)".format(videoId),
                            frameList)
    mot_db.commit()

# Insert Tracking Infos
# videoID (Int) : Single Video ID
# trackingInfoList (List) : [[FrameID, ID, X, Y], [FrameID, ID, X, Y]..]
def insertTrackingInfos(videoID, trackingInfoList):
    getCursor().executemany("insert into `trackinginfo`("
                            "`frameinfo_video_id`, "
                            "`frameinfo_frame_id`, "
                            "`identifyID`, "
                            "`position`) "
                            "values ({}, %s, %s, POINT(%s, %s))".format(videoID), trackingInfoList)
    mot_db.commit()

# Insert Correction Tracking Infos
# videoID (Int) : Single Video ID
# trackingInfoList (List) : [[FrameID, ID, X, Y], [FrameID, ID, X, Y]..]
def insertCorrectionTrackingInfos(videoID, trackingInfoList):
    getCursor().executemany("insert into `trackinginfo_correction`("
                            "`frameinfo_video_id`, "
                            "`frameinfo_frame_id`, "
                            "`identifyID`, "
                            "`position`) "
                            "values ({}, %s, %s, POINT(%s, %s))", videoID, trackingInfoList)
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
# Return [[FrameID, ID, [X, Y]], ...]
def getMOTDatas(videoId):
    cursor = getCursor()
    print("SELECT frameinfo_frame_id, identifyID, ST_AsText(position) "
                   "from `trackinginfo` "
                   "where `frameinfo_video_id` = {}".format(videoId))
    cursor.execute("SELECT frameinfo_frame_id, identifyID, ST_AsText(position) "
                   "from `trackinginfo` "
                   "where `frameinfo_video_id` = {}".format(videoId))

    datas = list(cursor.fetchall())
    for dataIdx in range(len(datas)):
        data = list(datas[dataIdx])
        data[2] = list(map(int, data[2].replace('POINT(', '').replace(')', '').split(' ')))
        datas[dataIdx] = data[0]
        datas.append(data[1])

    return datas


# Get Single Video MOT Data (From Specific Frame)
# videoID : Single Video ID
# frameID : Single Video Frame ID
# Return [[ID, [X, Y]], [ID, [X, Y]]]
def getMOTDatabyFrame(videoId, frameId):
    cursor = getCursor()
    cursor.execute("SELECT identifyID, ST_AsText(position) "
                   "from `trackinginfo` "
                   "where `frameinfo_video_id` = {} and `frameinfo_frame_id` = {}".format(videoId, frameId))

    datas = list(cursor.fetchall())
    for dataIdx in range(len(datas)):
        data = list(datas[dataIdx])
        data[1] = list(map(int, data[1].replace('POINT(', '').replace(')', '').split(' ')))
        datas[dataIdx] = data

    return datas

# Insert Global Tracking Info
# groupID (Int) : Video Group ID (globaltrackinginfo's videoGroup_id)
# mappingInfo (List) : [[Video ID, FrameID, GlobalID, TrackingID], [Video ID, FrameID, GlobalID, TrackingID], ...]
# trackingInfo (List) : [[FrameID, Global ID, X, Y], [FrameID, Global ID, X, Y]..]
def insertGlobalTrackingInfo(groupID, mappingInfo, trackingInfo):
    getCursor().executemany("insert into `globaltrackinginfo`("
                            "`videoGroup_id`, "
                            "`frame_id`, "
                            "`globalID`, "
                            "`position`) "
                            "values ({}, %s, %s, POINT(%s, %s))".format(groupID), trackingInfo)

    getCursor().executemany("insert into `trackinginfo_has_globaltrackinginfo`("
                            "`videoGroup_id`, "
                            "`localVideo_id`, "
                            "`frame_id`, "
                            "`globalID`, "
                            "`trackingID`) "
                            "values ({}, %s, %s, %s, %s)".format(groupID), mappingInfo)
    mot_db.commit()

# Get Global Tracking Data (From All Frame)
# groupID (Int) : Video Group ID
# Return [[FrameID, ID, [X, Y]], ...]
def getGlobalTrackingDatas(groupID):
    cursor = getCursor()
    cursor.execute("SELECT frame_id, globalID, ST_AsText(position) "
                   "from `globaltrackinginfo` "
                   "where `videoGroup_id` = {}".format(groupID))

    datas = list(cursor.fetchall())
    for dataIdx in range(len(datas)):
        data = list(datas[dataIdx])
        data[2] = list(map(int, data[2].replace('POINT(', '').replace(')', '').split(' ')))
        datas[dataIdx] = data

    return datas


# Get Global Tracking Data (From Specific Frame)
# groupID : Video Group ID
# frameID : Video Frame ID
# Return [[ID, [X, Y]], [ID, [X, Y]]]
def getGlobalTrackingDatabyFrame(groupID, frameId):
    cursor = getCursor()
    cursor.execute("SELECT globalID, ST_AsText(position) "
                   "from `globaltrackinginfo` "
                   "where `videoGroup_id` = {} and `frame_id` = {}".format(groupID, frameId))

    datas = list(cursor.fetchall())
    for dataIdx in range(len(datas)):
        data = list(datas[dataIdx])
        data[1] = list(map(int, data[1].replace('POINT(', '').replace(')', '').split(' ')))
        datas[dataIdx] = data

    return datas

# Insert New BEV Data
# groupID (Int) : Video Group ID
# mappingInfo (List) : [[FrameID, GlobalID, BEV ID], [FrameID, GlobalID, BEV ID], ...]
# bevInfo (List) : [[FrameID, BEV ID, X, Y], [FrameID, BEV ID, X, Y]]
def insertBEVData(groupID, mappingInfo, bevInfo):
    getCursor().executemany("insert into `BEV`("
                            "`videoGroup_id`, "
                            "`frame_id`, "
                            "`bevID`, "
                            "`position`) "
                            "values ({}, %s, %s, POINT(%s, %s))".format(groupID), bevInfo)

    getCursor().executemany("insert into `BEV_has_globaltrackinginfo`("
                            "`videoGroup_id`, "
                            "`frame_id`, "
                            "`globalID`, "
                            "`bevID`) "
                            "values ({}, %s, %s, %s)".format(groupID), mappingInfo)
    mot_db.commit()

# Get BEV Data by Group ID
# groupID (Int) : Video Group ID
def getBEVData(groupID):
    cursor = getCursor()
    cursor.execute("SELECT frame_id, bevID, ST_AsText(position) "
                   "from `BEV` "
                   "where `videoGroup_id` = {}".format(groupID))

    datas = list(cursor.fetchall())
    for dataIdx in range(len(datas)):
        data = list(datas[dataIdx])
        data[2] = list(map(int, data[1].replace('POINT(', '').replace(')', '').split(' ')))
        datas[dataIdx] = data

    return datas

# Get Video Group ID by Video ID
# videoID : Single Video ID
def getGroupIDbyVideoID(videoID):
    cursor = getCursor()
    cursor.execute("SELECT videoGroup_id from video where id = %s", videoID)
    return cursor.fetchall()[0][0]