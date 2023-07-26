import time as tm
import airsim
import os
import numpy as np
import random as rd
import json
import argparse

tempo = tm.time()
#Correction of a bug that input twice
def cBug1():
    airsim.wait_key()

#Defining the name and type of camera
CAM_NAME = "fixed1"
IS_EXTERNAL_CAM = True

#start some global variables
typePose= 0
interaction = 0

ap = argparse.ArgumentParser()
ap.add_argument('-n', '--nameObject', required=True)
ap.add_argument('-i', '--imageNumber', required=True, type=int)


#starting the conection with airsim
client = airsim.VehicleClient()
client.confirmConnection()

#Making the path to store the pictures
tmp_dir = 'dataset/images'

try:
    os.makedirs(tmp_dir)
except OSError:
    if not os.path.isdir(tmp_dir):
        raise

try:
    os.makedirs("dataJson")
except OSError:
    if not os.path.isdir("dataJson"):
        raise

#starting the simulation
airsim.wait_key('Press any key to get images')
cBug1()

#defining what type of image we want
requests = [airsim.ImageRequest(CAM_NAME, airsim.ImageType.Scene)]
nameObject = vars(ap.parse_args())["nameObject"]

#starting takng pictures
while interaction < vars(ap.parse_args())["imageNumber"]:
    
    #getting the pose of the car and spliting in position and orientation
    objectPose = client.simGetObjectPose(nameObject)


    objectPosition = objectPose.position
    objectOrientation = objectPose.orientation
    #correction factor of car's z_val
    objectZajust = objectPosition.z_val - 1.012

    #Puting the camera close to the car
    
    x = objectPosition.x_val + 4
    y = objectPosition.y_val  + 4

    #Defining the camera's position
    b1 = 4*rd.random() - 2
    b2 = 4*rd.random() - 2 
    a = 2 + (2*rd.random()) - objectZajust
    positions = [(x + b1, y + b2 , objectZajust), (x - (8 + b1), y+ b2 , objectZajust), (x - (8 + b1), y - (8 + b2), objectZajust), (x  + b1, y -(8 + b2), objectZajust),
                 (x + b1, y + b2 , -a), (x - (8 + b1), y+ b2, -a), (x - (8 + b1), y - (8 + b2), -a), (x  + b1, y -(8 + b2), -a)]

    filename = os.path.join(tmp_dir,'image' + nameObject + "_" + str(interaction))
    
    auxAngYaw = np.arange(-0.6, 0.6, 0.001)
    auxAngYawInd = rd.randint(0, len(auxAngYaw)-1)

    auxAngPitch = np.arange(-0.1, 0.1, 0.01)
    auxAngIndPitch = rd.randint(0, len(auxAngPitch)-1)
    #getting the relative distance between camera and car
    x_rel = positions[typePose][0]-objectPosition.x_val
    y_rel = positions[typePose][1]-objectPosition.y_val
    z_rel = positions[typePose][2]-(objectZajust)

    #Adjusting the camera pitch if it is higher than the car
    if z_rel < -2:
        pitch = -np.arctan(-z_rel/np.sqrt((x_rel**2)+(y_rel)**2))    
    else:
        pitch = 0


    #Adjusting the camera yaw to focus on car    
    yaw = np.arctan((y_rel)/(x_rel))
    if x_rel > 0:
         yaw = np.pi + yaw
    
    yaw = yaw + auxAngYaw[auxAngYawInd]
    pitch = pitch + auxAngPitch[auxAngIndPitch]
    
 
    dictInformation = { "car_position" : [objectPosition.x_val, objectPosition.y_val, objectPosition.z_val],
                        "camera_position": positions[typePose], "diffYaw" :auxAngYaw[auxAngYawInd], 
                        "diffPitch": auxAngPitch[auxAngIndPitch]}
    

    jsonString = json.dumps(dictInformation, indent=6)

    with open("dataJson/data"+str(interaction)+".json", "w") as jsonFile:
    #start procedure
        jsonFile.write(jsonString)
        jsonFile.close

    #setting the new camera's pose
    npose = airsim.Pose(position_val=airsim.Vector3r(positions[typePose][0], positions[typePose][1], positions[typePose][2] ),
                         orientation_val=airsim.to_quaternion(pitch, 0, yaw ))
    
    
    client.simSetCameraPose(camera_name=CAM_NAME, pose=npose, external=IS_EXTERNAL_CAM)
    #getting the pictures
    responses = client.simGetImages(requests, external=IS_EXTERNAL_CAM)
    for i, response in enumerate(responses):
        if response.pixels_as_float:
                airsim.write_pfm(os.path.normpath(filename + '.pfm'), airsim.get_pfm_array(response))
        else:
                airsim.write_file(os.path.normpath(filename + '.png'), response.image_data_uint8)
    
    #adjust to the next type of camera's position
    typePose = typePose+1
    if typePose >= 8:
         typePose = 0
    
    interaction = interaction + 1

print(tm.time() - tempo)
