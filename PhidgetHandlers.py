

def on_attach_handler(channel):
    channel.setDataInterval(250)  # 250 ms
    channel.setRescaleFactor(1 / 3200)  # 1 now equals full rotation
    channel.setVelocityLimit(1.5)
    channel.setEngaged(True)
    print('\x1b[1;34mPhidget::SN::{}\x1b[0m < Attached'.format(channel.getDeviceSerialNumber()))


def on_detach_handler(channel):
    channel.setEngaged(False)


def on_error_handler(channel, error_code, error_string):
    print('\x1b[1;34mPhidget::SN::{}\x1b[0m < raised error {}: {}\n'.format(channel.getDeviceSerialNumber(),
                                                                            error_code, error_string))


def on_position_change_handler(channel, position, debug=False):
    if debug:
        print('\x1b[1;34mPhidget::SN::{}\x1b[0m < position {:8.4f}\t={:8.4f} mm'.format(channel.getDeviceSerialNumber(),
                                                                                        position, position * 2))
