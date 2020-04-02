import visa
import numpy as np


class SCPICommands:

    """
    The Standard Commands for Programmable Instrumentation (SCPI)

    Standard commands that all SCPI compliant instruments
    have implemented with defined behaviour.
    """
    CLS = "*CLS"    # - / no query        Clear status
    ESE = "*ESE"    # 0..255              Event status enable register
    ESR = "*ESR?"   # query only          Event status read
    IDN = "*IDN?"   # query only          Instrument identification
    IST = "*IST?"   # query only          IST flag (0|1)
    OPC = "*OPC"    # -                   Operation complete
    OPCQ = "*OPC?"  # -                   Operation complete Query
    OPT = "*OPT?"   # query only          Option identification query
    PCB = "*PCB"    # 0..30 / no query    Pass control back
    PRE = "*PRE"    # 0..255              Parallell poll Register Enable
    PSC = "*PSC"    # 0 | 1               Power on status clear
    RST = "*RST"    # - / no query        Reset instrument to default
    SRE = "*SRE"    # 0..255              Service Request Enable
    STB = "*STB?"   # query only          Status Byte Query
    TRG = "*TRG"    # - / no query        Trigger
    WAI = "*WAI"    # - / no query        Wait to continue


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

    [2020-04-02] Links working
    https://www.rohde-schwarz.com/se/applications/using-r-s-forum-application-for-instrument-remote-control-application-note_56280-50946.html
    https://www.rohde-schwarz.com/se/driver-pages/remote-control/why-visa-_231254.html
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

        if self.debug:
            self.__debug_string(response)

        return response.rstrip()

    def write(self, scpi_command):
        if self.debug:
            self.__debug_string(scpi_command)

        self.instrument.write(scpi_command)

    def query(self, scpi_command):
        if self.debug:
            self.__debug_string(scpi_command)

        response = self.instrument.query(scpi_command)

        if self.debug:
            self.__debug_string(response)

        return response.rstrip()

    def idn(self):
        return self.query(SCPICommands.IDN)

    def clear_status(self):
        """
        Clears the instrument io buffers and status
        :return:
        """
        self.instrument.clear()
        self.query(SCPICommands.CLS)
        self.query(SCPICommands.OPCQ)

    def reset(self):
        self.write(SCPICommands.RST)

    def check_opc(self):
        self.write('*OPC?')
        return self.read()

    def check_error_queue(self):
        """
        Function implemented as defined in the Instrument Error Checking chapter
        :return:
        """
        errors = []
        stb = int(self.query(SCPICommands.STB))
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
            vna.write('INIT1:IMM')
            vna.write(SCPICommands.WAI)

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

    except AttributeError as e:
        print('Attribute error(s) occurred:\n{}'.format(e.message))
