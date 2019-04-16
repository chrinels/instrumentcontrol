import visa
import numpy as np


# Define helper functions for the VNA.
# Just makes it easier to enable/disable debug output,
# and makes the measurement script easier to read.
#
# This file is heavily inspired by R&S VISAresourceExtensions.py,
# especially the ext_check_error_queue and ext_error_checking methods.


class InstrumentErrorException(Exception):
    def __init__(self, errors):
        # Call the base class constructor with the parameters it needs
        message = ''
        if errors is not None and len(errors) > 0:
            message = '\n'.join(errors)
        super(InstrumentErrorException, self).__init__(message)


# Clears the instrument io buffers and status
def ext_clear_status(instrument):
    instrument.clear()
    instrument.query('*CLS;*OPC?')


visa.Resource.ext_clear_status = ext_clear_status


def ext_write(instrument, scpi_cmd):
    if instrument.ext_debug:
        print('{} > {}'.format(instrument.ext_resource.rstrip(), scpi_cmd))
    instrument.write(scpi_cmd)


visa.Resource.ext_write = ext_write


def ext_query(instrument, scpi_cmd):
    if instrument.ext_debug:
        print('{} > {}'.format(instrument.ext_resource.rstrip(), scpi_cmd))
    resp = instrument.query(scpi_cmd)
    if instrument.ext_debug:
        print('{} < {}'.format(instrument.ext_resource.rstrip(), resp.rstrip()))
    return resp.rstrip()


visa.Resource.ext_query = ext_query


def ext_read(instrument):
    response = instrument.read()
    if instrument.ext_debug:
        print('{} < {}'.format(instrument.ext_resource.rstrip(), response.rstrip()))
    return response.rstrip()


visa.Resource.ext_read = ext_read


def ext_check_opc(instrument):
    instrument.ext_write('*OPC?')
    return instrument.ext_read()


visa.Resource.ext_check_opc = ext_check_opc


def ext_wait_for_opc(instrument):
    instrument.ext_check_opc()


visa.Resource.ext_wait_for_opc = ext_wait_for_opc


def ext_set_debug(instrument, debug=False):
    print('{} < Setting debug to {}'.format('', str(debug)))
    instrument.ext_debug = debug


visa.Resource.ext_set_debug = ext_set_debug


def ext_set_resource(instrument, res='INSTRUMENT'):
    print(' < Setting ext_set_resource to {}'.format(res))
    instrument.ext_resource = res


visa.Resource.ext_set_resource = ext_set_resource


# Function implemented as defined in the Instrument Error Checking chapter
def ext_check_error_queue(instrument):
    errors = []
    stb = int(instrument.query('*STB?'))
    if (stb & 4) == 0:
        return errors

    while True:
        response = instrument.query('SYST:ERR?')
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


visa.Resource.ext_check_error_queue = ext_check_error_queue


# This function calls ReadErrorQueue and raise InstrumentErrorException if any error occurred
# If you want to only check for error without generating the exception, use the ext_check_error_queue() function
def ext_error_checking(instrument):
    errors = instrument.ext_check_error_queue()
    if errors is not None and len(errors) > 0:
        raise InstrumentErrorException(errors)


visa.Resource.ext_error_checking = ext_error_checking


def ext_query_values(instrument):
    instrument.ext_write('CALC:DATA? SDAT')
    resp = instrument.read()
    resp = resp.rstrip()
    resp = resp.split(',')
    resp_numpy = np.array(resp, dtype=np.float)
    resp_numpy_comp = resp_numpy[:-1:2] + 1j * resp_numpy[1::2]
    print('{} < Saved {} complex values'.format(instrument.ext_resource.rstrip(), len(resp_numpy_comp)))
    return resp_numpy_comp


visa.Resource.ext_query_values = ext_query_values
