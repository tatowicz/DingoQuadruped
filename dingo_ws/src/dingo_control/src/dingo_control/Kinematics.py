import numpy as np
from numpy.linalg import inv, norm
from numpy import asarray, matrix
from math import *
#import matplotlib.pyplot as plt
from dingo_control.util import RotMatrix3D, point_to_rad
from transforms3d.euler import euler2mat


def leg_explicit_inverse_kinematics(r_body_foot, leg_index, config):
    """Find the joint angles corresponding to the given body-relative foot position for a given leg and configuration
    
    Parameters
    ----------
    r_body_foot : [type]
        [description]
    leg_index : [type]
        [description]
    config : [type]
        [description]
    
    Returns
    -------
    numpy array (3)
        Array of corresponding joint angles.
    """
    #This inverse kinematics code has a different axis definition from pupper. Conversion to pupper frame:
    x,y,z = r_body_foot
    y = -y
    r_body_foot = np.array([x,y,z])
    
    #Temp
    phi = radians(73.17)
    L1 = 0.04973
    L2 = 0.140
    L3 = 0.1631477
    
    #Determine if leg is a right or a left leg
    if leg_index == 2 or leg_index == 4:
        is_right = 0
    else:
        is_right = 1
    
    #rotate the origin frame to be in-line with L1 for calculating theta_1 (rotation about x-axis):
    R1 = pi/2 - phi
    if is_right: rot_mtx = RotMatrix3D([-R1,0,0],is_radians=True)
    else: rot_mtx = RotMatrix3D([R1,0,0],is_radians=True)
    r_body_foot_ = rot_mtx * (np.reshape(r_body_foot,[3,1]))
    r_body_foot_ = np.ravel(r_body_foot_)
    
    # xyz in the rotated coordinate system
    x = r_body_foot_[0]
    y = r_body_foot_[1]
    z = r_body_foot_[2]

    # length of vector projected on the YZ plane. equiv. to len_A = sqrt(y**2 + z**2)
    len_A = norm([0,y,z])   
    
    # a_1 : angle from the positive y-axis to the end-effector (0 <= a_1 < 2pi)
    # a_2 : angle bewtween len_A and leg's projection line on YZ plane
    # a_3 : angle between link1 and length len_A
    a_1 = point_to_rad(y,z)                     
    a_2 = asin(sin(phi)*L1/len_A) #correct
    a_3 = pi - a_2 - phi #correct                   
    
    # angle of link1 about the x-axis 
    if is_right: theta_1 = a_1 + a_3
    else: 
        theta_1 = a_1 + a_3
    if theta_1 >= 2*pi: theta_1 -= 2*pi
    
    #Translate frame to the frame of the leg
    offset = np.array([0.0,L1*cos(theta_1),L1*sin(theta_1)])
    translated_frame = r_body_foot_ - offset
    
    print(translated_frame)
    
    if is_right: R2 = theta_1 + phi - pi/2
    else: R2 = -(pi/2 - phi + theta_1) #This line may need to be adjusted
    
    # create rotation matrix to work on a new 2D plane (XZ_)
    rot_mtx = RotMatrix3D([-R2,0,0],is_radians=True)
    j4_2_vec_ = rot_mtx * (np.reshape(translated_frame,[3,1]))
    j4_2_vec_ = np.ravel(j4_2_vec_)
    # xyz in the rotated coordinate system + offset due to link_1 removed
    x_, y_, z_ = j4_2_vec_[0], j4_2_vec_[1], j4_2_vec_[2]
    
    print(x_)
    print(y_)
    print(z_)
    
    len_B = norm([x_, 0, z_]) # norm(j4-j2)
    
    # handling mathematically invalid input, i.e., point too far away to reach
    if len_B >= (L2 + L3): 
        len_B = (L2 + L3) * 0.99999
        # self.node.get_logger().warn('target coordinate: [%f %f %f] too far away' % (x, y, z))
        print('target coordinate: [%f %f %f] too far away' % (x, y, z))
    
    # b_1 : angle between +ve x-axis and len_B (0 <= b_1 < 2pi)
    # b_2 : angle between len_B and link_2
    # b_3 : angle between link_2 and link_3
    b_1 = point_to_rad(x_, z_)  
    b_2 = acos((L2**2 + len_B**2 - L3**2) / (2 * L2 * len_B)) 
    b_3 = acos((L2**2 + L3**2 - len_B**2) / (2 * L2 * L3))  
    
    # assuming theta_2 = 0 when the leg is pointing down (i.e., 270 degrees offset from the +ve x-axis)
    theta_2 = b_1 - b_2    
    theta_3 = pi - b_3
    
    # CALCULATE THE COORDINATES OF THE JOINTS FOR VISUALIZATION
    j1 = np.array([0,0,0])
    
    # calculate joint 3
    #j3_ = np.reshape(np.array([L2*cos(theta_2),0, L2*sin(theta_2)]),[3,1])
    #j3 = np.asarray(j2 + np.reshape(np.linalg.inv(rot_mtx)*j3_, [1,3])).flatten()
    
    # calculate joint 4
    #j4_ = j3_ + np.reshape(np.array([L3*cos(theta_2+theta_3),0, L3*sin(theta_2+theta_3)]), [3,1])
    #j4 = np.asarray(j2 + np.reshape(np.linalg.inv(rot_mtx)*j4_, [1,3])).flatten()
    
    #Calculating theta_0 (angle of the servo attached to the linkage to achieve desired theta_3 and theta_2 combo)
    #theta_0 = linkage_calculation(theta_2, theta_3)

    # print(degrees(angles[0]))
    return [degrees(angles[0]), degrees(angles[1]), degrees(angles[2])]



def four_legs_inverse_kinematics(r_body_foot, config):
    """Find the joint angles for all twelve DOF correspoinding to the given matrix of body-relative foot positions.
    
    Parameters
    ----------
    r_body_foot : numpy array (3,4)
        Matrix of the body-frame foot positions. Each column corresponds to a separate foot.
    config : Config object
        Object of robot configuration parameters.
    
    Returns
    -------
    numpy array (3,4)
        Matrix of corresponding joint angles.
    """
    alpha = np.zeros((3, 4))
    for i in range(4):
        body_offset = config.LEG_ORIGINS[:, i]
        alpha[:, i] = leg_explicit_inverse_kinematics(
            r_body_foot[:, i] - body_offset, i, config
        )
    return alpha

def angle_corrector(angles=[0,0,0], is_right=1):
    theta_1 = angles[0]
    theta_2 = angles[1] - pi
    theta_3 = angles[2] - pi/2

    #if is_right:
    #   theta_1 = angles[0] - pi
    #    theta_2 = angles[1] + 45*pi/180 # 45 degrees initial offset
    #else: 
    #    if angles[0] > pi:  
    #        theta_1 = angles[0] - 2*pi
    #    else: theta_1 = angles[0]
    #    
    #    theta_2 = -angles[1] - 45*pi/180

    #theta_3 = -angles[2] + 45*pi/180
    return [theta_1, theta_2, theta_3]
