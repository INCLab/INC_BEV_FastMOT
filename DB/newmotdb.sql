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
	frame_id INT PRIMARY KEY,
    video_id INT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES video(id)
);

CREATE TABLE IF NOT EXISTS `trackinginfo` (
	identifyID INT NOT NULL,
    frameinfo_frame_id INT NOT NULL,
    frameinfo_video_id INT NOT NULL,
    x DOUBLE NOT NULL,
    y DOUBLE NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(identifyID, frameinfo_frame_id),
    FOREIGN KEY(frameinfo_frame_id) REFERENCES frameinfo(frame_id),
    FOREIGN KEY(frameinfo_video_id) REFERENCES frameinfo(video_id)
);

CREATE TABLE IF NOT EXISTS `globalmapping` (
	globalID INT NOT NULL PRIMARY KEY,
    x DOUBLE NOT NULL,
    y DOUBLE NOT NULL,
    frameinfo_frame_id INT NOT NULL,
    videoGroup_id INT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (frameinfo_frame_id) REFERENCES frameinfo(frame_id),
	FOREIGN KEY (videoGroup_id) REFERENCES videoGroup(id)
);

CREATE TABLE IF NOT EXISTS `globalmapping_has_trackinginfo` (
	globalmapping_globalID INT NOT NULL,
    trackinginfo_identifyID INT NOT NULL,
    trackinginfo_frameinfo_frame_id INT NOT NULL,
    createAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updateAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (globalmapping_globalID, trackinginfo_identifyID, trackinginfo_frameinfo_frame_id),
    FOREIGN KEY (globalmapping_globalID) REFERENCES globalmapping(globalID),
    FOREIGN KEY (trackinginfo_identifyID) REFERENCES trackinginfo(identifyID),
    FOREIGN KEY (trackinginfo_frameinfo_frame_id) REFERENCES trackinginfo(frameinfo_frame_id)
);

