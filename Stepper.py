#
# Requires:
# - an installation of NI-VISA
# - PyVISA
# - Phidget22 drivers
# - Phidget22Python
#
import time

from Phidget22.Devices.Stepper import *
from Phidget22.Phidget import *

import PhidgetHandlers

'''
#
# Configure and open the phidget stepper.
# Software Objects for the Phidget 1063 PhidgetStepper Bipolar 1-Motor
# --------------------------------------------------
# Device	                Object Name	    Channel
# --------------------------------------------------
# Stepper Motor Output	    Stepper	        0
# Motor Current Sense	    CurrentInput	0
# Digital Inputs	        DigitalInput	0 - 3
# --------------------------------------------------
#
#
# Set up parameters for measurement
#
# @param debug: True/False. Print out debug messages
#
# @param stepper_sn: is the Serial number for the phidget device
#
#
# Define event handlers for the phidget stepper.
#
# on_attach_handler: Event when phidget is found/connected
# on_detach_handler: Event when phidget is disconnected
# on_error_handler: Event when phidget sends error messages
# on_position_change_handler: When phidget sends position updates
#
'''


class PhidgetStepper:

    def __init__(self, stepper_sn, debug=False):
        try:
            self.debug = debug
            self.channel = Stepper()
            self.channel.setDeviceSerialNumber(stepper_sn)
            self.channel.setIsHubPortDevice(False)
            self.channel.setChannel(0)

            self.channel.setOnAttachHandler(PhidgetHandlers.on_attach_handler)
            self.channel.setOnDetachHandler(PhidgetHandlers.on_detach_handler)
            self.channel.setOnErrorHandler(PhidgetHandlers.on_error_handler)
            self.channel.setOnPositionChangeHandler(PhidgetHandlers.on_position_change_handler)

            self.channel.openWaitForAttachment(10000)
        except PhidgetException as e:
            print('\x1b[1;31mPhidget::SN::{}\x1b[0m <> {}'.format(stepper_sn, e))

    def __del__(self):
        self.close()

    def _get_device_str(self):
	    return str('\x1b[1;34mPhidget::SN::{}\x1b[0m'.format(self.channel.getDeviceSerialNumber()))

    def close(self):
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m > Closing channel {}'.format(self.channel.getDeviceSerialNumber(),
                                                                             self.channel.getChannel()))
        self.channel.close()

    def set_target_absolute_position(self, position):
        # One full rotation is 2 mm movement along the rail
        shaft_conversion = 1/2
        self.channel.setTargetPosition(position*shaft_conversion)

    def wait_to_settle(self):
        is_moving = self.channel.getIsMoving()

        while is_moving:
            time.sleep(0.01)
            is_moving = self.channel.getIsMoving()

        position = self.channel.getPosition()
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m < Position {:8.4f}\t<=>\t{:8.4f} mm'.format(
            self.channel.getDeviceSerialNumber(),
            position, position * 2))

        return is_moving

    def print_movement_info(self):
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m < minAcceleration {:8.4f}'.format(
            self.channel.getDeviceSerialNumber(),
            self.channel.getMinAcceleration()))
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m < maxAcceleration {:8.4f}'.format(
            self.channel.getDeviceSerialNumber(),
            self.channel.getMaxAcceleration()))        
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m < velocityLimit {:8.4f}'.format(
            self.channel.getDeviceSerialNumber(),
            self.channel.getVelocityLimit()))        


if __name__ == '__main__':

    phidget_serial_num = 117906
    ph_stepper = PhidgetStepper(stepper_sn=phidget_serial_num)

    ph_stepper.print_movement_info()

    ph_stepper.set_target_absolute_position(-800)
    ph_stepper.wait_to_settle()

    ph_stepper.close()
