import time

import numpy as np

import visa
import VISAExtension
from Stepper import PhidgetStepper


debug = True

resource = 'TCPIP::169.254.86.175::hislip0::INSTR'  # Rohde & Schwarz ZNB8 VNA
f_start = 2.3E+9
f_stop = 6.0E+9
n_f_points = 7401  # Number of frequency points between
f = np.linspace(f_start, f_stop, n_f_points)
if_bw = 1.0E+3     # IF Bandwidth

phidget_serial_num = 117906
ph_stepper = PhidgetStepper(stepper_sn=phidget_serial_num)
positions = range(0, 801, 1)


def measure_and_save(instrument, pos):
    # Tell the VNA to make the sweep
    instrument.ext_write('INIT1:IMM; *WAI')
    instrument.ext_wait_for_opc()

    hf = instrument.ext_query_values()
    instrument.ext_wait_for_opc()
    instrument.ext_error_checking()  # Error Checking after the data transfer

    # Use h = numpy.load(fname); f = h['f']; s21 = h['hf']
    np.savez_compressed('s21_{}_{}'.format(time.strftime('%Y%m%d_%H%M%S'), pos), hf=hf, f=f)


# Connect to the VNA and configure the measurement settings.
rm = visa.ResourceManager()

try:
    vna = rm.open_resource(resource)
    vna.ext_set_debug(True)
    vna.ext_set_resource(resource)
    vna.write_termination = '\n'

    vna.ext_query('*IDN?')                  # Query the Identification string
    vna.ext_clear_status()                  # Clear instrument io buffers and status
    vna.timeout = 1500

    vna.ext_write('FORMat:BORDer?')         # Ask instrument for Byte Order, Big or Little Endian
    vna.ext_read()                          # SWAP = Little Endian, NORM = Big Endian

    # Set up the frequency range, and # of sweep points
    vna.ext_write('SENS1:FREQ:STAR ' + str(f_start))
    vna.ext_write('SENS1:FREQ:STOP ' + str(f_stop))
    vna.ext_write('SENS1:BWID ' + str(if_bw))
    vna.ext_write('SENS1:SWE:POIN {}'.format(str(n_f_points)))

    vna.ext_wait_for_opc()
    vna.ext_error_checking()

    vna.ext_write('SENS1:SWE:TIME:AUTO 1')
    estimated_sweep_time = vna.ext_query('SENS1:SWE:TIME?')

    vna.timeout = float(estimated_sweep_time)*1E+3 + 1000   # Milliseconds1

    # SETUP THE TRACES HERE!

    vna.ext_write('INIT:CONT:ALL OFF')    # Turn off sweeps for all channels
    vna.ext_write('SYST:DISP:UPD OFF')    # Stop updating the instrument display
    vna.ext_wait_for_opc()
    vna.ext_error_checking()

    # Perform measurement: measure channel -> move Rx -> ...
    print('\n################## STARTING MEASUREMENT ##################\n')
    w_time = 20
    for t in range(w_time):
        print('.. in {} seconds'.format(w_time-t))
        time.sleep(1)

    first = True
    count = 0
    for pos in positions:

        count += 1
        print('\n################## {}/{} ##################'.format(count, len(positions)+2))

        # Move the antenna and Let the movement settle
        ph_stepper.set_target_absolute_position(pos)
        ph_stepper.wait_to_settle()
        time.sleep(0.5)

        measure_and_save(vna, pos)

        if first:
            count += 1
            print('\n################## {}/{} ##################'.format(count, len(positions)+2))
            measure_and_save(vna, pos)
            first = False

    count += 1
    print('\n################## {}/{} ##################'.format(count, len(positions)+2))
    # MOVE THE ANTENNA to home position
    # Tell the VNA to make the final sweep at pos 0
    # Move the antenna and Let the movement settle
    ph_stepper.set_target_absolute_position(positions[0])
    ph_stepper.wait_to_settle()
    time.sleep(0.5)

    measure_and_save(vna, positions[0])

    # Clean up. Set VNA to Sweep on all channels.
    # Turn on the VNA display.
    # Close connection to VNA.
    vna.ext_write('INIT:CONT:ALL ON')
    vna.ext_write('SYST:DISP:UPD ON')

    print('\nDisconnecting from:\n{}\tIDN:{}'.format(resource, vna.query('*IDN?')))
    vna.ext_clear_status()
    vna.close()

    ph_stepper.close()

    time.sleep(1)


except visa.VisaIOError as e:
    print('\x1b[1;37;41m Visa IO Error\x1b[0m {}\n{}'.format(resource, e.description))

except visa.LibraryError as e:
    print('\x1b[1;37;41m VISA Library Error\x1b[0m\n{}'.format(e.message))

except visa.VisaTypeError as e:
    print('\x1b[1;37;41m VISA Type Error\x1b[0m\n{}'.format(e.message))

except VISAExtension.InstrumentErrorException as e:
    print('\x1b[1;37;41m Instrument error(s) occurred:\x1b[0m\n{}'.format(e.message))
