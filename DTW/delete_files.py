import os

start_num = 1
end_num = 20

for i in range(start_num, end_num + 1):
    #os.system('sudo rm -r /home/inclab/mot/INC_BEV_FastMOT/output/paper_5person/skip10/' + str(i) + '/' + 'map_frame')
    os.system('sudo rm -r /home/inclab/mot/paper_5person/no_skip/' + str(i) + '/' + 'frame')