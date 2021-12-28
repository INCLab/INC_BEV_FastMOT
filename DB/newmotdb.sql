DROP DATABASE `inc_mot`;
CREATE DATABASE IF NOT EXISTS `inc_mot` default character set utf8mb4;
use `inc_mot`;

CREATE TABLE IF NOT EXISTS `videoGroup` (
	id INT PRIMARY KEY auto_increment,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `video` (
	id INT PRIMARY KEY auto_increment,
    videoFileName varchar(512) not null unique,
    videoGroup_id INT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (videoGroup_id) REFERENCES videoGroup(id)
);

CREATE TABLE IF NOT EXISTS `frameinfo` (
    video_id INT,
	frame_id INT,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, frame_id),
    FOREIGN KEY (video_id) REFERENCES video(id)
);

CREATE TABLE IF NOT EXISTS `trackinginfo` (
	identifyID INT NOT NULL,
	frameinfo_video_id INT NOT NULL,
    frameinfo_frame_id INT NOT NULL,
    position POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(identifyID, frameinfo_video_id, frameinfo_frame_id),
    FOREIGN KEY (frameinfo_video_id, frameinfo_frame_id) REFERENCES frameinfo(video_id, frame_id)
);

CREATE TABLE IF NOT EXISTS `trackinginfo_correction` (
	identifyID INT NOT NULL,
	frameinfo_video_id INT NOT NULL,
    frameinfo_frame_id INT NOT NULL,
    position POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(identifyID, frameinfo_video_id, frameinfo_frame_id),
    FOREIGN KEY (frameinfo_video_id, frameinfo_frame_id) REFERENCES frameinfo(video_id, frame_id)
);

CREATE TABLE IF NOT EXISTS `BEV` (
    videoGroup_id INT NOT NULL,
    video_id INT NOT NULL,
    frame_id INT NOT NULL,
    bevID INT NOT NULL,
    position POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (videoGroup_id, video_id, frame_id, bevID),
    FOREIGN KEY (videoGroup_id) REFERENCES videoGroup(id),
    FOREIGN KEY (video_id) REFERENCES video(id)
);

CREATE TABLE IF NOT EXISTS `globaltrackinginfo` (
    videoGroup_id INT NOT NULL,
    frame_id INT NOT NULL,
    globalID INT NOT NULL,
    position POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (videoGroup_id, frame_id, globalID),
    FOREIGN KEY (videoGroup_id) REFERENCES videoGroup(id)
);


CREATE TABLE IF NOT EXISTS `spaceinfo` (
    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    space POLYGON NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `mousepoint_frame` (
    video_id INT NOT NULL PRIMARY,
    p1 POINT NOT NULL,
    p2 POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    FOREIGN KEY (video_id) REFERENCES video(id)
)

CREATE TABLE IF NOT EXISTS `mousepoint_map` (
    video_id INT NOT NULL,
    map_name varchar(512) NOT NULL,
    p1 POINT NOT NULL,
    p2 POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (video_id, map_name)
    FOREIGN KEY (video_id) REFERENCES video(id)
)

-- TrackingInfo - BEV Mapping
CREATE TABLE IF NOT EXISTS `trackinginfo_has_BEV` (
    videoGroup_id INT NOT NULL,
    localVideo_id INT NOT NULL,
    frame_id INT NOT NULL,
    bevID INT NOT NULL,
	trackingID INT NOT NULL,
    PRIMARY KEY (videoGroup_id, localVideo_id, frame_id, bevID, trackingID),
    FOREIGN KEY (localVideo_id, frame_id, trackingID) REFERENCES trackinginfo_correction(frameinfo_video_id, frameinfo_frame_id, identifyID),
    FOREIGN KEY (videoGroup_id, localVideo_id, frame_id, bevID) REFERENCES BEV(videoGroup_id, video_id, frame_id, bevID)
);

-- BEV - GlobalTrackingInfo Mapping
CREATE TABLE IF NOT EXISTS `BEV_has_globaltrackinginfo` (
    videoGroup_id INT NOT NULL,
    localVideo_id INT NOT NULL,
    frame_id INT NOT NULL,
	globalID INT NOT NULL,
    bevID INT NOT NULL,
    PRIMARY KEY (videoGroup_id, frame_id, globalID, bevID),
	FOREIGN KEY (videoGroup_id, frame_id, globalID) REFERENCES globaltrackinginfo(videoGroup_id, frame_id, globalID),
    FOREIGN KEY (videoGroup_id, localVideo_id, frame_id, bevID) REFERENCES BEV(videoGroup_id, video_id, frame_id, bevID)
);