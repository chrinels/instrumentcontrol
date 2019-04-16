import visa
import VISAExtension

debug = True

resource = 'TCPIP::169.254.86.175::hislip0::INSTR'  # Rohde & Schwarz ZNB8 VNA
f_start = 2.0E+9
f_stop = 8.0E+9
n_f_points = 401    # Number of frequency points between
if_bw = 10.0E+3     # IF Bandwidth


# Connect to the VNA and configure the measurement settings.
rm = visa.ResourceManager()

try:
    vna = rm.open_resource(resource)
    vna.ext_set_debug(True)
    vna.ext_set_resource(resource)
    vna.write_termination = '\n'

    idn = vna.ext_query('*IDN?')            # Query the Identification string
    print('Connected to:\n{}\tIDN:{}\n'.format(resource, idn.rstrip()))

    vna.ext_clear_status()                  # Clear instrument io buffers and status
    vna.timeout = 1500

    vna.ext_write('FORMat:BORDer?')         # Ask instrument for Byte Order, Big or Little Endian
    vna.ext_read()                          # SWAP - Little Endian, NORM - Big Endian

    # Set up the frequency range, and # of sweep points
    vna.ext_write('SENS1:FREQ:STAR ' + str(f_start))
    vna.ext_write('SENS1:FREQ:STOP ' + str(f_stop))
    vna.ext_write('SENS1:BWID ' + str(if_bw))
    vna.ext_write('SENS1:SWE:POIN {}'.format(str(n_f_points)))

    vna.ext_wait_for_opc()
    vna.ext_error_checking()

    vna.ext_write('SENS1:SWE:TIME:AUTO 1')
    sweep_time = vna.ext_query('SENS1:SWE:TIME?')

    vna.timeout = float(sweep_time)*1E3 + 2000

    # SETUP THE TRACES HERE!

    vna.ext_write('INIT:CONT:ALL OFF')    # Turn off sweeps for all channels
    vna.ext_write('SYST:DISP:UPD OFF')    # Stop updating the instrument display
    vna.ext_wait_for_opc()
    vna.ext_error_checking()

    # Perform measurement: measure channel -> move Rx -> ...
    for _ in range(100):

        # Tell the VNA to make the sweep
        vna.ext_write('INIT1:IMM; *WAI')
        vna.ext_wait_for_opc()

        print('Fetching waveform in ASCII format... ')
        vna.ext_write('CALC:DATA? SDAT')
        waveformASCII = vna.ext_read()
        print('ASCII data samples read: {}'.format(len(waveformASCII)/2))
        vna.ext_error_checking()  # Error Checking after the data transfer

    # Clean up. Set VNA to Sweep on all channels.
    # Turn on the VNA display.
    # Close connection to VNA.
    vna.ext_write('INIT:CONT:ALL ON')
    vna.ext_write('SYST:DISP:UPD ON')

    print('\nDisconnecting from:\n{}\tIDN:{}'.format(resource, idn))
    vna.ext_clear_status()
    vna.close()

except visa.VisaIOError as e:
    print('VisaIOError {}\n{}'.format(resource, e.description))

except visa.LibraryError as e:
    print('VISA Library Error\n{}'.format(e.message))

except visa.VisaTypeError as e:
    print('VISA Type Error\n{}'.format(e.message))

except VISAExtension.InstrumentErrorException as e:
    print('Instrument error(s) occurred:\n{}'.format(e.message))
