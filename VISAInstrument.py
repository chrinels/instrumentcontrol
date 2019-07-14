import visa
import numpy as np


class VISAInstrumentErrorException(Exception):
    def __init__(self, errors):
        # Call the base class constructor with the parameters it needs
        message = ''
        if errors is not None and len(errors) > 0:
            message = '\n'.join(errors)
        super(VISAInstrumentErrorException, self).__init__(message)


class VISAInstrument:
    """
    This class is heavily inspired by R&S VISAresourceExtensions.py,
    especially the check_error_queue and error_checking methods.
    """

    def __init__(self, resource, timeout=1500.0, write_termination='\n', debug=False):
        """

        :param resource:
        :param timeout:
        :param write_termination:
        :param debug:
        """
        self.debug = debug
        self.resource = resource
        self.rm = visa.ResourceManager()
        self.instrument = self.rm.open_resource(resource)
        self.visa_connection_timeout(timeout)
        self.visa_write_termination(write_termination)
        self.clear_status()

        print('Connected to:\n{}\tIDN:{}\n'.format(self.resource, self.idn()))

    def __del__(self):
        print('\nDisconnecting from:\n'
              '{}\tIDN:{}'.format(self.resource, self.idn()))
        self.clear_status()
        self.instrument.close()

    @property
    def debug(self):
        return self.__debug

    @debug.setter
    def debug(self, val):
        if not isinstance(val, bool):
            raise VISAInstrumentErrorException('Wrong type.')
        self.__debug = val

    def visa_write_termination(self, term='\n'):
        self.instrument.write_termination = term

    def visa_connection_timeout(self, timeout=1500.):
        self.instrument.timeout = timeout

    def get_byte_order(self):
        self.write('FORMat:BORDer?')    # Ask instrument for Byte Order, Big or Little Endian
        return self.read()              # SWAP - Little Endian, NORM - Big Endian

    def __debug_string(self, message):
        print('[{}]\t{}'.format(self.resource, message.rstrip()))

    def read(self):
        response = self.instrument.read()
        if self.debug: self.__debug_string(response)
        return response.rstrip()

    def write(self, scpi_command):
        if self.debug: self.__debug_string(scpi_command)
        self.instrument.write(scpi_command)
        self.check_opc()

    def query(self, scpi_command):
        if self.debug: self.__debug_string(scpi_command)
        response = self.instrument.query(scpi_command)
        if self.debug: self.__debug_string(response)
        self.check_opc()
        return response.rstrip()

    def idn(self):
        return self.query('*IDN?')

    def clear_status(self):
        """
        Clears the instrument io buffers and status
        :return:
        """
        self.instrument.clear()
        self.query('*CLS;*OPC?')

    def reset(self):
        self.write('*RST')

    def check_opc(self):
        self.write('*OPC?')
        return self.read()

    def check_error_queue(self):
        """
        Function implemented as defined in the Instrument Error Checking chapter
        :return:
        """
        errors = []
        stb = int(self.query('*STB?'))
        if (stb & 4) == 0:
            return errors

        while True:
            response = self.query('SYST:ERR?')
            if '"no error"' in response.lower():
                break
            errors.append(response)
            if len(errors) > 50:
                # safety stop
                errors.append('Cannot clear the error queue')
                break
        if len(errors) == 0:
            return None
        else:
            return errors

    def error_checking(self):
        """
        This function calls ReadErrorQueue and raise InstrumentErrorException
        if any error occurred.
        If you want to only check for error without generating the exception,
        use the check_error_queue() function.
        :return:
        """
        errors = self.check_error_queue()
        if errors is not None and len(errors) > 0:
            raise VISAInstrumentErrorException(errors)

    def get_freq_star(self):
        return self.write('SENS1:FREQ:STAR?')

    def set_freq_star(self, val):
        if not isinstance(val, int):
            raise VISAInstrumentErrorException('')
        if val < 0:
            raise VISAInstrumentErrorException('')

        self.write('SENS1:FREQ:STAR ' + str(val))

    def query_scattering_values(self):
        self.write('CALC:DATA? SDAT')
        resp = self.read()
        resp = resp.rstrip()
        resp = resp.split(',')
        resp_numpy = np.array(resp, dtype=np.float)
        resp_numpy_comp = resp_numpy[:-1:2] + 1j * resp_numpy[1::2]
        self.error_checking()

        if self.debug:
            print('{} < Saved {} complex values'.format(self.resource.rstrip(),
                                                        len(resp_numpy_comp)))
        return resp_numpy_comp


if __name__ == '__main__':
    try:
        # Rohde & Schwarz ZNB8 VNA over Ethernet
        vna = VISAInstrument('TCPIP::169.254.86.175::hislip0::INSTR', debug=True)
        vna.reset()

        # Set up the frequency range, and # of sweep points
        vna.write('SENS1:FREQ:STAR 2.0E+9')
        vna.write('SENS1:FREQ:STOP 8.0E+9')
        vna.write('SENS1:BWID 10.0E+3')  # IF Bandwidth

        vna.write('SENS1:SWE:POIN 401')  # Number of frequency points between
        vna.write('SENS1:SWE:TIME:AUTO 1')

        sweep_time = vna.query('SENS1:SWE:TIME?')
        vna.visa_connection_timeout(float(sweep_time)*1E3 + 2000.0)

        # SETUP THE TRACES HERE!

        vna.write('INIT:CONT:ALL OFF')    # Turn off sweeps for all channels
        vna.write('SYST:DISP:UPD OFF')    # Stop updating the instrument display
        vna.error_checking()

        # Perform measurement: measure channel -> move Rx -> ...
        for _ in range(100):

            # Tell the VNA to make the sweep
            vna.write('INIT1:IMM; *WAI')
            vna.query_scattering_values()

        # Set VNA to Sweep on all channels.
        # Turn on the VNA display.
        vna.write('INIT:CONT:ALL ON')
        vna.write('SYST:DISP:UPD ON')

    except visa.VisaIOError as e:
        print('VisaIOError\n{}'.format(e.description))

    except visa.LibraryError as e:
        print('VISA Library Error\n{}'.format(e.message))

    except visa.VisaTypeError as e:
        print('VISA Type Error\n{}'.format(e.message))

    except VISAInstrumentErrorException as e:
        print('Instrument error(s) occurred:\n{}'.format(e.message))
