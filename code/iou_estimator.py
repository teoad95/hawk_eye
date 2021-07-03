import numpy as np
import cv2
from matplotlib import path
import matplotlib.pyplot as plt
from improvedIoUCameraToTop import transformAndShow
from shapely.geometry import Polygon
import json
import os.path as op

if __name__ == '__main__':
    
    with open('code/matches.json') as json_file:
        data = json.load(json_file)
    # print(data)
    
    IoU_scores = {}
    ct = 0
    good_ct = 0
    avg_IoU = 0.0
    good_avg_IoU = 0.0
    
    queries = data.keys()
    for query in queries:
    
        test_file_name_idx = query.split('/')[-1].split('_')[0]
        database_file_name_idx = data[query].split('/')[-2:]
        database_file_name_idx = op.join(database_file_name_idx[0], database_file_name_idx[1])
        # print(test_file_name, database_file_name)

        # ------ Image from Test Dataset ------

        test_file_name = 'soccer_data/test/' + test_file_name_idx + '.jpg'
        test_homography_file = 'soccer_data/test/' + test_file_name_idx + '.homographyMatrix'
        
        with open(test_homography_file) as f:
            content = f.readlines()
            
        H = np.zeros((3, 3))
        for i in range(len(content)):
            H[i] = np.array([float(x) for x in content[i].strip().split()])
        top_left = None
        
        try:
            transformed_corners = transformAndShow(test_file_name, H, padding=0, top_left=top_left)
        except:
            ct += 1
            avg_IoU += 0.0
            continue
            
        transformed_corners_database = [[corner[0], corner[1]] 
                                for corner in transformed_corners]
        
        # print("\nTrapezium corners from dataset image-\n", transformed_corners_database)
        
         # ----- Image from dictionary -----
         
        if False:
            database_file_name = 'soccer_data/' + database_file_name_idx
            
            h_database_paths = database_file_name_idx.split('/')
            h_final_path = h_database_paths[0] + '/H' + h_database_paths[1]
            h_final_path = h_final_path[:-3] + 'npy'
            
            database_homography_file = 'soccer_data/' + h_final_path
            
            top_left_path = h_database_paths[1].split('_')[0] + '.txt'
            
            # print(database_homography_file, top_left_path)
            H = np.load(database_homography_file)
            
            with open('soccer_data/top_left/' + top_left_path) as f:
                content = [float(line.strip()) for line in f.readlines()]
            top_left = (content[0], content[1])
            
            try:
                transformed_corners = transformAndShow(database_file_name, H, padding=0, top_left=top_left)
            except:
                ct += 1
                avg_IoU += 0.0
                continue
                
            transformed_corners_dict = [[corner[0] - top_left[0], corner[1] - top_left[1]] for corner in transformed_corners]
            
        else: 
            test_file_name = 'soccer_data/train_val/' + test_file_name_idx + '.jpg'
            test_homography_file = 'soccer_data/train_val/' + test_file_name_idx + '.homographyMatrix'
            
            # print(test_file_name, test_homography_file)
            # exit()
            
            with open(test_homography_file) as f:
                content = f.readlines()
                
            H = np.zeros((3, 3))
            for i in range(len(content)):
                H[i] = np.array([float(x) for x in content[i].strip().split()])
            top_left = None
            
            try:
                transformed_corners = transformAndShow(test_file_name, H, padding=0, top_left=top_left)
            except:
                ct += 1
                avg_IoU += 0.0
                continue
                
            transformed_corners_dict = [[corner[0], corner[1]] for corner in transformed_corners]
            
        # print("Trapezium corners from dictionary image-\n", transformed_corners_dict)

        # ---- IoU calculation ----
        
        try:
            a = Polygon([(x[0], x[1]) for x in transformed_corners_dict])
            b = Polygon([(x[0], x[1]) for x in transformed_corners_database])
            IoU = a.intersection(b).area / a.union(b).area
        except:
            print('bad IoU')
            IoU = 0.0
        
        IoU_scores[query] = IoU
        
        print("IoU: ", IoU)
        
        if IoU > 0.1:
            good_ct += 1
            good_avg_IoU += IoU
        
        if ct % 10 == 0:
            with open('IoU_results.json', 'w') as fi:
                json.dump(IoU_scores, fi)
             
        ct += 1
        avg_IoU += IoU  
        
    print("The Ultimate IoU Scores")
    print("Good mIoU: ", good_avg_IoU / good_ct) 
    print("All mIoU: ", avg_IoU / ct)
    print(good_ct, ct)