#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import JointState
from markers import *
from funciones import *
from roslib import packages

import rbdl


rospy.init_node("control_pdg")
pub = rospy.Publisher('joint_states', JointState, queue_size=1)
bmarker_actual  = BallMarker(color['RED'])
bmarker_deseado = BallMarker(color['GREEN'])
# Archivos donde se almacenara los datos
#fqact = open("/tmp/qactual.txt", "w")
#fqdes = open("/tmp/qdeseado.txt", "w")
#fxact = open("/tmp/xactual.txt", "w")
#fxdes = open("/tmp/xdeseado.txt", "w")

# Nombres de las articulaciones
jnames = ['joint1', 'joint2','joint3', 'joint4', 'joint5','joint6','joint7']
# Objeto (mensaje) de tipo JointState
jstate = JointState()
# Valores del mensaje
jstate.header.stamp = rospy.Time.now()
jstate.name = jnames

# =============================================================
# Configuracion articular inicial (en radianes)
q = np.array([0.6, 0.3, 0.3, -0.5, -0.6, 0.2, 0.0])
# Velocidad inicial
dq = np.array([0., 0., 0., 0., 0., 0.,0.])
# Configuracion articular deseada
qdes = np.array([0.6, 0.4, 0.2, -0.5, -0.5, 0.1, 0.0])
# =============================================================

# Posicion resultante de la configuracion articular deseada
xdes = fkine_kuka(qdes)[0:3,3]
# Copiar la configuracion articular en el mensaje a ser publicado
jstate.position = q
pub.publish(jstate)

# Modelo RBDL
modelo = rbdl.loadModel('../urdf/lbr_iiwa7_r800.urdf')
ndof   = modelo.q_size     # Grados de libertad

# Frecuencia del envio (en Hz)
freq = 20
dt = 1.0/freq
rate = rospy.Rate(freq)

# Simulador dinamico del robot
robot = Robot(q, dq, ndof, dt)

# Se definen las ganancias del controlador
valores = 0.004*np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
Kp = np.diag(valores)
Kd = 2*np.sqrt(Kp)

# Bucle de ejecucion continua
t = 0.0
while not rospy.is_shutdown():

    # Leer valores del simulador
    q  = robot.read_joint_positions()
    dq = robot.read_joint_velocities()
    # Posicion actual del efector final
    x = fkine_kuka(q)[0:3,3]
    # Tiempo actual (necesario como indicador para ROS)
    jstate.header.stamp = rospy.Time.now()

    # Almacenamiento de datos
    #fxact.write(str(t)+' '+str(x[0])+' '+str(x[1])+' '+str(x[2])+'\n')
    #fxdes.write(str(t)+' '+str(xdes[0])+' '+str(xdes[1])+' '+str(xdes[2])+'\n')
    #fqact.write(str(t)+' '+str(q[0])+' '+str(q[1])+' '+ str(q[2])+' '+ str(q[3])+' '+str(q[4])+' '+str(q[5])+' '+str(q[6])+'\n ')
    #fqdes.write(str(t)+' '+str(qdes[0])+' '+str(qdes[1])+' '+ str(qdes[2])+' '+ str(qdes[3])+' '+str(qdes[4])+' '+str(qdes[5])+' '+str(q[6])+'\n ')

    # ----------------------------
    # Control dinamico (COMPLETAR)
    # ----------------------------
    u = np.zeros(ndof)   # Reemplazar por la ley de control

    zeros = np.zeros(ndof)  #Vector de ceros
    g_1    = np.zeros(ndof)
    rbdl.InverseDynamics(modelo, q, zeros, zeros, g_1)  # Vector de gravedad
   
    g_1 = np.round(g_1,4)
    u = g_1 + Kp.dot(qdes - q) - Kd.dot(dq)   # Ley de Control (PD + Gravedad)
    # ------------------------------


    # Simulacion del robot
    robot.send_command(u)

    # Publicacion del mensaje
    jstate.position = q
    pub.publish(jstate)
    bmarker_deseado.xyz(xdes)
    bmarker_actual.xyz(x)
    t = t+dt
    # Esperar hasta la siguiente  iteracion
    rate.sleep()

#fqact.close()
#fqdes.close()
#fxact.close()
#fxdes.close()
