# Lightweight Indoor Multi-Object Tracking in Overlapping FOV Multi-Camera Environments

BEV Project와 FastMOT Framework 저장소

사용 전 Docker 및 Nvidia-Docker를 설치해야 합니다!

Nvidia Docker 참조 URL : https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker

## 사용 방법

https://aftermoon-dev.notion.site/FastMOT-BEV-in-Docker-15c1ffbbb113436b872715b2f1e7c7bb 의 4번부터 참조

## DB Structure

<p><img src="https://user-images.githubusercontent.com/51084152/147249911-3871de93-d6ef-4102-b229-e36abd763699.png" width="50%" height="50%"></p>  

## Lightweight Indoor Multi-Object Tracking in Overlapping FOV Multi-Camera Environments  
>**Abstract:** *Multi-Target Multi-Camera Tracking (MTMCT), which aims to track multiple targets within a multi-camera network, has recently attracted considerable attention due to its wide range of applications. The main challenge of MTMCT is to match local tracklets (i.e., sub-trajectories) obtained by different cameras and to combine them into global trajectories across the multi-camera network. This paper addresses the cross-camera tracklet matching problem in scenarios with partially overlapping fields of view (FOVs), such as indoor multi-camera environments. We present a new lightweight matching method for the MTMC task that employs similarity analysis for location features. The proposed approach comprises two steps: (i) extracting the motion information of targets based on a ground projection method and (ii) matching the tracklets using similarity analysis based on the Dynamic Time Warping (DTW) algorithm. We use a Kanade–Lucas–Tomasi (KLT) algorithm-based frame-skipping method to reduce the computational overhead in object detection and to produce a smooth estimate of the target’s local tracklets. To improve matching accuracy, we also investigate three different location features to determine the most appropriate feature for similarity analysis. The effectiveness of the proposed method has been evaluated through real experiments, demonstrating its ability to accurately match local tracklets.*
  
### CALS Architecture  
<p align="center"><img src="https://user-images.githubusercontent.com/51084152/231771241-fb0e775c-5764-43d3-b3ce-fbf9a1b450db.png"  width="500" height="300"/></p>

## Citation
If you find this work useful for your research, please cite our paper:
```bibtex
@article{jang2022lightweight,
  title={Lightweight Indoor Multi-Object Tracking in Overlapping FOV Multi-Camera Environments},
  author={Jang, Jungik and Seon, Minjae and Choi, Jaehyuk},
  journal={Sensors},
  volume={22},
  number={14},
  pages={5267},
  year={2022},
  publisher={MDPI}
}
```
