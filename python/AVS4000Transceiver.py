#!/usr/bin/env python

import socket
import json
import array
import threading
import time
import struct
import logging
import Vita49


RXType = 'RX'
TXType = 'TX'

COMPLEXOutputFormat  = 'ComplexData'
VITA49OutputFormat   = 'Vita49Data'

BASE_CONTROL_PORT = 12900
BASE_RECEIVE_PORT = 12700

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s @ %(lineno)d')

module_logger = logging.getLogger('AVS4000Transceiver')


"""
RX Use Cases:
  Initialize:
    Prereq:
        Object created.
    
    Steps:
        Ensure that the data socket is closed and not running:
            rxdata
                ConEnable = false
                Run       = false        
            
            rx
                ???? 
        
  Tune:
    Prereq:
        Device has been initialized
        
    Reference:
        deviceSetTuning - REDHAWK calls this method prior to enabling the device.
        
    Steps:
        Ensure that the data socket is enabled and running
            rxdata
                ConEnable = false
                Run       = false
                useV49    = <true, false> # depends on what user configured, should this be configurable at run time?
            
        Ensure that the 
            rx
                SampleRate = <SR>
                Freq       = <FREQ>
                GainMode   = 'SlowAGC'      # Pulled from a REDHAWK property
                StartMode  = 'Immediate'    # Pulled from a REDHAWK property
                LBMode     = 'Auto'         # Pulled from a REDHAWK property
            
  Enable:
    Prereq:
       The device has been tuned.
       
    Reference:
        deviceEnable - REDHAWK calls this to turn the data on.
    
    Steps:
        Enable the data socket 
            rxdata.ConEnable = True
        
        Connect to the data_socket
        
        Turn the data on 
            rxdata.Run       = True

  Disable:
    Prereq:
        The device has been Enabled.
        
    Steps:
        Ensure data socket is off and no data is flowing:
            rxdata.ConEnable = false
            rxdata.run       = false


  changeFreq
    Prereq:
        The device has been Enabled
        
    Steps:
        rx:
            Freq = <FREQ>
  
  changeSampleRate
    Prereq:
        The device has been Enabled
    
    Steps:
        rx:
            SampleRate = <SR>
  
  changeGain
    Prereq:
        The device has been Enabled
        The device's GainMode is "Manual
    
    Steps:
        rx:
            Gain = <GAIN>
  
  changeGainMode
    Prereq:
        The device ahs been Enabled
        
    Steps:
        rx:
            GainMode = <MODE>
    
"""

class Master:
    """
    This class encapsulates the information assoicated with the Master group defined by the
    AVS4000 API.
    """
    def __init__(self, the_sample_rate, the_sample_rate_mode):
        """
        Represents the master group of the AVS4000

        :param the_sample_rate:       The actual sample_rate, 0 means unknown
        :param the_sample_rate_mode:  String representing mode {"Auto", "Manual"}
        """
        self.sample_rate_      = the_sample_rate
        self.sample_rate_mode_ = the_sample_rate_mode

    def __str__(self):
        the_str = "Master:\n"\
                  "  sample_rate      <{}>\n"\
                  "  sample_rate_mode <{}>".format\
            (
                self.sample_rate_,
                self.sample_rate_mode_
            )

        return the_str

    def sample_rate(self):
        return self.sample_rate_

    def sample_rate_mode(self):
        return(self.sample_rate_mode_)

class RxStatus:
    """
    This class encapsulates the status returned from a AVS4000 transciever

    """
    def __init__(self, the_string=""):
        """

        :param the_string:
        """
        self.overflow_     = -1
        self.gain_         = 0.0
        self.overflow_     = -1
        self.rate_         = -1
        self.sample_count_ = -1

        try:
            the_json = json.loads(the_string)
        except Exception:
            return

        if len(the_json) == 2:
            the_object = the_json[1]

            if the_object.has_key('rxstat'):
                the_rxstat = the_json['rxstat']

                if the_rxstat.haskey('Gain'):
                    self.gain_ = the_json['rx']

                if the_rxstat.haskey('Overflow'):
                    self.overflow_ = the_rxstat['Overflow']

                if the_rxstat.haskey('Rate'):
                    self.rate_ = the_rxstat['Rate']

                if the_rxstat.haskey('Sample'):
                    self.sample_count_ = the_rxstat['Sample']

    def __str__(self):
        """
        This method will provide a string representation of the RxStatus object.

        :return:
            A string.
        """
        the_string = \
            "Gain:         <{}>\n" \
            "Overflow:     <{}>\n" \
            "Rate:         <{}>\n" \
            "Sample Count: <{}>\n".format\
                (
                    self.gain_,
                    self.overflow_,
                    self.rate_,
                    self.sample_count_
                )

        return the_string

    def gain(self):
        """
        Accessor method, returns the current gain

        :return:
          integer representing the gain value.
        """
        return(self.gain_)

    def overflow(self):
        """
        Accessor method, that returns the overflow value,

        NOTE:
           A value of 0 represents no overflow.

        :return:
          integer representing the overflow
        """
        return self.overflow_

    def rate(self):
        """
        Accessor method, that returns the current rate value

        :return:

        """
        return self.rate_

    def sample_count(self):
        """
        Accessor method, that returns the current sample_count sent.

        :return:
            An integer representing the sample_count.
        """
        return self.sample_count_


class DeviceManager:
    """
    This class represents the Device Manager (DM) provided by the AVS4000 daemon.  The DM, is
    responsible for manageing all of the Device Controllers (DC)'s present.
    """

    def __init__(self, the_host='localhost', the_port=BASE_CONTROL_PORT, loglevel=logging.INFO):
        """

        :param the_host:
        :param the_port:
        :param loglevel:
        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.DeviceManager')
        self.logger_.setLevel(loglevel)

        self.socket_ = None
        self.host_   = the_host
        self.port_   = the_port

    def _create_device_controllers_(self, the_string):
        """
        This is a utility method that will take a string representation of a JSON object and create
        the associated DeviceController objects.

        :param the_device_map: The devices_ map
        :param the_data:       The JSON string returned from a 'get' call to the avs4000d

        :return:
            != {}, a map containing the DeviceController objects
            == {}, no devices available.
        """

        self.logger_.debug("--> create_device_controllers()")
        self.logger_.debug("    data <{}>".format(the_string))

        the_map = {}

        try:
            the_json = json.loads(the_string)

            self.logger_.debug("    json <{}>".format(json.dumps(the_json, indent=2)))
            self.logger_.debug("    Num entries <{}>".format(len(the_json)))

            if len(the_json) < 1:
                self.logger_.debug("<-- create_device_controllers()")
                return

            if the_json[0] is False:
                self.logger_.debug("<-- create_device_controllers()")
                return

            the_index = 0
            for the_key in the_json[1].keys():
                if the_key != 'dm':
                    self.logger_.debug("    Processing key <{}>".format(the_key))

                    the_object = the_json[1].get(the_key)

                    if the_object.has_key('dn'):
                        the_device_number = the_object['dn']
                    else:
                        the_device_number = 'UNKNOWN'

                    if the_object.has_key('addr'):
                        the_address = the_object['addr']
                    else:
                        the_address = "UNKNOWN"

                    if the_object.has_key('sn'):
                        the_serial_number = the_object['sn']
                    else:
                        the_serial_number = "UNKNOWN"

                    if the_object.has_key('model'):
                        the_model = the_object['model']
                    else:
                        the_model = "UNKOWN"

                    if the_object.has_key('type'):
                        the_type = the_object['type']
                    else:
                        the_type = "UNKNOWN"

                    the_controller = DeviceController\
                        (
                            the_device_number,
                            the_address,
                            the_serial_number,
                            the_model,
                            the_type,
                            logging.INFO
                        )

                    the_map[the_index] = the_controller
                    the_index += 1

        except Exception as the_error:
            self.logger_.error("Unable to update map because: {}".format(the_error))
            return {}

        self.logger_.debug("    number devices <{}>".format(len(the_map)))
        self.logger_.debug("<-- create_device_controllers()")

        return the_map

    def get_controllers(self):
        """
        Use this method to obtain the list of device controllers attached to the system.
        This method connects to the Device Manager and obtains a list of know device controllers.

        :return:
            A list of DeviceController objects
        """
        self.logger_.debug("--> get_controllers()")
        self.logger_.debug("    host <{}>, port <{}>".format(self.host_, self.port_))

        try:
            self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_.connect((self.host_, self.port_))

            the_request = ['get']

            the_string = json.dumps(the_request) + '\n'

            self.socket_.send(the_string)

            the_data = self.socket_.recv(8192)

            self.logger_.debug("    the_data <{}>".format(the_data))

            the_map = self._create_device_controllers_(the_data)

        except Exception as the_error:
            self.logger_.error("Unable to obtain list of device controllers")

        try:
            self.socket_.close()
        except Exception:
            pass

        self.logger_.debug("<-- get_controllers()")
        return the_map


class DeviceController:
    """
    This class is intended to communicate with the AVS4000 daemons device controller software.
    """
    #
    # Constants
    #
    _vita49_expected_shorts_    = 4080
    _vita49_payload_unpack_str_ = 'h' * _vita49_expected_shorts_
    _le_complex_unpack_str_     = "<" + 'h' * (256 * 1024)  # See complex_buffer_ below, WORKING!!!, Little Endian

    def __init__(self, the_device_number, the_address, the_serial_number, the_model, the_type, loglevel=logging.INFO):
        """
        This constructor is designed to work with a REDHAWK device and takes the values obtained from performing
        an get operation.

        :param the_device_number: string representing the device number
        :param the_address:       string representing the ???
        :param the_serial_number: string representing the serial number of the device
        :param the_model:         string representing the model of device
        :param the_type:          string representing the type of device typically "usb"

        Notes:
            1. Added a lock on the data_socket_ because the REDHAWK SDR may call a get_data, while the data_socket_
               is being manipulated.  Need to ensure that the value of that parameter is protected.

        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.DeviceManager')
        self.logger_.setLevel(loglevel)

        #
        # Device Manager parameters.
        #
        self.device_number_    = int(the_device_number) # The device number zero based
        self.address_          = the_address            # FIXME: removed in latest driver
        self.ready_            = False                  # What state the physical device is in, True means usable.
        self.model_            = the_model              # What the model is,
        self.device_type_      = the_type               # Should always be USB
        self.serial_number_    = the_serial_number      # The serial number pulled from the device

        #
        # Device Controller parameters:
        #
        self.host_             = "localhost"                               # What host controller is on
        self.control_port_     = BASE_CONTROL_PORT + self.device_number_   # The control port to use
        self.data_port_        = BASE_RECEIVE_PORT + self.device_number_   # The data port to read from
        self.stream_id_        = "avs4000_{:03d}_{:03d}".format(self.device_number_, 0) # stream_id for data flow
        self.control_socket_   = None                                      # Socket attached to control port
        self.data_socket_      = None                                      # Socket attached to data port
        self.data_lock_        = threading.Lock()                          # See Note 1.

        #
        # RX Tuning parameters
        #
        self.sample_rate_      = 0                         # Donot base off of bandwidth because Complex data
        self.center_frequency_ = 0                         # Where to tune the radio
        self.bandwidth_        = None                      # Should always be 0, as bandwidth equals sample_rate
        self.output_format_    = COMPLEXOutputFormat       # What kind of data will be written out
        self.rx_status_        = None                      # Dictionary containing status of receiver.
        self.tx_status_        = None                      # Dictionary containing status of transmitter.
        self.allocation_id_    = ''                        # REDHAWK specific.

        self.change_flag_      = False                     # Has the user changed the RX Tuning parameters.
        self.read_data_        = True                      # Determines if this object will attach to data_port_

        self.complex_buffer_       = bytearray(1024 * 512)  # How much data to allocate for reads from data_port
        self.vita49_data_buffer_   = bytearray(8192 * 64)   # 64 Vita49 packets ~= 512K
        self.vita49_packet_buffer_ = bytearray(8192 * 64)   # 1024 packets

        self.master_           = Master(0, 'Auto')        # Will hold the Master class object

    def __str__(self):
        """
        Helper function to display human readable representation of object.

        :return:
            A string representing the object
        """

        the_string = "  device number  : {}\n"\
                     "  ready          : {}\n"\
                     "  address        : {}\n"\
                     "  model          : {}\n"\
                     "  device_type    : {}\n"\
                     "  serial number  : {}\n"\
                     "  control_socket : {}\n"\
                     "  data_socket    : {}\n"\
                     "  host           : {}\n"\
                     "  control port   : {}\n"\
                     "  data port      : {}\n"\
                     "  output_format  : {}\n"\
                     "  read_data      : {}\n"\
                     "  stream id      : {}\n"\
                     "  complex unpack : {}\n".format\
            (
                self.device_number_,
                self.ready_,
                self.address_,
                self.model_,
                self.device_type_,
                self.serial_number_,
                self.control_socket_,
                self.data_socket_,
                self.host_,
                self.control_port_,
                self.data_port_,
                self.output_format_,
                self.read_data_,
                self.stream_id_,
                self._le_complex_unpack_str_[0]
            )

        return the_string

    def connect_data(self):
        """
        This helper method will connect to the device controller data port

        :return:
            N/A
        """
        self.logger_.debug("--> connect_data()")

        with self.data_lock_:
            if self.data_socket_ is None:
                try:
                    self.logger_.debug("    port <{}>".format(self.data_port_))

                    self.data_socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.data_socket_.setblocking(1)
                    self.data_socket_.settimeout(0.10)
                    self.data_socket_.connect((self.host_, self.data_port_))

                except Exception as the_error:
                    self.data_socket_ = None
                    raise RuntimeError("ERROR: Unable to connect to device because <{}>".format(str(the_error)))

        self.logger_.debug("<-- connect_data()")

    def disconnect_data(self):
        """
        This method will gracefully shutdown the data connection to the device controller

        :return:
            N/A
        """
        self.logger_.debug("--> disconnect_data()")

        self.logger_.debug("    Waiting for lock")
        with self.data_lock_:

            if self.data_socket_ is not None:
                self.logger_.debug("   cloing")
                self.data_socket_.close()
                self.data_socket_ = None

        self.logger_.debug("<-- disconnect_data()")

    def connect_control(self):
        """
        This is a utility routine used to connect to the device controller's control port.
        :param the_host:

        :return:

        """
        self.logger_.debug("--> connect_control() ")

        if self.control_socket_ is None:
            try:
                self.control_socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.control_socket_.connect((self.host_, self.control_port_))
                self.logger_.debug("    connected <{}>".format(self.control_socket_))

            except Exception as the_error:
                self.control_socket_ = None
                raise RuntimeError("ERROR: Unable to connect to device because <{}>".format(str(the_error)))

        self.logger_.debug("<-- connect_control()")


    def disconnect_control(self):
        """
        This is a utility routine used to gracefully disconnect from the device controllers control port

        :return:
            N/A
        """
        self.logger_.debug("--> disconnect_control() ")

        if self.control_socket_ is not None:
            self.control_socket_.close()
            self.control_socket_ = None

        self.logger_.debug("<-- disconnect_control() ")

    def send_command(self, the_request):
        """
        Use this method to send a JSON request to the control port of the associated
        device controller.

        :param the_request:  the JSON/(Python list/dictionary) to send

        :return:
            Tuple of two elements:
                Item 1:
                    == True, request successful
                    == False, request failed.

                Item 2:
                    != None, The string representing the response
                    == None, no response provided.
        """

        self.logger_.debug("--> send_command()")
        self.logger_.debug("    request type <{}>".format(type(the_request)))

        the_string = json.dumps(the_request) + "\n"

        try:
            the_number_bytes = self.control_socket_.send(the_string)
        except Exception:
            self.control_socket_ = None
            return False, None

        self.logger_.debug("    sent <{}>".format(the_number_bytes))

        try:
            the_data = self.control_socket_.recv(8912)
        except Exception:
            self.control_socket_ = None
            return False, None

        self.logger_.debug("    received <{}".format(the_data))

        try:
            the_response = json.loads(the_data)
        except ValueError:
            return False, None

        self.logger_.debug("    ".format(json.dumps(the_response, indent=2)))
        self.logger_.debug("    returning <{}>".format(the_response[0]))

        if len(the_response) > 1:
            return the_response[0], the_response[1]
        else:
            return the_response[0], None



    def setup(self):
        """
        Use this method to ensure that the device controller is in a known state

        :return:
            == True,  Initialization successful
            == False, Unable to initialize

        """
        self.logger_.debug("--> setup()")

        self.connect_control()

        the_request = \
            [
                "set",
                {
                    "rxdata" :
                        {
                            "run":       False,
                            "conEnable": False
                        }
                }
            ]

        valid, data = self.send_command(the_request)

        self.logger_.debug("<-- setup()")
        return valid

    def teardown(self):
        """
        Use this method to gracefully shutdown the interface to the device controller

        :return:
            == True,  Initialization successful
            == False, Unable to initialize

        """
        self.logger_.debug("--> teardown()")

        self.connect_control()

        the_request = \
            [
                "set",
                {
                    "rxdata" :
                        {
                            "run":       False,
                            "conEnable": False
                        }
                }
            ]

        valid, data = self.send_command(the_request)

        self.disconnect_data()
        self.disconnect_control()

        self.logger_.debug("<-- teardown()")
        return valid


    def enable(self):
        """
        Use this method to start data flowing.

        Notes:
           - It will connect to the control port if not already connected
           - It will connect to the data port if not already connected.

        :return:
            == True,  successfully turned data on
            == False, unable to start data.
        """
        self.logger_.debug("--> enable()")

        self.connect_control()

        #
        # Tell device to create data socket
        #
        the_request = \
            [
                "set",
                {
                    "rxdata":
                    {

                        "conEnable": True
                    }
                }
            ]

        valid, data = self.send_command(the_request)

        if not valid:
            self.logger_.debug("<-- enable()")
            return False

        '''
        NOTE:
          It is unclear if the component has been connected to the device at this point.
        '''

        #
        # Create data connection
        #
        if self.read_data_:
            self.logger_.debug("    read_data_ <True>")
            self.connect_data()
        else:
            self.logger_.debug("    read_data_ <False>")

        #
        # Turn the data on
        #
        the_request = \
            [
                "set",
                {
                    "rxdata":
                    {
                        "run": True
                    }
                }
            ]

        valid, data = self.send_command(the_request)

        self.logger_.debug("<-- enable()")
        return valid

    def disable(self):
        """
        Use this method to turn data off

        :return:
            N/A

        :raises RuntimeError: when there is a problem:
        """

        self.logger_.debug("--> disable()")

        #
        # Make sure I have a control connection
        #
        self.connect_control()

        #
        # Issue the request to stop the data.
        #
        #  - conEnable: needs to be sent to ensure socket is closed on server
        #  - run:       needs to be sent to ensure that the data is turned off.
        #
        the_request = \
            [
                "set",
                {
                    "rxdata":
                    {
                        "run": False
                    }
                }
            ]

        #
        # Send the request to stop the data
        #
        valid, data = self.send_command(the_request)
        self.logger_.debug("    rxdata.run valid <{}>, <{}>".format(valid, data))

        if not valid:
            self.disconnect_data()
            self.logger_.debug("<-- disable()")
            raise RuntimeError("Unable to update rxdata.run, received <{}>".format(data))

        the_request = \
            [
                "set",
                {
                    "rxdata":
                        {
                            "conEnable":  False
                        }
                }
            ]

        #
        # Send the request to teardown socket
        #
        valid, data = self.send_command(the_request)
        self.logger_.debug("    rxdata.conEnable valid <{}>, <{}>".format(valid, data))

        if not valid:
            self.disconnect_data()
            self.logger_.debug("<-- disable()")
            raise RuntimeError("Unable to update rxdata.conEnable, received <{}>".format(data))

        #
        # Disconnect the data port
        #
        self.disconnect_data()
        self.logger_.debug("<-- disable()")


    def _create_tune_request(self, the_data_port, the_center_frequency, the_sample_rate, the_output_format):
        '''
        This is a utility method to create the JSON message to configure the receiver for tuning

        :param the_data_port:         The TCP port that the data consumer/sink will read from
        :param the_center_frequency:  The center frequency to tune to in MHz
        :param the_sample_rate:       The sample rate in MSPS
        :param the_output_format:     The output format: COMPLEXOutputFormat, VITA49OutputFormat

        :return:
            List that may be converted to a JSON object, and conforms to the AVS4000 API
        '''

        #
        # Determine what the output fprmat should be:
        #
        if the_output_format == VITA49OutputFormat:
            useV49 = True
        else:
            useV49 = False

        the_request = \
            [
                "set",
                {
                    "rxdata" :
                    {
                        "conEnable": False,
                        "run":       False,
                        "conType":   "tcp",
                        "conPort":   the_data_port,
                        "useV49":    useV49
                    },
                    "rx" :
                    {
                        "sampleRate": the_sample_rate,
                        "freq":       the_center_frequency,
                    }
                }
            ]

        return the_request

    def set_tune(self, the_center_frequency, the_bandwidth, the_sample_rate):
        """
        This method will setup the transceiver to recieve data at the specified center_frequency and sample_rate.  The
        bandwidth parameter is ignored for now.  The receiver will be configured but not sending data at this point

        :param the_center_frequency:  Where to tune in MHz
        :param the_bandwidth:         Ignored
        :param the_sample_rate:       The sample rate in MSPS

        :return:
            == True, the tune reqquest was successful
            == False, the tune request failed.
        """

        self.logger_.debug("--> set_tune()")

        self.connect_control()

        self.bandwidth_        = None
        self.center_frequency_ = the_center_frequency
        self.sample_rate_      = the_sample_rate

        self.logger_.debug("   output_format_ <{}>".format(self.output_format_))

        the_request = self._create_tune_request\
            (
            self.data_port_,
            self.center_frequency_,
            self.sample_rate_,
            self.output_format_
            )

        valid, data = self.send_command(the_request)

        self.change_flag_ = True

        #
        # Query the device for the current master sample rate.
        # This value will be used when calculating the fractional sample rate when receiving vita49 packets
        #
        if not self.query_master():
            self.logger_.error("Unable to obtain master sample rate.")

        self.logger_.debug("<-- set_tune()")
        return valid

    def delete_tune(self):
        self.logger_.debug("--> delete_tune()")

        #
        # FIXME: Not sure what I should do here
        #

        self.logger_.debug("<-- set_tune()")
        return True

    def query_rxstatus(self):
        """
        Use this method to make a request to the Device Controller for the current rxstatus information.

        :return:
           RxStatus: an object representing the rx status

        :raises RunTimeError: Unable to communicate to Device Controller
        """
        self.logger_.debug("--> query_rxstatus()")

        self.connect_control()

        the_request = ['get', ['rxstat']]

        valid, data = self.send_command(the_request)

        if valid:
            self.rx_status_ = RxStatus(data)
        else:
            self.logger_.debug("<-- query_rxstatus()")
            raise RuntimeError("Daemon refused status request.")

        self.logger_.debug("<-- query_rxstatus()")

        return self.rx_status_

    def query_txstatus(self):
        """
        Use this method to make a request to the Device Controller for the current txstatus information.

        :return:
            TxStatus: an object representing the tx status

        :raises NotImplementedError: Unable to communicate to Device Controller
        """
        self.logger_.debug("--> query_txstatus()")

        self.connect_control()

        raise NotImplementedError("TX statusing is not available yet.")

        self.logger_.debug("<-- query_txstatus()")

    def query_master(self):
        """
        Use this method to make a request to the
        :return:
        """
        self.logger_.debug("--> query_master()")

        self.connect_control()

        #
        # Tell device to create data socket
        #
        the_request = \
            [
                "get", "master"
            ]

        valid, data = self.send_command(the_request)

        if not valid:
            self.logger_.debug("<-- query_master()")
            return False

        self.logger_.debug("    data <{}>".format(data))

        the_sample_rate      = data['master']['SampleRate']
        the_sample_rate_mode = data['master']['SampleRateMode']

        self.master_ = Master(the_sample_rate, the_sample_rate_mode)

        self.logger_.debug("<-- query_master()")
        return True

    '''
    #
    # This method is depricated because it is way too slow.
    #
    def get_data_complex_old(self):
        """
        This method will pull data from the data socket, and return a complex data as a list of two unsigned shorts.
        The problem is that it is extremely slow.  It is left in the source for reference.

        :return:
            == None, no data
            != None, A list/sequence of unsigned shorts
        """
        self.logger_.debug("--> get_data_complex()")
        the_data = []

        with self.data_lock_:
            if self.data_socket_ is not None:
                #
                # FIXME:
                #   - Need to investigate doing this in a more efficient manner
                #   - Need to investigate changing the recv to have a timeout!
                #
                try:
                    the_string = self.data_socket_.recv(16384)
                except socket.error as the_error:
                    self.logger_.debug("    get_data_complex error <{}>".format(str(the_error)))
                    self.logger_.debug("<-- get_data_complex()")
                    return the_data


                while len(the_string) % 2 != 0:
                    print("WARNING: length is not multiple of 2 <{}>".format(len(the_string)))

                    try:
                        the_byte = self.data_socket_.recv(1)
                    except socket.error as the_error:
                        self.logger_.error("Error: <{}>".format(str(the_error)))
                        self.logger_.debug("<-- get_data_complex()")
                        return the_data

                    self.logger_.debug("    len the_byte <{}>".format(len(the_byte)))
                    the_string.join(the_byte)
                    self.logger_.debug("    length now <{}>".format(len(the_string)))

                    time.sleep(0.1)

                the_array = array.array('h', the_string)
                the_data = the_array.tolist()

        self.logger_.debug("<-- get_data_complex()")
        return the_data
        '''

    def get_data_complex(self):
        """
        This method will pull data from the data socket, and return a complex data as a list of two unsigned shorts.
        It is assumed that the Device Controller is configured to provide just complext data.

        :return:
            == None, no data
            != None, a list of unsigned short
        """

        self.logger_.debug("--> get_data_complex()")

        current_view = memoryview(self.complex_buffer_)

        toread = len(self.complex_buffer_)

        self.logger_.debug("   Waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("    Waiting for data")
                        nbytes = self.data_socket_.recv_into(current_view, toread)
                        self.logger_.debug("    Received nbytes <{}>".format(nbytes))
                    except socket.error as the_error:
                        self.logger_.debug("    Recieved <{}>".format(str(the_error)))
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        return None

                    current_view = current_view[nbytes:] # slicing views is cheap
                    toread -= nbytes

                #
                # The following is used to unpack
                #
                #the_num_shorts = len(self.complex_buffer_) / 2
                #the_list = struct.unpack('h' * the_num_shorts, self.complex_buffer_)

                the_list = struct.unpack(self._le_complex_unpack_str_, self.complex_buffer_)

                self.logger_.debug("<-- get_data_complex()")
                return the_list
            else:
                self.logger_.debug("<-- get_data_complex()")
                return None

        self.logger_.debug("<-- get_data_complex()")
        return None

    def get_data_vita49(self):
        """
        This method will pull data from the data socket, a series of Vita49DataPacket objects.

        Notes:
          This method does not handle synchronizing to the Vita49 FAW it expects that byte 0 is the start of
          the packet.  Therefore if there are any buffer overflows on the daemon, then no data will be returned.

        :return:
            == None, no data
            != None, A list of Vita49DataPackets objects
        """
        self.logger_.debug("--> get_data_vita49()")

        the_packet_list = []

        current_view = memoryview(self.vita49_data_buffer_)
        full_view    = current_view

        toread = len(self.vita49_data_buffer_)

        self.logger_.debug("    Waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("    Waiting for data")
                        nbytes = self.data_socket_.recv_into( current_view, toread)
                        self.logger_.debug("    Received nbytes <{}>".format(nbytes))
                    except socket.error as the_error:
                        self.logger_.debug("    Recieved <{}>".format(str(the_error)))
                        self.logger_.debug("<-- get_data_vita49()")
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("    Read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("<-- get_v49_data()")
                        return None

                    current_view =  current_view[nbytes:] # slicing views is cheap
                    toread -= nbytes

                #
                # This loop will break the buffer up into separate packets based upon the
                # information defined in the Vita49 module
                #
                # It will slice the associated memoryview on packet boundaries, then
                # extract the VRL and VRT Header information and finally unpack the
                # payload into signed 16bit values.
                #
                for index in range (0, len(self.vita49_data_buffer_)/Vita49.VRT_PACKET_SIZE):
                    end = (index + 1) * Vita49.VRT_PACKET_SIZE
                    value = index * Vita49.VRT_PACKET_SIZE
                    if (value > 0):
                        start = value
                    else:
                        start = 0

                    self.logger_.debug("    start <{}>, end <{}>".format(start,end))
                    data =  full_view[start:end]
                    self.logger_.debug("    data length <{}> type <{}> ".format(len(data), data))
                    self.logger_.debug("    view is type <{}>".format( current_view))

                    #
                    # The following is used to unpack,
                    #   vrl        = bytes[0 - 7]
                    #   vrt header = bytes[8 - 28]
                    #
                    # self.vita49_data_buffer_[Vita49.VRL_OFFSET:Vita49.VRL_OFFSET + Vita49.VRL.SIZE],
                    # self.vita49_data_buffer_[Vita49.VRT_OFFSET:Vita49.VRT_OFFSET + Vita49.VRT.HDR_SIZE],
                    #
                    the_vrl = Vita49.VRL\
                        (
                            data[Vita49.VRL_OFFSET:Vita49.VRL_OFFSET + Vita49.VRL.SIZE],
                            Vita49.LITTLE_ENDIAN
                        )

                    the_vrt = Vita49.VRT\
                        (
                            data[Vita49.VRT_OFFSET:Vita49.VRT_OFFSET + Vita49.VRT.HDR_SIZE],
                            Vita49.LITTLE_ENDIAN
                        )

                    if the_vrl.faw() != Vita49.VRL.EXPECTED_FAW:
                        self.logger_.debug("    {} = {}".format(the_vrl.faw(), Vita49.VRL.EXPECTED_FAW))
                        self.logger_.debug\
                             (
                                "    Invalid faw <{0:#010x}>, VRL: \n<{1}>, \nEXPECTED <{2:#010x}>".format
                                (
                                    the_vrl.faw(),
                                    the_vrl,
                                    Vita49.VRL.EXPECTED_FAW
                                )
                            )
                        self.logger_.debug("<-- get_data_vita49()")
                        return None

                    if the_vrt.packet_size() != Vita49.VRT.EXPECTED_PACKET_SIZE:
                        self.logger_.debug("    Invalid packet_size, VRL: <{}>".format(the_vrt))
                        self.logger_.debug("<-- get_data_vita49()")
                        return None

                    #
                    # Convert the buffer to unsigned short 16 Complex data, starting at 28 bytes from beginning of the
                    # buffer.
                    #  the_num_shorts should always be 4090.
                    #  the_buffer_end is where payload stops and VEND begins.
                    #
                    #  Need to set the end of the buffer based upon that number otherwise the unpack will complain.
                    #
                    the_num_shorts = the_vrt.number_payload_words() * 2
                    the_buffer_end = Vita49.VRT_PAYLOAD_OFFSET + (the_vrt.number_payload_words() * 4)

                    if (the_num_shorts != self._vita49_expected_shorts_):
                        self.logger_.debug\
                            (
                                "    packet_size <{}>, buffer size <{}>, the_num_shorts <{}>".format
                                (
                                    the_vrt.number_payload_words(),
                                    len(self.vita49_data_buffer_[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]),
                                    the_num_shorts
                                )
                            )
                    #self.vita49_data_buffer_[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]
                    the_tuple = struct.unpack\
                        (
                            self._vita49_payload_unpack_str_,
                            data[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]
                        )

                    the_packet = Vita49.Vita49DataPacket(the_vrl, the_vrt, the_tuple)
                    the_packet_list.append(the_packet)

                self.logger_.debug("    Good data")
                self.logger_.debug("<-- get_data_vita49()")
                return the_packet_list

            else:
                self.logger_.debug("    data_socket_ == None")
                self.logger_.debug("<-- get_data_vita49()")
                return None

        #
        # Here for completeness
        #
        self.logger_.debug("    while loop failed.")
        self.logger_.debug("<-- get_data_vita49()")
        return None

    def get_data_vita49_single_timestamp(self):
        """
        This method will pull data from the data socket and encapsulate it into a list of Vita49DataPacket object.
        Currently this list has only one element.  This is being done to keep the return API the same as
        get_data_vita49. Additionally this will combine the payload of multiple Vita49.0/1 packets together with
        the first VRT,VRL being returned.

        Notes:
          This method does not handle synchronizing to the Vita49 FAW it expects that byte 0 is the start of
          the packet.  Therefore if there are any buffer overflows on the daemon, then no data will be returned.

        :return:
            == None, no data
            != None, A list of Vita49DataPackets objects (1 element in size)
        """
        self.logger_.debug("--> get_data_vita49_single_timestamp()")

        the_packet_list = []

        current_view = memoryview(self.vita49_data_buffer_)
        full_view = current_view

        toread = len(self.vita49_data_buffer_)

        self.logger_.debug("    Waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                the_packet = None
                while toread > 0:
                    try:
                        self.logger_.debug("    Waiting for data")
                        nbytes = self.data_socket_.recv_into(current_view, toread)
                        self.logger_.debug("    Received nbytes <{}>".format(nbytes))
                    except socket.error as the_error:
                        self.logger_.debug("    Recieved <{}>".format(str(the_error)))
                        self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("    Read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                        return None

                    current_view = current_view[nbytes:]  # slicing views is cheap
                    toread -= nbytes

                #
                # This loop will break the buffer up into seperate packets based upon the
                # information defined in the Vita49 module
                #
                # It will slice the associated memoryview on packet boundaries, then
                # extract the VRL and VRT Header inforamtion and finally unpack the
                # payload into signed 16bit values.
                #
                for index in range(0, len(self.vita49_data_buffer_) / Vita49.VRT_PACKET_SIZE):
                    end = (index + 1) * Vita49.VRT_PACKET_SIZE
                    value = index * Vita49.VRT_PACKET_SIZE
                    if (value > 0):
                        start = value
                    else:
                        start = 0

                    self.logger_.debug("    start <{}>, end <{}>".format(start, end))
                    data = full_view[start:end]
                    self.logger_.debug("    data length <{}> type <{}> ".format(len(data), data))
                    self.logger_.debug("    view is type <{}>".format(current_view))

                    #
                    # The following is used to unpack,
                    #   vrl        = bytes[0 - 7]
                    #   vrt header = bytes[8 - 28]
                    #
                    # self.vita49_data_buffer_[Vita49.VRL_OFFSET:Vita49.VRL_OFFSET + Vita49.VRL.SIZE],
                    # self.vita49_data_buffer_[Vita49.VRT_OFFSET:Vita49.VRT_OFFSET + Vita49.VRT.HDR_SIZE],
                    #
                    the_vrl = Vita49.VRL \
                            (
                            data[Vita49.VRL_OFFSET:Vita49.VRL_OFFSET + Vita49.VRL.SIZE],
                            Vita49.LITTLE_ENDIAN
                        )

                    the_vrt = Vita49.VRT \
                            (
                            data[Vita49.VRT_OFFSET:Vita49.VRT_OFFSET + Vita49.VRT.HDR_SIZE],
                            Vita49.LITTLE_ENDIAN
                        )

                    if the_vrl.faw() != Vita49.VRL.EXPECTED_FAW:
                        self.logger_.debug("    {} = {}".format(the_vrl.faw(), Vita49.VRL.EXPECTED_FAW))
                        self.logger_.debug \
                                (
                                "    Invalid faw <{0:#010x}>, VRL: \n<{1}>, \nEXPECTED <{2:#010x}>".format
                                    (
                                    the_vrl.faw(),
                                    the_vrl,
                                    Vita49.VRL.EXPECTED_FAW
                                )
                            )
                        self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                        return None

                    if the_vrt.packet_size() != Vita49.VRT.EXPECTED_PACKET_SIZE:
                        self.logger_.debug("    Invalid packet_size, VRL: <{}>".format(the_vrt))
                        self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                        return None

                    #
                    # Convert the buffer to unsigned short 16 Complex data, starting at 28 bytes from beginning of the
                    # buffer.
                    #  the_num_shorts should always be 4090.
                    #  the_buffer_end is where payload stops and VEND begins.
                    #
                    #  Need to set the end of the buffer based upon that number otherwise the unpack will complain.
                    #
                    the_num_shorts = the_vrt.number_payload_words() * 2
                    the_buffer_end = Vita49.VRT_PAYLOAD_OFFSET + (the_vrt.number_payload_words() * 4)

                    if (the_num_shorts != self._vita49_expected_shorts_):
                        self.logger_.debug \
                                (
                                "    packet_size <{}>, buffer size <{}>, the_num_shorts <{}>".format
                                    (
                                    the_vrt.number_payload_words(),
                                    len(self.vita49_data_buffer_[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]),
                                    the_num_shorts
                                )
                            )
                    # self.vita49_data_buffer_[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]
                    the_tuple = struct.unpack \
                            (
                            self._vita49_payload_unpack_str_,
                            data.tobytes()[Vita49.VRT_PAYLOAD_OFFSET:the_buffer_end]
                        )

                    if the_packet == None:
                        the_packet = Vita49.Vita49DataPacket(the_vrl, the_vrt, the_tuple)
                    else:
                        the_packet.extend(the_tuple)

                self.logger_.debug("    Good data")
                self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                return [the_packet]

            else:
                self.logger_.debug("    data_socket_ == None")
                self.logger_.debug("<-- get_data_vita49_single_timestamp()")
                return None

        #
        # Here for completeness
        #
        self.logger_.debug("    while loop failed.")
        self.logger_.debug("<-- get_data_vita49_single_timestamp()")
        return None

    def get_data_vita49_raw(self):
        """
        This method will pull data from the data socket, and return raw Vita49.0/1 packets without parsing or otherwise
        inspecting the information.

        Notes:
          This method does not handle synchronizing to the Vita49 FAW it expects that byte 0 is the start of
          the packet.  Therefore if there are any buffer overflows on the daemon, then no data will be returned.

        :return:
            == None, no data
            != None, A string containing one or more Vita49 packets.
        """
        self.logger_.debug("--> get_data_vita49_raw()")

        view = memoryview(self.vita49_packet_buffer_)

        toread = len(self.vita49_packet_buffer_)

        self.logger_.debug("    Waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("    Waiting for data")
                        nbytes = self.data_socket_.recv_into(view, toread)
                        self.logger_.debug("    Received nbytes <{}>".format(nbytes))
                    except socket.error as the_error:
                        self.logger_.debug("    Recieved <{}>".format(str(the_error)))
                        self.logger_.debug("<-- get_data_vita49_raw()")
                        return None, None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("    Read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("<-- get_data_vita49_raw()")
                        return None, None

                    view = view[nbytes:] # slicing views is cheap
                    toread -= nbytes

                self.logger_.debug("    Good data")
                self.logger_.debug("<-- get_data_vita49_raw()")
                return None, self.vita49_packet_buffer_

            else:
                self.logger_.debug("    data_socket_ == None")
                self.logger_.debug("<-- get_data_vita49_raw()")
                return None, None

        #
        # Here for completeness
        #
        self.logger_.debug("    while loop failed.")
        self.logger_.debug("<-- get_data_vita49_raw()")
        return None, None

    def data_port(self):
        """
        Accessor method, that returns the value of the data port associated with this Device Controller

        :return:
          integer representing the data port
        """
        return(self.data_port_)

    def allocation_id(self):
        """
        Accessor method, that returns the allocation id associated with this Device Controller

        :return:
           A string representing the allocation id
        """
        return(self.allocation_id_)

    def stream_id(self):
        """
        Accessor method, that returns the current stream id associated with this Device Controller

        :return:
            A string representing the current stream id.
        """
        return self.stream_id_

    def center_frequency(self):
        """
        Accessor method, that returns the current center frequency associated with this Device Controller
        This is the value that was sent via tune

        :return:
            The integer value of the center frequency sent to this Device Controller
        """
        return self.center_frequency_

    def bandwidth(self):
        """
        Accessor method, that returns the current bandwidth associated with this Device Controller

        Note:
            Because the device produces complex data samples, the bandwidth will typically
            equal the sample rate.

        :return:
            The integer value of the bandwidth
        """
        return(self.bandwidth_)

    def sample_rate(self):
        """
        Accessor method, that returns the current sample rate associated with this Device Controller

        :return:
            The integer value of the sample rate
        """
        return(self.sample_rate_)

    def rxstatus(self):
        """
        Accessor method, that returns the cached information obtained from a query_rxstatus request.

        :return:
            None:      query_rxstatus never performed.
            RxStatus : the cached results obtained from the query_rxstatus method.
        """
        return self.rx_status_

    def txstatus(self):
        """
        Accessor method, that returns the cached information obtained from a query_txstatus request.

        :return:
            None:      query_rxstatus never performed.
            TxStatus : the cached results obtained from the query_rxstatus method.
        """
        return self.tx_status_


    def output_format(self):
        """
        Accessor method, that returns the output_format of the Device Controller

        :return:
            COMPLEXOutputFormat: data_port will be producing signed 16bit complex data
            VITA49OutputFormat:  data port will be producing Vita49.0/1 packets
        """
        return self.output_format_
    
    def loglevel(self):
        """
        Accessor method, that returns the current loglevel set for the Device Controller
        :return:
            the logging level specified by the constructor, or set_log_level
        """
        return self.logger_.getEffectiveLevel()

    def read_data_flag(self):
        """
        Accessor method, that returns whether or not this device controller should be performing the network
        reads on the data socket.  When true data must be consumed using one of the get_data_x methods depending upon
        the output_format specified.

        :return:
            == True, then need to call get_data_x to obtain data based upon output_format
            == False, Some other application/thread is reading the data from the data_port
        """
        return self.read_data_

    def master(self):
        """
        Accessor method, that returns the cached value of the Master group data

        NOTE:
            Assumes that query_master has been performed.

        :return:
            == None: query_master has not been called.
            != None: Master object.
        """
        return self.master_

    def sri_changed(self):
        """
        Accessor method, that returns whether or not the signal related information has changed since the last call
        to this method.

        Notes:
            - This method returns the current value, and resets the internal state to False.
            - The set_tune method will set the internal state to True.

        :return:
            == True, SRI has changed
            == False, SRI has not changed.
        """
        the_result = self.change_flag_
        self.change_flag_ = False
        return the_result

    def set_read_data_flag(self, the_value):
        """
        Mutator method, that is used to indicate to the device controller whether on not it should read from the TCP/IP
        data port or not.

            If set to True, then the data packets read from the data port may be obtained by
            calling get_data_complex, get_data_vita49.

            If set to False, then it is expected that some other process will be consuming data form the
            data port.

        :param the_value: Boolean

        :return:
            N/A
        """

        self.logger_.debug("--> set_read_data_flag()")
        self.logger_.debug("    read_data_ <{}>".format(the_value))
        self.read_data_ = the_value
        self.logger_.debug("<-- set_read_data_flag()")

    def set_loglevel(self, the_level):
        """
        Mutator method, that is used to indicate the loglevel to use for this Device Controller

        :param the_level: logging.{DEBUG, INFO, WARN....}

        :return:
            N/A
        """

        self.logger_.setLevel(the_level)

    def set_output_format(self, the_type):
        """
        Mutator method, that is used to indicate to the device controller what kind of data to send over the
        data port.

        :param the_type: {COMPLEXDataFormat, VITA49DataFormat}

        :raises ValueError: if the_type not one of the defined values.

        :return:
            N/A
        """
        self.logger_.debug("--> setOutputFormat()")
        self.logger_.debug("    the_type <{}>".format(the_type))

        if the_type == COMPLEXOutputFormat:
            self.output_format_ = COMPLEXOutputFormat

        elif the_type == VITA49OutputFormat:
            self.output_format_ = VITA49OutputFormat

        else:
            raise ValueError("Invalid output type of <{}> requested.".format(the_type))

        self.logger_.debug("    output_format <{}>".format(self.output_format_))
        self.logger_.debug("<-- setOutputFormat()")


if __name__ == '__main__':
    the_dm = DeviceManager()
    the_dc_map = the_dm.get_controllers()

    print("Number of DC's <{}>".format(len(the_dc_map)))

