import argparse
from pathlib import Path
import cv2
import imutils
import os
import numpy as np
import pandas as pd


def get_dir():
    parser = argparse.ArgumentParser(description='Enter name of folder (e.g: fumo)')
    parser.add_argument(
        "name", 
	help="name of image folder",
    )
    p = parser.parse_args()
    data_dir = Path(__file__).absolute().parent/ p.name
    img_name = str(p.name)
    return data_dir, img_name

def rearrange(dir_folder, name):
    df = pd.DataFrame(columns=['img','row','col'])
    for i,img in enumerate(os.listdir(dir_folder)):   
        # load image, convert to HSV
        image = cv2.imread(os.path.join(dir_folder,img))
        height, width = image.shape[:2]
        image_to_process = image.copy()
        image_to_process = cv2.cvtColor(image_to_process, cv2.COLOR_BGR2HSV) 

        colours = ['red','blue']
        counter = {}
        for colour in colours:   
            counter[colour] = 0
            if colour == 'red':
                lower = np.array([110,200,200])
                upper = np.array([130,255,255])
            elif colour == 'blue':
                lower = np.array([0,210,210])
                upper = np.array([20,255,255])

            # find the colour within the HSV range and apply the mask
            image_mask = cv2.inRange(image_to_process, lower, upper)
            image_res = cv2.bitwise_and(image_to_process, image_to_process, mask=image_mask)
            # convert to grayscale, blur it slightly and apply binary threshold
            image_gray = cv2.cvtColor(image_res, cv2.COLOR_BGR2GRAY)
            image_gray = cv2.GaussianBlur(image_gray, (5, 5), 0)
            _,threshold = cv2.threshold(image_gray, 100, 255, cv2.THRESH_BINARY)
            # perform edge detection, then perform dilation and erosion to close gaps between edges
            image_edged = cv2.Canny(threshold, 50, 50) 
            image_edged = cv2.dilate(image_edged, None, iterations=1)
            image_edged = cv2.erode(image_edged, None, iterations=1)
            # find contours 
            cnts = cv2.findContours(image_edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            
            # loop over the contours individually
            for c in cnts:
                # ignore if the contour is too small
                if cv2.contourArea(c) < 2:
                    continue
                counter[colour] += 1
            # input dataframe with the image name, position of row and column
            df.loc[i,'img'] = img[:-4]
            if colour == 'blue':
                df.loc[i,'row'] = counter[colour]
            else:  
                df.loc[i,'col'] = counter[colour]

    # sort the dataframe         
    sorted_df = pd.DataFrame() 
    for row in range(max(df['row'])):
        sort_df = df.loc[df['row'] == row+1]
        sort_df = sort_df.sort_values(by ='col' , ascending=True)
        sorted_df = pd.concat([sorted_df, sort_df], ignore_index=True)

    # make a new blank image with height and width of the final rearranged puzzle
    canvas = np.zeros((height*sorted_df.loc[i,'col'],width*sorted_df.loc[i,'row'],3), np.uint8)

    # paste patches on the image
    for i in range(sorted_df.shape[0]):
        patch = cv2.imread(os.path.join(dir_folder, sorted_df.loc[i,'img'] + '.jpg'))
        x, y, channels = patch.shape
        height = (sorted_df.loc[i,'row']-1)*y
        width = (sorted_df.loc[i,'col']-1)*x
        canvas[width:width+x,height:height+y]=patch
        

    # resize the image into max of 800
    if max(canvas.shape) > 800:
        scale_percent = 800 / max(canvas.shape) * 100 # percent of original size
        width = int(canvas.shape[1] * scale_percent / 100)
        height = int(canvas.shape[0] * scale_percent / 100)
        dim = (width, height)
        result = cv2.resize(canvas,dim)
    else:
        result = canvas


    # write the output image at output directory folder 'result'
    output_dir = 'result'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    cv2.imwrite(os.path.join(output_dir,name + '.jpg'),result)
      
if __name__ == "__main__":
    data_dir, img_name = get_dir()
    rearrange(dir_folder = data_dir, name = img_name)
  

    
