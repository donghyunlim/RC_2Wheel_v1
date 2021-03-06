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
from rpi_common_module import RegistrationToSvr
from rpi_common_module import SmoothGpioController
# import GpioController
from rpi_common_module import HeartBeatToSvr
from rpi_common_module import LedController
from rpi_common_module import device_http_api_handler
from rpi_common_module.model import device_info
import requests
from threading import Timer

##PIN MAP
ESC_LEFT=12 #left wheel
ESC_RIGHT=13 #right wheel
ESC_WEAPON=15 #ESC used weapon
SERVO_WEAPON_1=18 #Servo used weapon
CAMERA_X = 22 #cam X
CAMERA_Y = 23 #cam y
PRESS_SENSOR = 4

KICK_SOLENOID = 24 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_1 = 25 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_2 = 8 #relay for solenoid

INJORA35T_STOP=1500 #should be init. (by manually)
INJORA35T_WIDTH=25 #*10 pwm, 40 means it has +-400 pwm.
INJORA35T_OFFSET_MIN_WORK_PWM=160 #Offset for minimum work(starts rotate) (21T PWM 70) for now
#210601 donny - for now, 2wheel minimun operative pwm is about +-160.

Camera_X_MAX = 2500 # 2520, on origin code
Camera_X_MIN = 520
Camera_Y_MAX = 1500
Camera_Y_MIN = 800

Camera_X = 1500
Camera_Y = 1000

pi = pigpio.pi()
pi.set_mode(KICK_SOLENOID, pigpio.OUTPUT)
pi.set_mode(KICK_SOLENOID_PWR_SUPPORT_1, pigpio.OUTPUT)
pi.set_mode(KICK_SOLENOID_PWR_SUPPORT_2, pigpio.OUTPUT)
pi.set_servo_pulsewidth(ESC_LEFT, INJORA35T_STOP) #esc init
pi.set_servo_pulsewidth(ESC_RIGHT, INJORA35T_STOP) #esc init
pi.set_servo_pulsewidth(ESC_WEAPON, INJORA35T_STOP)
pi.set_PWM_frequency(ESC_LEFT,500) #supersafe -> 50hz, spec -> 500hz
pi.set_PWM_frequency(ESC_RIGHT,500) #supersafe -> 50hz, spec -> 500hz
pi.set_PWM_frequency(ESC_WEAPON,50) #supersafe -> 50hz

pi.set_mode(PRESS_SENSOR, pigpio.INPUT) # flow sensor
pi.set_pull_up_down(PRESS_SENSOR, pigpio.PUD_DOWN)

# gpioController = GpioController.GpioController() #GPIO fast-serized queue system(sort of)
gpioController = SmoothGpioController.GpioController() #GPIO fast-serized queue system(sort of)
gpioController.setOurDefaultPWM(INJORA35T_STOP, INJORA35T_WIDTH)
gpioController.popDequePeriodically()

#Server Matters
RegistrationToSvr.__name__ #Do registration work to onff local server.
registratorVariableGetter = RegistrationToSvr.Getter()

deviceInformation = device_info.DeviceInformation()
deviceInformation.setMyInformation(
	registratorVariableGetter.getMyType(),
	registratorVariableGetter.getPrivIP(),
	registratorVariableGetter.getPublibcIP(),
	registratorVariableGetter.getMyPrefferedWebSvrPort(),
	registratorVariableGetter.getMyPrefferedMediaSvrPort()
)

heartbeater = HeartBeatToSvr.HeartBeating()
heartbeater.setMyInfo(
	deviceInformation.deviceType,
	deviceInformation.privIP,
	deviceInformation.publicIP,
	deviceInformation.websvrPort,
	deviceInformation.mediasvrPort
)
heartbeater.heartbeating()

#Led Controller (ws2812, neopixel)
ledController = LedController.LedControl()
#flags
isCharging = False

app = Flask(__name__)
app.register_blueprint(device_http_api_handler.DeviceHttpApiHandler.deviceHttpApiHandler)

def Clamp(val,vMin,vMax):
	if  val > vMin and val < vMax:
		return val
	elif val < vMin:
		return vMin
	elif val > vMax:
		return vMax
	else :
		return val

def pressCallback(gpio, level, tick):
	ledController.setTargetBright(255,0,0)
	ledController.blinking(4)
	# print("inpuT!"+str(gpio)+str(level)+str(tick))

@app.route("/")
def connectionCheck(): 
	return "working Fine"

@app.route("/join_room")
def joinRoom():
	RegistrationToSvr.joinToGame()
	return "true"
	
@app.route("/init")
def arm():
	#motor
	pi.set_PWM_frequency(ESC_LEFT,500)
	pi.set_PWM_frequency(ESC_RIGHT,500)
	gpioController.gpio_PIN_PWM(ESC_LEFT, 1500) # stop
	gpioController.gpio_PIN_PWM(ESC_RIGHT, 1500) # stop
	pi.set_servo_pulsewidth(ESC_LEFT, INJORA35T_STOP)
	pi.set_servo_pulsewidth(ESC_RIGHT, INJORA35T_STOP)
	#weapon(esc)
	pi.set_PWM_frequency(ESC_WEAPON,50) # 20 times per a second.
	gpioController.gpio_PIN_PWM(ESC_WEAPON, 1500) # stop
	pi.set_servo_pulsewidth(ESC_WEAPON, INJORA35T_STOP)
	#weapon(servo)
	pi.set_PWM_frequency(SERVO_WEAPON_1,50) # 20 times per a second.
	pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	#camera
	pi.set_PWM_frequency(CAMERA_X,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_X,1500) #500(min) - 2500(max)
	pi.set_PWM_frequency(CAMERA_Y,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_Y,1500)
	time.sleep(100)
	return "ready"

#hit by other
@app.route("/damaged", methods = ['GET', 'POST'])
def damaged():
	ledController.setTargetBright(255,0,0)
	ledController.blinkingAndDimming(4)
	
#right wheel
@app.route("/motor_right")
def motorControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel"))*0.3 #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-INJORA35T_OFFSET_MIN_WORK_PWM-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		# pi.set_servo_pulsewidth(ESC_RIGHT, int(Clamp(1500-velocity*40,1100,1500)))
		gpioController.gpio_PIN_PWM(ESC_RIGHT, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel"))*0.3 #0~10 from mobile. 
		pwm = int(Clamp(INJORA35T_STOP+INJORA35T_OFFSET_MIN_WORK_PWM+velocity*INJORA35T_WIDTH
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
		velocity = int(request.args.get("vel"))*1.2 #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-INJORA35T_OFFSET_MIN_WORK_PWM-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		# pi.set_servo_pulsewidth(ESC_LEFT, int(Clamp(1500-velocity*40,1100,1500)))
		gpioController.gpio_PIN_PWM(ESC_LEFT, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel"))*1.2 #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP+INJORA35T_OFFSET_MIN_WORK_PWM+velocity*INJORA35T_WIDTH
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

#WEAPON1_blade
@app.route("/weapon1") #1500, 500 2500
def weapon1Control(): 
	state = request.args.get("state")
	if state == "left":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, int(Clamp(INJORA35T_STOP+10*100,500,2500)))
	if state == "right":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, int(Clamp(INJORA35T_STOP-10*100,500,2500)))
	elif state == "stop":
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	else: 
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	return "Checked: " + state

#Blade
@app.route("/esc_weapon")
def escWeaponControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		gpioController.gpio_PIN_PWM(ESC_WEAPON, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP+velocity*INJORA35T_WIDTH
			,INJORA35T_STOP
			,INJORA35T_STOP + (INJORA35T_WIDTH*10)))
		gpioController.gpio_PIN_PWM(ESC_WEAPON, pwm)
	elif state == "stop":
		gpioController.gpio_PIN_PWM(ESC_WEAPON, INJORA35T_STOP)
	else: 
		gpioController.gpio_PIN_PWM(ESC_WEAPON, INJORA35T_STOP)
	return ""
 
#kick_solenoid
@app.route("/kick_solenoid") #1500, 500 2500
def kickSolenoid(): 
	global isCharging
	state = request.args.get("state")
	if state == "run" and not isCharging:
		isCharging = True
		pi.write(KICK_SOLENOID, 1)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 1)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 1)
		solenoidStopTimer = Timer(0.15, kickSolenoidStop)
		solenoidStopTimer.start()
	elif state == "stop":
		isCharging = False
		pi.write(KICK_SOLENOID, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	else: 
		isCharging = False
		pi.write(KICK_SOLENOID, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	return "Checked: " + state

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

#little awkward api, but I'm quite sure that this is the best choice 
#untill we gets 'perfect lifecycle smartphone client'.
@app.route("/onusing")
def onUse():
	status = request.args.get("status")
	SVR_BASE_ADDR = 'http://onffworld.iptime.org:48080' #todo: https 보안 스트림으로의 업그레이드
	RESTFUL_EXPRESSION = '/rc/onuse'
	infos = {'type_of_rc':RegistrationToSvr.Getter().getMyType(),'serial_of_rc':RegistrationToSvr.getserial(),'on_use': status}
	response = requests.post(SVR_BASE_ADDR+RESTFUL_EXPRESSION, params=infos) #can be params, or simply json.
	# response = requests.post(SVR_BASE_ADDR+RESTFUL_EXPRESSION, data=infos)
	try:
		response.raise_for_status()
		if(response.status_code == 200 or response.status_code == 201): #good
			pass
			# print('all good!')
		else: #not good, but received anyway.
			pass
			# print('server alive but went wrong. maybe there are some mistaken things?')
		
	except requests.exceptions.HTTPError as e:
		print('bam! error occured while connecting to the static server')
	return status

def kickSolenoidStop():
	global isCharging
	isCharging = False
	pi.write(KICK_SOLENOID, 0)
	pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
	pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	# print('kick solenoid stop')

if __name__ == "__main__":
	cb = pi.callback(PRESS_SENSOR, pigpio.FALLING_EDGE, pressCallback)
	#cb.cancel() #no need to cancel.
	app.run(host="0.0.0.0")

