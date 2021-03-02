#! /usr/bin/env python
# -*- coding: utf-8 -*-
# this Web.py also forks RegistrationToSvr.py - Donny
# 단순 클라이언트의 post 요청을 받는 웹서버 였으나, 이제는 웹 담당일진
# 사무실 내 서버컴퓨터와의 등록/세션핸들링, 미디어서버와의 접속, 클라이언트와의 접속 모든걸 담당한다.
from flask import Flask, request
import os     #importing os library so as to communicate with the system
import time   #importing time library to make Rpi wait because its too impatient 
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1) # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio #importing GPIO library
# Raspberry Pi PWN PIN 12, 13, 18, 19
import RegistrationToSvr
import GpioController

##left wheel
ESC_LEFT=12
##right wheel
ESC_RIGHT=13
INJORA35T_STOP=1500 #should be init. (by manually)
INJORA35T_WIDTH=40 #*10 pwm, 40 means it has +-400 pwm.


pi = pigpio.pi()
pi.set_servo_pulsewidth(ESC_LEFT, INJORA35T_STOP) #esc init
pi.set_servo_pulsewidth(ESC_RIGHT, INJORA35T_STOP) #esc init
pi.set_PWM_frequency(ESC_LEFT,50)
pi.set_PWM_frequency(ESC_RIGHT,50)

RegistrationToSvr.__name__ #Do registration work to onff local server.
# gpioController = GpioController.__name__ #GPIO fast-serized queue system(sort of)
gpioController = GpioController.GpioController() #GPIO fast-serized queue system(sort of)
gpioController.popDequePeriodically()

app = Flask(__name__)

def Clamp(val,vMin,vMax):
	if  val > vMin and val < vMax:
		return val
	elif val < vMin:
		return vMin
	elif val > vMax:
		return vMax
	else :
		return val

@app.route("/")
def connectionCheck(): 
	return "working Fine"
	
@app.route("/init")
def arm():
	#movement
	# pi.set_servo_pulsewidth(ESC_LEFT, 1500)
	# pi.set_servo_pulsewidth(ESC_RIGHT, 1500) 
	pi.set_PWM_frequency(ESC_LEFT,50)
	pi.set_PWM_frequency(ESC_RIGHT,50) # 20 times per a second.
	gpioController.gpio_PIN_PWM(ESC_LEFT, 1500) # stop
	gpioController.gpio_PIN_PWM(ESC_RIGHT, 1500) # stop
	# pi.set_PWM_frequency(STEER,50)
	time.sleep(100)
	return "ready"
	
#do not use
# @app.route("/intialize")
# def initialize():
# 	pi.set_servo_pulsewidth(ESC, 0)
# 	print("Disconnect the battery")
# 	time.sleep(1)
# 	pi.set_servo_pulsewidth(ESC, max_value)
# 	print("Connect the battery NOW.. you will here two beeps, then wait for a gradual falling tone then press Enter")
# 	time.sleep(2)
# 	pi.set_servo_pulsewidth(ESC, min_value)
# 	print ("Wierd eh! Special tone")
# 	time.sleep(7)
# 	print ("Wait for it ....")
# 	time.sleep (5)
# 	print ("Im working on it, DONT WORRY JUST WAIT.....")
# 	pi.set_servo_pulsewidth(ESC, 0)
# 	time.sleep(2)
# 	print ("Arming ESC now...")
# 	pi.set_servo_pulsewidth(ESC, min_value)
# 	time.sleep(1)
# 	print ("See.... uhhhhh")
            

#!!IMPORTANT !!
#!!this pwm value is ESC(quicrun1060) with INJORA 550 BRUSHED MOTOR 35T
#totally different from another motor!!!
#right wheel
@app.route("/motor_right")
def motorControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		# pi.set_servo_pulsewidth(ESC_RIGHT, int(Clamp(1500-velocity*40,1100,1500)))
		gpioController.gpio_PIN_PWM(ESC_RIGHT, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP+velocity*INJORA35T_WIDTH
			,INJORA35T_STOP
			,INJORA35T_STOP + (INJORA35T_WIDTH*10)))
		# pi.set_servo_pulsewidth(ESC_RIGHT, int(Clamp(1500+velocity*40,1500,1900)))
		gpioController.gpio_PIN_PWM(ESC_RIGHT, pwm)
	elif state == "stop":
		# pi.set_servo_pulsewidth(ESC_RIGHT, 1500)
		gpioController.gpio_PIN_PWM(ESC_RIGHT, INJORA35T_STOP)
	else: 
		# pi.set_servo_pulsewidth(ESC_RIGHT, 1500)
		gpioController.gpio_PIN_PWM(ESC_RIGHT, INJORA35T_STOP)
	return ""
	
#left wheel
@app.route("/motor_left")
def steerContorl():
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		# pi.set_servo_pulsewidth(ESC_LEFT, int(Clamp(1500-velocity*40,1100,1500)))
		gpioController.gpio_PIN_PWM(ESC_LEFT, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP+velocity*INJORA35T_WIDTH
			,INJORA35T_STOP
			,INJORA35T_STOP + (INJORA35T_WIDTH*10)))
		# pi.set_servo_pulsewidth(ESC_LEFT, int(Clamp(1500+velocity*40,1500,1900)))
		gpioController.gpio_PIN_PWM(ESC_LEFT, pwm)
	elif state == "stop":
		# pi.set_servo_pulsewidth(ESC_LEFT, 1500)
		gpioController.gpio_PIN_PWM(ESC_LEFT, INJORA35T_STOP)
	else: 
		# pi.set_servo_pulsewidth(ESC_LEFT, 1500)
		gpioController.gpio_PIN_PWM(ESC_LEFT, INJORA35T_STOP)
	return ""

#WEAPON1_blade(not yet)
@app.route("/weapon1")
def weapon1Control(): 
	state = request.args.get("state")
	if state == "run":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(ESC_WEAPON, int(Clamp(1400+10*50,1400,1900)))
	elif state == "stop":
		pi.set_servo_pulsewidth(ESC_WEAPON, 1400)
	else: 
		pi.set_servo_pulsewidth(ESC_WEAPON, 1400)
	return "Checked: " + state

#Not used 
@app.route("/camera")
def cameraControl():
	global Camera_X,Camera_Y
	dir = request.args.get("dir")
	velocity = int(request.args.get("vel"))*10 #0~10, 0~5/2 
	if dir == "up":
		Camera_Y = int(Clamp(Camera_Y-velocity,Camera_Y_MIN,Camera_Y_MAX))
	elif dir == "down":
		Camera_Y = int(Clamp(Camera_Y+velocity,Camera_Y_MIN,Camera_Y_MAX))
	elif dir == "left":
		Camera_X = int(Clamp(Camera_X+velocity,Camera_X_MIN,Camera_X_MAX))
	elif dir == "right":
		Camera_X = int(Clamp(Camera_X-velocity,Camera_X_MIN,Camera_X_MAX))
	pi.set_servo_pulsewidth(CAMERA_X,Camera_X) # pin, pwm
	pi.set_servo_pulsewidth(CAMERA_Y,Camera_Y) # pin, pwm
	return "steered"

if __name__ == "__main__":
	app.run(host="0.0.0.0")

