#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import JointState

from markers import *
from funciones import *

if __name__ == '__main__':

    # Initialize the node
    rospy.init_node("testKineControlPosition")
    print('starting motion ... ')
    # Publisher: publish to the joint_states topic
    pub = rospy.Publisher('joint_states', JointState, queue_size=10)
    # Files for the logs
    fxcurrent = open("/tmp/xcurrent.txt", "w")                
    fxdesired = open("/tmp/xdesired.txt", "w")
    fq = open("/tmp/q.txt", "w")

    # Markers for the current and desired positions
    bmarker_current  = BallMarker(color['RED'])
    bmarker_desired = BallMarker(color['GREEN'])

    # Joint names
    jnames = ['joint1', 'joint2','joint3', 'joint4', 'joint5','joint6','joint7']

    # Desired position
    #xd = np.array([0.84, 0.125, 0.249])
    #xd = np.array([0.44, 0.22, 0.5])
    xd = np.array([-0.44, 0.6, 0.8])
    # Initial configuration
    q0 = np.array([0.4, 0.2, 0.6, -0.1, -0.5, 0.0, 0.2])
    #q0 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    #q0 = np.array([0.8, 1.0, 0.8, 0.6, 0.8, 0.5, 0.0, 0.6])
    # Resulting initial position (end effector with respect to the base link)
    T = fkine_kuka(q0)
    x0 = T[0:3,3]

    # Red marker shows the achieved position
    bmarker_current.xyz(x0)
    # Green marker shows the desired position
    bmarker_desired.xyz(xd)

    # Instance of the JointState message
    jstate = JointState()
    # Values of the message
    jstate.header.stamp = rospy.Time.now()
    jstate.name = jnames
    # Add the head joint value (with value 0) to the joints
    jstate.position = q0

    # Frequency (in Hz) and control period 
    freq = 200
    dt = 1.0/freq
    rate = rospy.Rate(freq)

    # Initial joint configuration
    q = copy(q0)
    k = 0.5
    count = 0
    # Main loop
    while not rospy.is_shutdown():
        # Current time (needed for ROS)
        jstate.header.stamp = rospy.Time.now()
        # Kinematic control law for position (complete here)
        # -----------------------------
        T = fkine_kuka(q)  # Cinemática directa para obtener la posición actual del efector final
        x = T[0:3, 3]  # Posición actual
        e = x - xd  # Error de posición

        # Calcular la Jacobiana (matriz de derivadas) del robot en la posición actual
        J = jacobian(q)
        
        # Verificar si la posición deseada se alcanzó
        if np.linalg.norm(e) < 0.001:
            print("Posición deseada alcanzada.")
            break
        
        # Derivada del error
        de = -k*e
        # Variación de la configuración articular
        dq = np.linalg.pinv(J).dot(de)
        # Integración para obtener la nueva configuración articular
        q = q + dt*dq
        # Actualizar las articulaciones
        # -----------------------------
        count = count + 1 
        if(count > 100000):
            print('Max number of iterations reached')
            break
        
        # Log values                                                      
        fxcurrent.write(str(x[0])+' '+str(x[1]) +' '+str(x[2])+'\n')
        fxdesired.write(str(xd[0])+' '+str(xd[1])+' '+str(xd[2])+'\n')
        fq.write(str(q[0])+" "+str(q[1])+" "+str(q[2])+" "+str(q[3])+" "+
                 str(q[4])+" "+str(q[5])+" "+str(q[6])+"\n")
        
        # Publish the message
        jstate.position = q
        pub.publish(jstate)
        bmarker_desired.xyz(xd)
        bmarker_current.xyz(x)
        # Wait for the next iteration
        rate.sleep()

    print('ending motion ...')
    fxcurrent.close()
    fxdesired.close()
    fq.close()