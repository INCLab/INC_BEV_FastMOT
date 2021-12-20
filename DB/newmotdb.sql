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

CREATE TABLE IF NOT EXISTS `globaltrackinginfo` (
    globalID INT NOT NULL,
    videoGroup_id INT NOT NULL,
    position POINT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (globalID, videoGroup_id),
    FOREIGN KEY (videoGroup_id) REFERENCES videoGroup(id)
);

CREATE TABLE IF NOT EXISTS `trackinginfo_has_globaltrackinginfo` (
    videoGroup_id INT NOT NULL,
    globalID INT NOT NULL,
    video_id INT NOT NULL,
    frame_id INT NOT NULL,
    video_identifyID INT NOT NULL,
    PRIMARY KEY (videoGroup_id, globalID, video_id, frame_id, video_identifyID),
    FOREIGN KEY (videoGroup_id, globalID) REFERENCES globaltrackinginfo(videoGroup_id, globalID),
    FOREIGN KEY (video_id, frame_id, video_identifyID) REFERENCES trackinginfo(frameinfo_video_id, frameinfo_frame_id, identifyID)
);

CREATE TABLE IF NOT EXISTS `spaceinfo` (
    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    space POLYGON NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
