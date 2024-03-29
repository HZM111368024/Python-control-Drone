"""
Simple script for take off and control with arrow keys
"""

import time
from pymavlink import mavutil

# - Importing Tkinter: sudo apt-get install python-tk
import tkinter as tk
from tkinter import font
from tkinter import ttk

mavutil.set_dialect("ardupilotmega")

# -- Connect to the vehicle
print('Connecting...')
vehicle = mavutil.mavlink_connection('tcp:127.0.0.1:5763', )
# vehicle = mavutil.mavlink_connection('COM9', baud=57600)


# -- Set up the commanded flying speed
gnd_speed = 0.2  # [m/s]

# - Read the keyboard with tkinter
root = tk.Tk()
root.geometry("800x400")  # Size of the window
root.title("SITL Controller")  # Adding a title

labelfont = font.Font(family="microsoft yahe", size=12, weight=font.BOLD)
labelword = ["Q", "W", "E", "A", "S", "D", "UP", "DOWN", "M", "Alarm"]
labellist = []
relay_status = 0
servo_pwm = 2500


# -- Define arm and takeoff
def arm_and_takeoff(altitude):
    # Arm the motors
    print("Arming motors")
    arm(0, 1)

    # Wait for the vehicle to be armed
    while True:
        msg = vehicle.recv_match(type='HEARTBEAT', blocking=True)
        if msg.get_type() == 'HEARTBEAT' and msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
            print("break")
            break
        else:
            print("Waiting for vehicle to be armed")
            time.sleep(1)

    # Take off to the specified altitude
    print("Taking off")
    takeoff(0, altitude)
    # Wait for the vehicle to reach the target altitude
    """while True:
        msg = vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg.get_type() == 'GLOBAL_POSITION_INT':
            alt = msg.alt / 1000.0
            print(">> Altitude = %.1f m" % alt)
            if alt >= altitude - 1.0:
                print("Target altitude reached")
                break
        time.sleep(1)"""


def arm(drone_id, arm_status):
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0,  # target system ID
        0,  # target component ID
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,  # command
        0,  # confirmation
        arm_status,  # arm
        0, 0, 0, 0, 0, 0  # unused parameters
    )
    vehicle.mav.send(msg)


def takeoff(drone_id, altitude):
    print("takeoff")
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0,  # target system ID
        0,  # target component ID
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,  # command
        0,  # confirmation
        0, 0, 0, 0,  # unused parameters
        0, 0, altitude  # parameters 5-8
    )
    vehicle.mav.send(msg)
    # vehicle.flush()


# -- Define the function for sending mavlink velocity command in body frame
def set_velocity_body(drone_id, vx, vy, vz):
    """ Remember: vz is positive downward!!!
    http://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html

    Bitmask to indicate which dimensions should be ignored by the vehicle
    (a value of 0b0000000000000000 or 0b0000001000000000 indicates that
    none of the setpoint dimensions should be ignored). Mapping:
    bit 1: x,  bit 2: y,  bit 3: z,
    bit 4: vx, bit 5: vy, bit 6: vz,
    bit 7: ax, bit 8: ay, bit 9:
    """
    msg = vehicle.mav.set_position_target_local_ned_encode(
        0,
        0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # command
        0b0000111111000111,  # BITMASK -> Consider only the velocities
        0, 0, 0,  # POSITION
        vx, vy, vz,  # VELOCITY
        0, 0, 0,  # ACCELERATIONS
        0, 0)  # unused parameters
    vehicle.mav.send(msg)
    # vehicle.flush()


# -- Control Drone yaw angle
def condition_yaw(drone_id, heading, relative, direction):
    if relative:
        is_relative = 1  # yaw relative to direction of travel
    else:
        is_relative = 0  # yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        heading,  # param 1, yaw in degrees
        0,  # param 2, yaw speed deg/s
        direction,  # param 3, direction -1 ccw, 1 cw
        is_relative,  # param 4, relative offset 1, absolute angle 0
        0, 0, 0)  # unused parameters
    # send command to vehicle
    vehicle.mav.send(msg)
    # vehicle.flush()


def relay(drone_id, num, status):
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_CMD_DO_SET_RELAY,  # command
        0,  # confirmation
        num,  # param 1, relay number
        status,  # param 2, relay status
        0, 0, 0, 0, 0)  # unused parameters
    # send command to vehicle
    vehicle.mav.send(msg)
    # vehicle.flush()


def servo(drone_id, num, pwm):
    # Create a MAVLink message to set a servo
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0,  # target_system
        0,  # target_component
        mavutil.mavlink.MAV_CMD_DO_SET_SERVO,  # command
        0,  # confirmation
        num,  # servo number
        pwm,  # PWM value
        0, 0, 0, 0, 0)  # unused parameters
    # send the MAVLink message
    vehicle.mav.send(msg)
    # vehicle.flush()


def mode(drone_id, custom_mode):
    msg = mavutil.mavlink.MAVLink_command_long_message(
        0,  # target_system
        0,  # target_component
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,  # command
        0,  # confirmation
        1,  # param1
        4,  # param2
        0, 0, 0, 0, 0)  # unused parameters
    # Send the MAVLink message
    vehicle.mav.send(msg)
    # vehicle.flush()


# -- Key event function
def key(event):
    root.focus()
    id = int(list({box.current()})[0])
    global relay_status
    global servo_pwm
    if event.char == event.keysym:  # -- standard keys
        if event.keysym == 'w' or event.keysym == 'W':
            print("往前")
            set_velocity_body(id, gnd_speed, 0, 0)
            labellist[1].config(bg="firebrick4")
        elif event.keysym == 's' or event.keysym == 'S':
            set_velocity_body(id, -gnd_speed, 0, 0)
            print("往後")
            labellist[4].config(bg="firebrick4")
        elif event.keysym == 'a' or event.keysym == 'A':
            set_velocity_body(id, 0, -gnd_speed, 0)
            print("往左")
            labellist[3].config(bg="firebrick4")
        elif event.keysym == 'd' or event.keysym == 'D':
            set_velocity_body(id, 0, gnd_speed, 0)
            print("往右")
            labellist[5].config(bg="firebrick4")
        elif event.keysym == 'q' or event.keysym == 'Q':
            condition_yaw(id, 10, True, -1)
            print("Yaw往左")
            labellist[0].config(bg="firebrick4")
        elif event.keysym == 'e' or event.keysym == 'E':
            condition_yaw(id, 10, True, 1)
            print("Yaw往右")
            labellist[2].config(bg="firebrick4")
        elif event.keysym == 'm' or event.keysym == 'M':
            mode(id, 4)
            labellist[8].config(bg="firebrick4")
        elif event.keysym == 'n' or event.keysym == 'N':
            mode(id, 9)
        elif event.keysym == '1':
            if relay_status == 0:
                relay_status = 1
                relay(id, 0, relay_status)
            else:
                relay_status = 0
                relay(id, 0, relay_status)
        elif event.keysym == '8':
            servo_pwm += 30
            if servo_pwm >= 2500:
                servo_pwm = 2500
            servo(id, 9, servo_pwm)
        elif event.keysym == '2':
            servo_pwm -= 30
            if servo_pwm <= 500:
                servo_pwm = 500
            servo(id, 9, servo_pwm)

    else:  # -- non standard keys
        if event.keysym == 'Up':
            set_velocity_body(vehicle, 0, 0, -gnd_speed)
            print("往上")
            labellist[6].config(bg="firebrick4")
        elif event.keysym == 'Down':
            set_velocity_body(vehicle, 0, 0, gnd_speed)
            print("往下")
            labellist[7].config(bg="firebrick4")


def KeyRelease(event):
    for word in range(len(labelword)):
        labellist[word].config(bg="black")


for i in range(len(labelword)):
    labellist.append(tk.Label(root,  # 文字標示所在視窗
                              text=labelword[i],  # 顯示文字
                              bg='black',  # 背景顏色
                              font=labelfont,  # 字型與大小
                              fg="white",
                              width=15, height=2)  # 文字標示尺寸
                     )

box = ttk.Combobox(root,
                   width=15,
                   values=['All Drone', 'Drone_001', 'Drone_002', 'Drone_003', 'Drone_004', 'Drone_005'],
                   state='readonly')
com_box = ttk.Combobox(root,
                       width=15,
                       values=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6'],
                       state='readonly')


def takeoff_button_callback():
    arm_and_takeoff(2)


takeoff_button = tk.Button(root, text="Takeoff", command=takeoff_button_callback)

# 排版

labellist[0].grid(row=0, column=0, padx=10, pady=30)
labellist[1].grid(row=0, column=1, padx=10, pady=30)
labellist[2].grid(row=0, column=2, padx=10, pady=30)
labellist[6].grid(row=0, column=3, padx=90, pady=30)
labellist[3].grid(row=1, column=0, padx=0, pady=10)
labellist[4].grid(row=1, column=1, padx=10, pady=10)
labellist[5].grid(row=1, column=2, padx=10, pady=10)
labellist[7].grid(row=1, column=3, padx=90, pady=10)
labellist[8].grid(row=2, column=3, padx=90)
com_box.grid(row=3, column=3, pady=10)
box.grid(row=4, column=3, pady=10)
takeoff_button.grid(row=5, column=3)

root.bind_all('<Key>', key)
root.bind_all('<KeyRelease>', KeyRelease)
root.mainloop()

# MAIN FUNCTION
# 起飛到三公尺
mode(0, 4)

# check servo status
servo(0, 9, 2500)
