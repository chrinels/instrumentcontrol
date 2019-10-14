import time

import numpy as np

import visa
import VISAInstrument
from Stepper import PhidgetStepper


# VNA Settings
vna_conf = {'f_start': 2.3E+9, 'f_stop': 6.0E+9, 'nf_points': 7401, 'if_bw': 1.0E+3}

f = np.linspace(vna_conf['f_start'], vna_conf['f_stop'], vna_conf['nf_points'])
vna_conf['f'] = f


def do_measurement(vna, phidget, positions):
    print('\n################## STARTING MEASUREMENT ##################\n')

    n_positions = len(positions)
    first = True
    count = 0
    
    for pos in positions:
        count += 1
        print_status_bar(count, n_positions+2)
        
        # Move the antenna and Let the movement settle
        phidget.set_target_absolute_position(pos)
        phidget.wait_to_settle()
        time.sleep(0.5)

        measure_and_save(vna, pos)

        # Take to measurement sweeps on the first position to
        # enable SNR estimation in post-processing.
        if first:
            count += 1
            print_status_bar(count, n_positions+2)
            measure_and_save(vna, pos)
            first = False

    # MOVE THE ANTENNA to home position
    # This is just some kind of sanity check.
    # Tell the VNA to make the final sweep at pos 0.
    # Move the antenna and Let the movement settle.
    count += 1
    print_status_bar(count, n_positions+2)
    phidget.set_target_absolute_position(positions[0])
    phidget.wait_to_settle()
    time.sleep(0.5)

    measure_and_save(vna, positions[0])


def measure_and_save(instrument, pos):
    # Tell the VNA to make the sweep
    instrument.write('INIT1:IMM; *WAI')
    instrument.check_opc()

    hf = instrument.query_scattering_values()
    instrument.check_opc()
    instrument.error_checking()  # Error Checking after the data transfer

    # Use h = numpy.load(fname); f = h['f']; s21 = h['hf']
    np.savez_compressed('s21_{}_{}'.format(time.strftime('%Y%m%d_%H%M%S'), pos), hf=hf, f=vna_conf['f'])


def print_status_bar(c, n):
    print('\n################## {} {}/{} ##################'.format(time.strftime('%Y%m%d_%H%M%S'), c, n))


def delay_start(w_time=60):
    for t in range(w_time):
        print('.. in {} seconds'.format(w_time-t))
        time.sleep(1)


def setup_instrument(vna):
    # Set up the frequency range, and # of sweep points
    vna.write('SENS1:FREQ:STAR ' + str(vna_conf['f_start']))
    vna.write('SENS1:FREQ:STOP ' + str(vna_conf['f_stop']))
    vna.write('SENS1:BWID ' + str(vna_conf['if_bw']))
    vna.write('SENS1:SWE:POIN ' + str(vna_conf['nf_points']))

    vna.check_opc()
    vna.error_checking()

    # Change the VISA connection timeout
    vna.write('SENS1:SWE:TIME:AUTO 1')
    estimated_sweep_time = vna.query('SENS1:SWE:TIME?')
    vna.visa_connection_timeout(float(estimated_sweep_time)*1E+3 + 1000)   # Milliseconds!

    # Turn off continous sweeps for all channels
    vna.write('INIT:CONT:ALL OFF')
    
    # Stop updating the instrument display
    vna.write('SYST:DISP:UPD OFF')

    vna.check_opc()
    vna.error_checking()


if __name__ == '__main__':   

    # Open a connection to the Phidget stepper
    ph_stepper = PhidgetStepper(stepper_sn=117906)
    positions = range(0, 801, 1)

    try:
        # Rohde & Schwarz ZNB8 VNA
        vna = VISAInstrument('TCPIP::169.254.86.175::hislip0::INSTR', debug=True)
        setup_instrument(vna)

        # Do measurement loop
        delay_start(5)
        do_measurement(vna, ph_stepper, positions)

        # Set VNA to Sweep on all channels.
        # Turn on the VNA display.
        vna.write('INIT:CONT:ALL ON')
        vna.write('SYST:DISP:UPD ON')

    except visa.VisaIOError as e:
        print('\x1b[1;37;41m Visa IO Error\x1b[0m {}\n{}'.format(resource, e.description))

    except visa.LibraryError as e:
        print('\x1b[1;37;41m VISA Library Error\x1b[0m\n{}'.format(e.message))

    except visa.VisaTypeError as e:
        print('\x1b[1;37;41m VISA Type Error\x1b[0m\n{}'.format(e.message))

    except VISAExtension.InstrumentErrorException as e:
        print('\x1b[1;37;41m Instrument error(s) occurred:\x1b[0m\n{}'.format(e.message))
