#!/usr/bin/env python
import csv
import matplotlib
import numpy as np
import gps_assisted_simulator_node 
import subprocess
from std_msgs.msg import Float32
import matplotlib
from matplotlib import pyplot as plt

import kalman
import requestHandler
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import MultiArrayLayout
from std_msgs.msg import MultiArrayDimension


def bike_state(data):
    velocity = data.data[6]
    yaw = data.data[9]
    bike_vy = [velocity, yaw]
    
def gps(data):
    #Important fields from data
    latitude = data.data[0] # In degrees
    longitude = data.data[1]
    #psi = data.data[7] # psi = heading in radians
    #velocity = data.data[8]
    # Converts lat long to x,y 
    x, y = requestHandler.math_convert(float(latitude), float(longitude)) 
    # gps current state - only relevant fields
    gps_xy = [x, y]
   


def listener():
    pub = rospy.Publisher('kalman_pub', Float32MultiArray, queue_size=10)
    rospy.init_node('kalman', anonymous=True)
    rospy.Subscriber("bike_state", Float32MultiArray, bike_state)
    rospy.Subscriber("gps", Float32MultiArray, gps)
    rate = rospy.Rate(100)
    #Run until the nodes are shutdown (end.sh run OR start.sh was killed)
    while not rospy.is_shutdown():
        dim = [MultiArrayDimension('data', 4, 4)]
        layout = MultiArrayLayout(dim, 0)
        # The Kalman filter wants the GPS data in matrix form
        #Build matrix from gps x,y coordinates and bike velocity and yaw
        gps_matrix = np.matrix(gps_xy + bike_vy) 
        #Confirms correct shape of matrix
        rospy.loginfo(gps_matrix.shape)
        #save gps state values for later plotting
        gps_data.append(gps_matrix)
        # Run the Kalman filter - if we only have one point we can't run the filter yet
        if len(gps_data) >= 1:

            #If we have 
            if len(gps_data) == 1:
                output_matrix = kalman_real_time.kalman_no_loop(gps_matrix, np.matrix([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]), 
                                                     (gps_data[-1], np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))) 
            else:
                output_matrix = kalman_real_time.kalman_no_loop(gps_matrix, np.matrix([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]), 
                                                     (kalman_state_matrix, p_state_matrix)) 

            kalman_state_matrix = output_matrix[0]
            p_state_matrix = output_matrix[1]                                         
            #Change output_matrix to a standard array for publishing
            kalman_state = output_matrix[0].flatten()
            p_state = output_matrix[1].flatten()
            #save predicted state values for later plotting
            kalman_data.append(kalman_state_matrix) 
            pub.publish(layout, kalman_state)
        rate.sleep()
        rospy.loginfo('SUCCESSFUL ITERATION')
    kalman_data[0] = gps_data[0]
    rospy.loginfo('Test was terminated')
    # Plot the GPS data
    plt.scatter(gps_data[:,0], gps_data[:,1], c='r')
    # Plot the Kalman output
    plt.scatter(kalman_data[:,0], kalman_data[:,1])
    # Show everything
    plt.show()

if __name__ == '__main__':
    #Data from bike_state and gps respectively
    gps_xy = [] #x,y converted from latitude and longitude from gps
    bike_vy = [] #bike velocity and yaw
    #kalman/gps data saved as we go for later plotting
    kalman_data = np.matrix([0])
    gps_data = []
    #state that is published to ROS
    kalman_state = []
    p_state = []
    #State used for kalman_no loop
    kalman_state_matrix = np.matrix([0])
    p_state_matrix = np.matrix([0])

    listener()
