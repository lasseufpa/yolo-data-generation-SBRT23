import os
import numpy as np
import json
import cv2
import argparse

#hfunction to get the yolo format
def convert(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

ap = argparse.ArgumentParser()
ap.add_argument('-n', '--nameObject', required=True)
try:
    os.makedirs("fotosBB")
except OSError:
    if not os.path.isdir("fotosBB"):
        raise

try:
    os.makedirs("dataset/labels")
except OSError:
    if not os.path.isdir("dataset/labels"):
        raise


yolobox = []
count = 0
#counting the numbers of photos
for root_dir, cur_dir, files in os.walk("dataJson"):
    count += len(files)

#Generating the bounding box for each photo 
for i in range(count):
    #getting the photo's information
    file = "dataJson/data" + str(i) + ".json"
    a = open(file, 'r')
    ajson = json.load(a)

    #caculating the distance between car and camera
    x_rel = ajson["car_position"][0] - ajson["camera_position"][0]
    y_rel = ajson["car_position"][1] - ajson["camera_position"][1]
    z_rel = ajson["car_position"][2] - ajson["camera_position"][2]
    distanceCC = np.sqrt((x_rel**2) + (y_rel**2)
                         + (z_rel**2))
    #Getting the angular "error" of the camera's rotation
    angYaw = ajson["diffYaw"]
    angPitch = ajson["diffPitch"]

    #deffining a central point for the bounding box
    midX = 130
    midY = 80
    
    if z_rel > 4 and np.abs(y_rel) < 4:
        modo = 2
    else:
        modo = 1

    if i == 6:
        print(distanceCC)
    if modo == 2:
        heigh = 95 * 6.122 / distanceCC 
        width = 75 *6.122/ distanceCC
        correctBB_X = 15*np.sqrt(2*(distanceCC**2) - (2*(distanceCC**2)*np.cos(angYaw)))
        correctBB_Y = 20*np.sqrt(2*(distanceCC**2) - (2*(distanceCC**2)*np.cos(angPitch)))
     

    else:
        #deffining a proportional width and heigh using the distance Camera-car as base
        width = 95 * 6.122 / distanceCC 
        heigh = 65 *6.122/ distanceCC

        #Calculating the correction factor for the bounding box centralize the car 
        
        correctBB_X = (15 * 7.10 / distanceCC)*np.sqrt(2*(distanceCC**2) - (2*(distanceCC**2)*np.cos(angYaw)))
        correctBB_Y = (12 * 7.10/distanceCC)*np.sqrt(2*(distanceCC**2) - (2*(distanceCC**2)*np.cos(angPitch)))

    #analysing if the car is more left or more right in the photo
    if angYaw < 0:
        midX = midX + correctBB_X
    else:
        midX = midX - correctBB_X

    #analysing if the car is upper or bottom in the photo
    if angPitch < 0:
        midY = midY - correctBB_Y
    else:
        midY = midY + correctBB_Y

    #generating the photos with the bounding box
    tmp_dir = 'dataset/images/'
    picture = os.path.join(tmp_dir,'image' + vars(ap.parse_args())["nameObject"] + "_" + str(i)+".png")
    saveDir = os.path.join("fotosBB/",'imageBB' + "_" + str(i)+".png")
    
    image = cv2.imread(picture)

    predictions = {'predictions': [{'x': midX, 'y': midY, 'width': width, 'height': heigh, 
                                    'confidence': 0.7369905710220337}]}
    aux = 0
    for bounding_box in predictions["predictions"]:
        x0 = bounding_box['x'] - bounding_box['width'] / 2
        x1 = bounding_box['x'] + bounding_box['width'] / 2
        y0 = bounding_box['y'] - bounding_box['height'] / 2
        y1 = bounding_box['y'] + bounding_box['height'] / 2

        im=image.shape
        w= int(im[1])
        h= int(im[0])

        if x0 < 0:
            x0 = 0
        elif x1> w:
            x1 = w
        if y0 < 0:
            y0 = 0
        elif y1 > h:
            y1 = h
        b = (x0, x1, y0, y1)
        bb = convert((w,h), b)
        yolobox.append(bb)

        start_point = (int(x0), int(y0))
        end_point = (int(x1), int(y1))
        cv2.rectangle(image, start_point, end_point, color=(255,0,0), thickness=2)

        yolofile = open("dataset/labels/image" + "_" + str(i) + ".txt", 'w+')
        txt =str(0) + " " + str(yolobox[i][0]) + " " + str(yolobox[i][1]) + " " + str(yolobox[i][2]) + " " + str(yolobox[i][3])
        yolofile.write(txt)
        yolofile.close()

    cv2.imwrite(saveDir, image)
