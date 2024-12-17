# Install circuitpython via thonny/bootsel
# https://circuitpython.org/libraries - download zip, unzip,
#  grab adafruit_hid folder, lis3dh.mpy and adafruit_bus_device folder and put into /lib folder on pico
# wire up accelerometer - see github for diagram.
# Install accelerometer and pico in 3d printed phone case.
# install mirrors in 3d printed case
# save this code to code.py to auto run
# Notes on operation - mouse turns on/off via button on 16/gnd or shake on/off
#   Tilt head to move mouse. mouse click w/ head bop


"""CircuitPython Essentials HID Mouse example"""
import time
import board
import digitalio
from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.mouse import Mouse
import busio
import adafruit_lis3dh

#Parameters to set based on your experience
shakeThreshold = 14 #higher = more shake needed to start mouse
tapThreshold = 80 #0-120

# Onboard LED setup - on when mouse in is use
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

# mouse setup
mouse = Mouse(usb_hid.devices)
move_mouse_flag = False
ref_x = 0
ref_y = 0
ref_z = 0

# button setup - may not be used in your setup. Only if you want a hardware on/off for mouse
button = DigitalInOut(board.GP16)
button.switch_to_input(pull=Pull.UP)
button_state = 1
prev_button_state = 1

# Hardware I2C setup for accelerometer
i2c = busio.I2C(board.GP1,board.GP0)  # uses board.SCL and board.SDA
int1 = digitalio.DigitalInOut(board.GP2)  # Set this to the correct pin for the interrupt. This is only soldered pin
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

# Set range of accelerometer (can be RANGE_2_G, RANGE_4_G, RANGE_8_G or RANGE_16_G).
lis3dh.range = adafruit_lis3dh.RANGE_2_G
#set_tap (number of taps (head bobs) to activate, force required (how hard to bop head)).  Once on, this controls mouse clicks
lis3dh.set_tap(1, tapThreshold)
initial_tap_flag = False
shake_flag = False

def readAccelerometer():
  #read accelerometer, print pretty values adjusted for gravity, pass raw floats back
  x, y, z = [value / adafruit_lis3dh.STANDARD_GRAVITY for value in lis3dh.acceleration]
  #print("x = %0.3f G, y = %0.3f G, z = %0.3f G" % (x, y, z))
  return x,y,z

def moveMouseCalc(inst_float,ref_float):
  #determine how many pixels to move the mouse. 0 out small changes, magnify large ones
  return_int = 0
  if abs(inst_float - ref_float) > 0.05:
    if inst_float - ref_float > 0:
      if inst_float - ref_float > 0.4:
        return_int = 50 #number of pixels to move
      elif inst_float - ref_float > 0.3:
        return_int = 30 #number of pixels to move
      elif inst_float - ref_float > 0.2:
        return_int = 16
      elif inst_float - ref_float > 0.1:
        return_int = 8
      elif inst_float - ref_float > 0.05:
        return_int = 2
    if inst_float - ref_float < 0:
      if inst_float - ref_float < -0.4:
        return_int = -50
      elif inst_float - ref_float < -0.3:
        return_int = -30
      elif inst_float - ref_float < -0.2:
        return_int = -16
      elif inst_float - ref_float < -0.1:
        return_int = -8
      elif inst_float - ref_float < -0.05:
        return_int = -2
  return return_int

while True:
  #original on/off was button click, but can instead use shake. Give both options
  prev_button_state = button_state
  button_state = button.value
  if prev_button_state != button_state:
    time.sleep(0.1) # Debounce delay
  if lis3dh.shake(shake_threshold=shakeThreshold):
    shake_flag = True
  if shake_flag == True or (prev_button_state == 1 and button_state == 0):
    print("Shaken or pressed. Change state of mouse on/off")
    move_mouse_flag = not move_mouse_flag
    led.value = not led.value
    #initial_tap_flag = True #a shake also triggers a tap, ignore the first one
    if shake_flag == True:
      time.sleep(0.5) #wait for head shake to complete
    #get initial accelerometer values as reference for mouse moves
    ref_x,ref_y,ref_z = readAccelerometer()
    shake_flag = False

  if move_mouse_flag == True:
    #turned on mouse
    
    #check for a click first
    if lis3dh.tapped:
      if initial_tap_flag:
        #ignore initial tap+shake that turns us on, don't actually click
        print("Initial tap coupled with shake, ignore")
        initial_tap_flag = False
      else:
        print("Tapped! Click mouse")
        mouse.click(Mouse.LEFT_BUTTON)
        time.sleep(0.01)
    else:
      #capture accelerometer changes and move mouse accordingly
      inst_x,inst_y,inst_z = readAccelerometer()
      moveXPix=moveMouseCalc(inst_x,ref_x)
      moveYPix=moveMouseCalc(inst_y,ref_y)
      #print("x: ",inst_x," xref: ",ref_x," diff:",str(inst_x-ref_x)," y: ",inst_y," ref_y:",ref_y," diff:",str(inst_y-ref_y))
      #print(moveXPix," ",moveYPix)
      mouse.move(x=moveYPix,y=-moveXPix) #had to reverse values to accomodate accelerometer mounting
    