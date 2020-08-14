#!/usr/bin/env python

#
# Make sure the logging is prior to other imports so that I my basic config takes precedence
#
import logging

MODULE_LOG_FORMAT = '%(asctime)s %(name)s.%(funcName)s %(levelname)s: %(message)s @ %(lineno)d'
logging.basicConfig(level=logging.INFO, format=MODULE_LOG_FORMAT)
module_logger = logging.getLogger('AVS4000Transceiver')

import socket
import json
import array
import threading
import time
import distutils.util
import struct
import Vita49


RXType = 'RX'
TXType = 'TX'

COMPLEXOutputFormat  = 'ComplexData'
VITA49OutputFormat   = 'Vita49Data'

BASE_CONTROL_PORT = 12900
BASE_RECEIVE_PORT = 12700

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


class DN:
    """
    This classs encapsulates the information associated with the DN group defined by the
    AVS4000 API
    """

    def __init__(self, loglevel=logging.INFO):
        """
        Constructor

        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.DN')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.setLevel(loglevel)
        self.logger_.propagate = False

        self.logger_.debug("ENTER")

        self.addr_ = 0
        self.dn_ = 0
        self.model_ = ""
        self.ready_ = False
        self.sn_ = ""
        self.type_ = ""

        self.logger_.debug("LEAVE")

    def __str__(self):

        the_string = "DN:\n"\
                     "  dn:    {}\n" \
                     "  ready: {}\n" \
                     "  model: {}\n" \
                     "  type:  {}\n" \
                     "  sn:    {}\n" \
                     "  addr:  {}".format \
                (
                self.dn_,
                self.ready_,
                self.model_,
                self.type_,
                self.sn_,
                self.addr_
            )

        return the_string

    def config(self, **kwargs):
        """
        Use this to update the object.

        :param kwargs:
            Key     Type    Mode    Description
            ---     ----    ----    -----------
            addr    uint    RO      Device class specific addres that uniquely identifies the device.
            dn      uint    RW      Device number for the device
            model   string  RO      Model name for the device
            ready   bool    RO      Ready state of the device (true=device is ready)
            sn      string  RO      Model specific serial number for the device
            type    string  RO      Type associated with the device

        :return:
            N/A
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            self.logger_.debug("key <{}>, value <{}>".format(key, value))

            if key == "dn":
                self.dn_ = value

            elif key == "ready":
                self.ready_ = value

            elif key == "model":
                self.model_ = value

            elif key == "type":
                self.type_ = value

            elif key == "sn":
                self.sn_ = value

            elif key == "addr":
                self.addr_ = value

            else:
                raise ValueError("Invalid key <{}>".format(key))
                self.logger_.debug("LEAVE")

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This is a utility method that provides a way to update the contents of the object
        using the results returned from the control port of a device manager. It is up to the
        caller to parse out the DN portion of the string.

        Note:
          - This update is slightly different than the other's because it doesn't make sense to process the
             list of DN's returned back using ['get'].  It makes more sense to process a single instance of
             a DN returned.

        :param the_string:  the string representing the DN {'dn': 1, ....}

        :return:
            == True, parsed the string
            == False, unable to parse the string

        :raises RunTimeError: Unable to process the_string as a JSON object.

        """
        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        result = False
        for key, value in the_json.items():
            if key == "dn":
                self.dn_ = value
                result = True

            if key == "ready":
                self.ready_ = value
                result = True

            if key == "model":
                self.model_ = value
                result = True

            if key == "type":
                self.type_ = value
                result = True

            if key == "sn":
                self.sn_ = value
                result = True

            if key == "addr":
                self.addr_ = value
                result = True

        self.logger_.debug("LEAVE")
        return result

    def dn(self):
        return self.dn_

    def ready(self):
        return self.ready_

    def model(self):
        return self.model_

    def type(self):
        return self.type_

    def sn(self):
        return self.sn_

    def addr(self):
        return self.addr_


class Master:
    """
    This class encapsulates the information assoicated with the Master group defined by the
    AVS4000 API.
    """

    def __init__(self, loglevel=logging.INFO):
        """
        Constructor

        :param loglevel:  the level to use
        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.Master')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.sampleRate_ = 0.0
        self.realSampleRate_ = 0.0
        self.sampleRateMode_ = ""

        self.logger_.debug("LEAVE")

    def __str__(self):
        the_string = "Master:\n" \
                     "  SampleRate:     {}\n" \
                     "  RealSampleRate: {}\n" \
                     "  SampleRateMode: {}".format \
                (
                self.sampleRate_,
                self.realSampleRate_,
                self.sampleRateMode_
            )

        return the_string

    def config(self, **kwargs):
        """
        Use this method to update the contents of the object, using key value pairs.

        :param kwargs:
            Key             Type    Mode    Description
            ---             ----    ----    -----------
            RealSampleRate  float   RO      Sample Rate (Hz) [1e6 to 50e6]
            SampleRate      float   RW      Sample Rate (Hz) [1e6 to 50e6]
            SampleRateMode  string  RW      Sample Rate Mode [Auto,Manual]

        :return:
            N/A
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            self.logger_.debug("    key <{}>, value<{}>".format(key, value))
            if key == "SampleRate":
                self.sampleRate_ = value

            elif key == "SampleRateMode":
                self.sampleRateMode_ = value

            elif key == "RealSampleRate":
                self.realSampleRate_ = value

            else:
                self.logger_.debug("<-- config()")
                raise ValueError("Invalid key <{}>".format(key))

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This is a utility method that provides a way to update the ccntents of the object
        using the results returned from the control port of a device controller.

        :param the_string:  part of the buffer returned from the request ["get", ["master"]]
                            {
                                'master':
                                {
                                'RealSampleRate': 40000000,
                                'SampleRate': 40000000,
                                'SampleRateMode': u'Auto'
                                }
                            }

        :return:
             == True, successfully decoded string
             == False, string not valid

        :raises RunTimeError: Unable to process the_string as a JSON object.

        """
        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        for key, value in the_json.items():
            if key == "master":
                for key_1, value_1 in value.items():
                    if key_1 == "RealSampleRate":
                        self.realSampleRate_ = value_1
                        result = True

                    if key_1 == "SampleRate":
                        self.sampleRate_ = value_1
                        result = True

                    if key_1 == "SampleRateMode":
                        self.sampleRateMode_ = value_1
                        result = True

        self.logger_.debug("LEAVE")
        return result

    def sampleRate(self):
        return self.sampleRate_

    def sampleRateMode(self):
        return self.sampleRateMode_

    def realSampleRate(self):
        return self.realSampleRate_


class RX:
    """
    This class encapsulates the informtion associated with the RX group defined by the
    AVS4000 API
    """

    def __init__(self, loglevel=logging.INFO):
        """
        Constructor
        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.RX')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.freq_         = 0.0
        self.gain_         = 0
        self.gainMode_     = ""
        self.lbbw_         = ""
        self.lbMode_       = ""
        self.lbThreshold_  = 0
        self.rfbw_         = 0
        self.sampleRate_   = 0
        self.startDelay_   = 0
        self.startMode_    = ""
        self.startUTCFrac_ = 0
        self.startUTCInt_  = 0
        self.userDelay_    = 0

        self.logger_.debug("LEAVE")

    def __str__(self):
        the_string = "RX:\n"\
                     "  Freq:         {}\n"\
                     "  Gain:         {}\n"\
                     "  GainMode:     {}\n"\
                     "  LBBW:         {}\n"\
                     "  LBMode:       {}\n"\
                     "  LBThreshold:  {}\n"\
                     "  RFBW:         {}\n"\
                     "  SampleRate:   {}\n"\
                     "  StartDelay:   {}\n"\
                     "  StartMode:    {}\n"\
                     "  StartUTCFrac: {}\n"\
                     "  StartUTCInt:  {}\n"\
                     "  UserDelay:    {}".format\
                (
                self.freq_,
                self.gain_,
                self.gainMode_,
                self.lbbw_,
                self.lbMode_,
                self.lbThreshold_,
                self.rfbw_,
                self.sampleRate_,
                self.startDelay_,
                self.startMode_,
                self.startUTCFrac_,
                self.startUTCInt_,
                self.userDelay_
                )

        return the_string

    def config(self, **kwargs):
        """
        Use this method to update the contents of the object, using key value pairs.

        :param kwargs:
            Key             Type    MODE    Description
            ---             ----    ----    -----------
            Freq            uint    RW      Tuning Freq (Hz) [50e6 to 6e9]
            Gain            int     RW      RF Gain (dB) [-3 to 71]
            GainMode        string  RW      RF Gain Mode [Manual,FastAGC,SlowAGC,HybridAGC]
            LBBW            string  RW      Low Band Bandwidth [Narrow,Wide]
            LBMode          string  RW      Low Band Mode [Auto,Enable,Disable]
            LBThresholdw    uint    RW      Low Band Threshold (Hz) [5e6 to 5e9]
            RFBW            uint    RW      RF Bandwidth [100e3 to 56e6, 0=auto]
            SampleRate      uint    RW      Sample Rate (Hz) [1e6 to 50e6]
            StartDelay      uint    RW      Start Delay (Sec) [1 to 300]
            StartMode       string  RW      Start Mode [Immediate,OnPPS,OnFracRoll,OnTime]
            StartUTCFrac    uint    RW      Start UTC Fracional
            StartUTCInt     uint    RW      Start UTC Integer (Sec)
            UserDelay       uint    RW      User Delay

        :return:
            N/A
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            if key == "Freq":
                self.freq_ = value

            elif key == "Gain":
                self.gain_ = value

            elif key == "GainMode":
                self.gainMode_ = value

            elif key == "LBBW":
                self.lbbw_ = value

            elif key == "LBMode":
                self.lbMode_ = value

            elif key == "LBThreshold":
                self.lbThreshold_ = value

            elif key == "RFBW":
                self.rfbw_ = value

            elif key == "SampleRate":
                self.sampleRate_ = value

            elif key == "StartDelay":
                self.startDelay_ = value

            elif key == "StartMode":
                self.startMode_ = value

            elif key == "StartUTCFrac":
                self.startUTCFrac_ = value

            elif key == "StartUTCInt":
                self.startUTCInt_ = value

            elif key == "UserDelay":
                self.startUTCInt_ = value

            else:
                self.logger_.debug("LEAVE")
                raise(ValueError("Invalid Key {}".format(key)))

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This is a utility method that provides a way to update the ccntents of the object
        using the results returned from the control port of a device controller.

        :param the_string:  the sub buffer returned from the request ["get", ["rxdata"]]
                            {
                                "rx":
                                {
                                    "Freq":101100000,
                                    "Gain":59,
                                    "GainMode":"SlowAGC",
                                    "LBBW":"Wide",
                                    "LBMode":"Auto",
                                    "LBThreshold":670000000,
                                    "RFBW":0,
                                    "SampleRate":2000000,
                                    "StartDelay":3,
                                    "StartMode":"Immediate",
                                    "StartUTCFrac":2,
                                    "StartUTCInt":32709,
                                    "UserDelay":1000
                                }
                            }

        :return:
            == True,  able to parse string
            == False, unable to parse string

        :raises RunTimeError: Unable to process the_string as a JSON object.
        """

        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        result = False
        for key, value in the_json.items():
            if key == "rx":
                for key_1, value_1 in value.items():
                    if key_1 == "Freq":
                        self.freq_ = value_1
                        result = True

                    if key_1 == "Gain":
                        self.gain_ = value_1
                        result = True

                    if key_1 == "GainMode":
                        self.gainMode_ = value_1
                        result = True

                    if key_1 == "LBBW":
                        self.lbbw_ = value_1
                        result = True

                    if key_1 == "LBMode":
                        self.lbMode_ = value_1
                        result = True

                    if key_1 == "LBThreshold":
                        self.lbThreshold_ = value_1
                        result = True

                    if key_1 == "RFBW":
                        self.rfbw_ = value_1
                        result = True

                    if key_1 == "SampleRate":
                        self.sampleRate_ = value_1
                        result = True

                    if key_1 == "StartDelay":
                        self.startDelay_ = value_1
                        result = True

                    if key_1 == "StartMode":
                        self.startMode_ = value_1
                        result = True

                    if key_1 == "StartUTCFrac":
                        self.startUTCFrac_ = value_1
                        result = True

                    if key_1 == "StartUTCInt":
                        self.startUTCInt_ = value_1
                        result = True

                    if key_1 == "UserDelay":
                        self.startDelay_ = value_1
                        result = True

        self.logger_.debug("LEAVE")
        return result

class RxData:
    """
    This class encapsulates the information associated with the RxData group defined by the
    AVS4000 API
    """

    def __init__(self, loglevel=logging.INFO):
        """
        Constructor
        """

        self.logger_ = logging.getLogger('AVS4000Transceiver.RxData')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.conEnable_   = False
        self.conPort_     = 12701
        self.conType_     = "TCP"
        self.run_         = False
        self.testPattern_ = False
        self.useBE_       = False
        self.useV49_      = False
        self.loopback_    = False

        self.logger_.debug("LEAVE")

    def __str__(self):
        the_string = "RXDATA:\n"\
                     "  ConEnable:   {}\n"\
                     "  ConPort:     {}\n"\
                     "  ConType:     {}\n"\
                     "  Run:         {}\n"\
                     "  TestPattern: {}\n"\
                     "  UseBE:       {}\n" \
                     "  UseV49:      {}\n"\
                     "  loopback:    {}".format\
            (
                self.conEnable_,
                self.conPort_,
                self.conType_,
                self.run_,
                self.testPattern_,
                self.useBE_,
                self.useV49_,
                self.loopback_
            )

        return the_string

    def config(self, **kwargs):
        """
        Use this method to update the internal data.

        :param kwargs:
            Keys        Type    Mode    Description
            ----        ----    ----    -----------
            ConEnable   bool    RW      Enable/Disable Conection [true=connect,false=disconnect]
            ConPort     uint    RW      Connection Port [0 - 0xFFFF]
            ConType     string  RW      Connection Type [TCP]
            Run         bool    RW      Enable/Disable RX Data [true=start,false=stop]
            TestPattern bool    RW      Enable/Disable Test Pattern
            UseBE       bool    RW      Enable/Disable Big Endian byte ordering for data. (Bool)
            UseV49      bool    RW      Enable/Disable Vita 49 Packets
            loopback    bool    RW      Enable/Disable Loopback

        :return:
            N/A

        :raises ValueError:
            Key invalid
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            if key == "ConEnable":
                self.conEnable_ = value

            elif key == "ConPort":
                self.conPort_ = value

            elif key == "ConType":
                self.conType_ = value

            elif key == "Run":
                self.run_ = value

            elif key == "TestPattern":
                self.testPattern_ = value

            elif key == "UseBE":
                self.useBE_ = value

            elif key == "UseV49":
                self.useV49_ = value

            elif key == "loopback":
                self.loopback_ = value

            else:
                self.logger_.debug("LEAVE")
                raise ValueError("Invalid Key <{}>".format(key))

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This is a utility method that provides a way to update the ccntents of the object
        using the results returned from the control port of a device controller.

        :param the_string:  the sub buffer returned from the request ["get", ["rxdata"]]
                            {
                                "rxdata":
                                {"
                                    ConEnable":true,
                                    "ConPort":12701,
                                    "ConType":"tcp",
                                    "Run":true,
                                    "TestPattern":false,
                                    "UseBE":false,
                                    "UseV49":true,
                                    "loopback":false
                                }
                            }

        :return:
            N/A

        :raises RunTimeError: Unable to process the_string as a JSON object.
        """
        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        result = False
        for key, value in the_json.items():
            if key == "rxdata":
                for key_1, value_1 in value.items():
                    if key_1 == "ConEnable":
                        self.conEnable_ = value_1
                        result = True

                    if key_1 == "ConPort":
                        self.conPort_ = value_1
                        result = True

                    if key_1 == "ConType":
                        self.conType_ = value_1
                        result = True

                    if key_1 == "Run":
                        self.run_ = value_1
                        result = True

                    if key_1 == "TestPattern":
                        self.testPattern_ = value_1
                        result = True

                    if key_1 == "UseBE":
                        self.useBE_ = value_1
                        result = True

                    if key_1 == "UseV49":
                        self.useV49_ = value_1
                        result = True

                    if key_1 == "loopback":
                        self.loopback_ = value_1
                        result = True

        self.logger_.debug("LEAVE")
        return result

    def conEnable(self):
        return self.conEnable_

    def conPort(self):
        return self.conPort_

    def conType(self):
        return self.conType_

    def run(self):
        return self.run_

    def testPattern(self):
        return self.testPattern_

    def useBE(self):
        return self.useBE_

    def useV49(self):
        return self.useV49_

    def loopback(self):
        return self.loopback_

class RxStat:
    """
    This class encapsulates the RxStatus information associated with the AVS4000 transciever

    """
    def __init__(self, loglevel=logging.INFO):

        self.logger_ = logging.getLogger('AVS4000Transceiver.RxStatus')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.gain_     = 0.0
        self.overflow_ = -1
        self.rate_     = -1
        self.sample_   = -1

        self.logger_.debug("LEAVE")

    def __str__(self):
        """
        Provides a string representation of this object

        :return:
            A string
        """
        the_string = "RxStat:\n"\
                     "  Gain:     {}\n"\
                     "  Overflow: {}\n"\
                     "  Rate:     {}\n"\
                     "  Sample:   {}".format\
            (
                self.gain_,
                self.overflow_,
                self.rate_,
                self.sample_
            )

        return the_string

    def config(self, **kwargs):
        """
        Use this method to update the internal data.

        :param kwargs:
            Keys        Type    Mode    Description
            ----        ----    ----    -----------
            Gain        float   RO      Roll-up Gain for Stream (dB)
            Overflow    uint    RO      Number of overflow errors for stream
            Rate        string  RO      Current Transfer Data Rate (MB/s)
            Sample      uint    RO      Current Transfer sample count

        :return:
            N/A

        :raises ValueError: One of the Keys is invalid
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            if key == "Gain":
                self.gain_ = value

            elif key == "Overflow":
                self.overflow_ = value

            elif key == "Rate":
                self.rate_ = value

            elif key == "Sample":
                self.sample_ = value

            else:
                self.logger_.debug("LEAVE")
                raise ValueError("Invalid Key <{}>".format(key))

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This method provide a way to update the object using the result from AVS4000 device port.

        :param the_string: The sub string returned from ['get', ['rxstat']]

                           {
                                "rxstat":
                                {
                                    "Gain":0,
                                    "Overflow":0,
                                    "Rate":7.647379044208254,
                                    "Sample":2566687680
                                }
                            }

        :return:
            == True, string parsed
            == False, unable to parse stirng

        :raises RunTimeError: if unable to parse json
        """
        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        result = False
        for key, value in the_json.items():
            if key == "rxstat":
                for key_1, value_1 in value.items():
                    if key_1 == "Gain":
                        self.gain_ = value_1
                        result = True

                    if key_1 == "Overflow":
                        self.overflow_ = value_1
                        result = True

                    if key_1 == "Rate":
                        self.rate_ = value_1
                        result = True

                    if key_1 == "Sample":
                        self.sample_ = value_1
                        result = True

        self.logger_.debug("LEAVE")
        return result

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

    def samplee(self):
        """
        Accessor method, that returns the current sample_count sent.

        :return:
            An integer representing the sample_count.
        """
        return self.sample_


class GPS:
    """
    This class encapsulates the information associated with the GPS group that is part of a Device Controller
    """

    def __init__(self, loglevel=logging.INFO):
        """
        Constructor
        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.GPS')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.alt_        = 0.0
        self.altUnits_   = ""
        self.auto_       = False
        self.hdop_       = 0
        self.last_       = 0.0
        self.lat_        = 0.0
        self.long_       = 0.0
        self.quality_    = 0
        self.satellites_ = 0
        self.sep_        = 0.0
        self.sepUnits_   = 0.0
        self.time_       = 0
        self.updates_    = False

        self.logger_.debug("LEAVE")

    def __str__(self):
        """
        This method will provide a string representation of the RxStatus object.

        :return:
            A string.
        """

        the_string = "GPS:\n"\
                     "  Alt:        {}\n"\
                     "  AltUnits:   {}\n"\
                     "  Auto:       {}\n"\
                     "  HDOP:       {}\n"\
                     "  LAT:        {}\n"\
                     "  LONG:       {}\n"\
                     "  Last:       {}\n"\
                     "  Quality:    {}\n"\
                     "  Satellites: {}\n"\
                     "  Sep:        {}\n"\
                     "  SepUnits:   {}\n"\
                     "  Time:       {}\n" \
                     "  Updates:    {}".format\
            (
                self.alt_,
                self.altUnits_,
                self.auto_,
                self.hdop_,
                self.lat_,
                self.long_,
                self.last_,
                self.quality_,
                self.satellites_,
                self.sep_,
                self.sepUnits_,
                self.time_,
                self.updates_
            )

        return the_string

    def config(self, **kwargs):
        """
        Use this method to update the internal data.

        :param kwargs:
            Key         Type    Mode    Description
            ---         ----    ----    -----------
            Alt         float   RO      Altitude (Float)
            AltUnits    string  RO      Altitude Units. Typically it will be 'M' for meters.
            Auto        bool    RW      Auto Mode when enabled will automatically disable updates a valid
                                        GPS time has been obtained.
            HDOP        int     ??      ??
            Last        float   RO      Last received GPS update (sec)
            LAT         float   RO      Latitude in fractional degrees
            LONG        float   RO      Longitude in fractional degrees
            Quality     uint    RO      Satellites uint RO Number of satellites used [0-12]
            Satellites  uint    RO      ??
            Sep         float   RO      Geiod separation: difference between ellipsoid and mean sea level.
            SepUnits    string  RO      Separation units. Typically it will be 'M' for meters.
            Time        uint    RO      GPS UTC number of seconds since the Epoch (Jan 1 1970)
            Updates     bool    RW      Enable GPS updates.

        :return:
            N/A

        :raises ValueError: One of the Keys is invalid
        """
        self.logger_.debug("ENTER")

        for key, value in kwargs.items():
            if key == "Alt":
                self.alt_ = value

            elif key == "AltUnits":
                self.altUnits_ = value

            elif key == "Auto":
                self.auto_ = value

            elif key == "HDOP":
                self.hdop_ = value

            elif key == "LAT":
                self.lat_ = value

            elif key == "LONG":
                self.long_ = value

            elif key == "Last":
                self.last_ = value

            elif key == "Quality":
                self.quality_ = value

            elif key == "Satellites":
                self.satellites_ = value

            elif key == "Sep":
                self.sep_ = value

            elif key == "SepUnits":
                self.sepUnits_ = value

            elif key == "Time":
                self.time_ = value

            elif key == "Updates":
                self.updates_ = value

        self.logger_.debug("LEAVE")

    def update(self, the_string):
        """
        This method provide a way to update the object using the result from AVS4000 device port.

        :param the_string: The substring returned from ['get', ['gps']]
                            {
                                "gps":
                                {
                                    "Alt":0,
                                    "AltUnits":"\u0000",
                                    "Auto":true,
                                    "HDOP":0,
                                    "LAT":0,
                                    "LONG":0,
                                    "Last":1.16,
                                    "Quality":0,
                                    "Satellites":0,
                                    "Sep":0,
                                    "SepUnits":"\u0000",
                                    "Time":null,
                                    "Updates":true
                                }
                            }

        :return:
            == True, string parsed
            == False, unable to parse stirng

        :raises RunTimeError: if unable to parse json
        """
        self.logger_.debug("ENTER")

        try:
            the_json = json.loads(the_string)
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to convert string to json object, because {}".format(str(the_error)))

        result = False
        for key, value in the_json.items():
            if key == "gps":
                 for key_1, value_1 in value.items():
                    if key_1 == "Alt":
                        self.alt_ = value_1
                        result = True

                    if key_1 == "AltUnits":
                        self.altUnits_ = value_1
                        result = True

                    if key_1 == "Auto":
                        self.auto_ = value_1
                        result = True

                    if key_1 == "HDOP":
                        self.hdop_ = value_1
                        result = True

                    if key_1 == "LAT":
                        self.lat_ = value_1
                        result = True

                    if key_1 == "LONG":
                        self.long_ = value_1
                        result = True

                    if key_1 == "Last":
                        self.last_ = value_1
                        result = True

                    if key_1 == "Quality":
                        self.quality_ = value_1
                        result = True

                    if key_1 == "Satellites":
                        self.satellites_ = value_1
                        result = True

                    if key_1 == "Sep":
                        self.sep_ = value_1
                        result = True

                    if key_1 == "SepUnits":
                        self.sepUnits_ = value_1
                        result = True

                    if key_1 == "Time":
                        self.time_ = value_1
                        result = True

                    if key_1 == "Updates":
                        self.updates_ = value_1
                        result = True

        self.logger_.debug("LEAVE")
        return result

    def alt(self):
        return self.alt_

    def altUnits(self):
        return self.altUnits_

    def auto(self):
        return self.auto_

    def hdop(self):
        return self.hdop_

    def lat(self):
        return self.lat_

    def long(self):
        return self.long_

    def last(self):
        return self.last_

    def quality(self):
        return self.quality_

    def satellites(self):
        return self.satellites_

    def sep(self):
        return self.sep_

    def sepUnits(self):
        return self.sepUnits_

    def time(self):
        return self.time_

    def updates(self):
        return self.updates_


class DeviceManager:
    """
    This class represents the Device Manager (DM) provided by the AVS4000 daemon.  The DM, is
    responsible for manageing all of the Device Controllers (DC)'s present.
    """

    def __init__(self, the_host='localhost', the_port=BASE_CONTROL_PORT, loglevel=logging.INFO):
        """
        Constructor

        :param the_host: The host device manager running on
        :param the_port: The port to connect too
        :param loglevel: The log level to use
        """
        self.logger_ = logging.getLogger('AVS4000Transceiver.DeviceManager')
        ch = logging.StreamHandler()
        formatter = logging.Formatter(MODULE_LOG_FORMAT)
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.propagate = False
        self.logger_.setLevel(loglevel)

        self.logger_.debug("ENTER")

        self.socket_ = None
        self.host_   = the_host
        self.port_   = the_port

        self.logger_.debug("LEAVE")

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

        self.logger_.debug("ENTER, data <{}>".format(the_string))

        the_map = {}

        try:
            the_json = json.loads(the_string)

            self.logger_.debug("json <{}>".format(json.dumps(the_json, indent=2)))
            self.logger_.debug("num entries <{}>".format(len(the_json)))

            if len(the_json) < 1:
                self.logger_.debug("LEAVE")
                return

            if the_json[0] is False:
                self.logger_.debug("LEAVE")
                return

            the_index = 0
            for the_key in the_json[1].keys():
                if the_key != 'dm':
                    self.logger_.debug("processing key <{}>".format(the_key))

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
            self.logger_.debug("LEAVE")
            return {}

        self.logger_.debug("number devices <{}>".format(len(the_map)))
        self.logger_.debug("LEAVE")

        return the_map

    def get_controllers(self):
        """
        Use this method to obtain the list of device controllers attached to the system.
        This method connects to the Device Manager and obtains a list of know device controllers.

        :return:
            A list of DeviceController objects
        """
        self.logger_.debug("ENTER, host <{}>, port <{}>".format(self.host_, self.port_))

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
            self.logger_.debug("LEAVE")

        try:
            self.socket_.close()
        except Exception:
            pass

        self.logger_.debug("LEAVE")
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
        self.logger_ = logging.getLogger('AVS4000Transceiver.DeviceController')

        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)s.%(funcName)s %(levelname)s: %(message)s @ %(lineno)d')
        ch.setFormatter(formatter)
        self.logger_.addHandler(ch)
        self.logger_.setLevel(loglevel)
        self.logger_.propagate = False

        self.logger_.debug("ENTER")

        #
        # Device Manager parameters.
        #
        # Reflect as a DN dn":1,"model":"AVS4000","ready":true,"sn":"SN000043","type":"USB
        #
        self.dn_ = DN()
        self.dn_.config(dn=int(the_device_number), ready=False, model=the_model, type=the_type, sn=the_serial_number)

        #self.device_number_    = int(the_device_number) # The device number zero based
        #self.address_          = the_address            # FIXME: removed in latest driver
        #self.ready_            = False                  # What state the physical device is in, True means usable.
        #self.model_            = the_model              # What the model is,
        #self.device_type_      = the_type               # Should always be USB
        #self.serial_number_    = the_serial_number      # The serial number pulled from the device

        #
        # Device Controller parameters:
        #
        self.host_             = "localhost"                                      # What host controller is on
        self.stream_id_        = "avs4000_{:03d}_{:03d}".format(self.dn_.dn(), 0) # stream_id for data flow

        #self.control_port_     = BASE_CONTROL_PORT + self.device_number_   # The control port to use
        self.control_port_     = BASE_CONTROL_PORT + self.dn_.dn()   # The control port to use
        #self.data_port_        = BASE_RECEIVE_PORT + self.device_number_   # The data port to read from
        self.data_port_        = BASE_RECEIVE_PORT + self.dn_.dn()   # The data port to read from

        self.control_socket_   = None                                      # Socket attached to control port
        self.data_socket_      = None                                      # Socket attached to data port
        self.data_lock_        = threading.Lock()                          # See Note 1.

        #
        # RX Tuning parameters
        #
        self.rx_               = RX()
        self.sample_rate_      = 0                         # Donot base off of bandwidth because Complex data
        self.center_frequency_ = 0                         # Where to tune the radio
        self.bandwidth_        = None                      # Should always be 0, as bandwidth equals sample_rate

        self.rx_data_          = RxData()
        self.output_format_    = COMPLEXOutputFormat       # What kind of data will be written out

        self.rx_stat_           = RxStat()                      # Dictionary containing status of receiver.
        self.tx_status_        = None                      # Dictionary containing status of transmitter.

        self.allocation_id_    = ''                        # REDHAWK specific.
        self.sri_change_flag_  = False                     # Has the user changed the RX Tuning parameters.
        self.read_data_        = True                      # Determines if this object will attach to data_port_

        self.complex_buffer_       = bytearray(1024 * 512)  # How much data to allocate for reads from data_port
        self.vita49_data_buffer_   = bytearray(8192 * 64)   # 64 Vita49 packets ~= 512K
        self.vita49_packet_buffer_ = bytearray(8192 * 64)   # 1024 packets

        self.master_           = Master()                   # Will hold the Master class object
        self.gps_              = GPS()

    def __str__(self):
        """
        Helper function to display human readable representation of object.

        :return:
            A string representing the object
        """

        the_string = "  {}\n"\
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
                self.dn_,
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
        self.logger_.debug("ENTER")

        with self.data_lock_:
            if self.data_socket_ is None:
                try:
                    self.logger_.debug("port <{}>".format(self.data_port_))

                    self.data_socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.data_socket_.setblocking(1)
                    self.data_socket_.settimeout(0.10)
                    self.data_socket_.connect((self.host_, self.data_port_))

                except Exception as the_error:
                    self.data_socket_ = None
                    self.logger_.debug("LEAVE")
                    raise RuntimeError("ERROR: Unable to connect to device because <{}>".format(str(the_error)))

        self.logger_.debug("LEAVE")

    def disconnect_data(self):
        """
        This method will gracefully shutdown the data connection to the device controller

        :return:
            N/A
        """
        self.logger_.debug("ENTER")

        self.logger_.debug("waiting for lock")
        with self.data_lock_:

            if self.data_socket_ is not None:
                self.logger_.debug("closing")
                self.data_socket_.close()
                self.data_socket_ = None

        self.logger_.debug("LEAVE")

    def connect_control(self):
        """
        This is a utility routine used to connect to the device controller's control port.
        :param the_host:

        :return:

        """
        self.logger_.debug("ENTER")

        if self.control_socket_ is None:
            try:
                self.control_socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.control_socket_.connect((self.host_, self.control_port_))
                self.logger_.debug("connected <{}>".format(self.control_socket_))

            except Exception as the_error:
                self.control_socket_ = None
                self.logger_.debug("LEAVE")
                raise RuntimeError("ERROR: Unable to connect to device because <{}>".format(str(the_error)))

        self.logger_.debug("LEAVE")


    def disconnect_control(self):
        """
        This is a utility routine used to gracefully disconnect from the device controllers control port

        :return:
            N/A
        """
        self.logger_.debug("ENTER")

        if self.control_socket_ is not None:
            self.control_socket_.close()
            self.control_socket_ = None

        self.logger_.debug("LEAVE")

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

        self.logger_.debug("ENTER, request type <{}>".format(type(the_request)))

        the_string = json.dumps(the_request) + "\n"

        try:
            the_number_bytes = self.control_socket_.send(the_string)
        except Exception:
            self.control_socket_ = None
            return False, None

        self.logger_.debug("sent number bytes<{}>".format(the_number_bytes))

        try:
            the_data = self.control_socket_.recv(8912)
        except Exception:
            self.control_socket_ = None
            return False, None

        self.logger_.debug("received <{}".format(the_data))

        try:
            the_response = json.loads(the_data)
        except ValueError:
            return False, None

        self.logger_.debug("response: {}".format(json.dumps(the_response, indent=2)))
        self.logger_.debug("returning <{}>".format(json.dumps(the_response[0])))

        if len(the_response) > 1:
            #
            # Make sure to return the string representation of the data, so that the objects can process it themselves
            # using their update method.
            #
            self.logger_.debug("LEAVE")
            return the_response[0], json.dumps(the_response[1])

        self.logger_.debug("LEAVE")
        return the_response[0], None

    def setup(self):
        """
        Use this method to ensure that the device controller is in a known state

        :return:
            == True,  Initialization successful
            == False, Unable to initialize

        """
        self.logger_.debug("ENTER")

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

        self.logger_.debug("LEAVE")
        return valid

    def teardown(self):
        """
        Use this method to gracefully shutdown the interface to the device controller

        :return:
            == True,  Initialization successful
            == False, Unable to initialize

        """
        self.logger_.debug("ENTER")

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

        self.logger_.debug("LEAVE")
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
        self.logger_.debug("ENTER")

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
            self.logger_.debug("LEAVE")
            return False

        '''
        NOTE:
          It is unclear if the component has been connected to the device at this point.
        '''

        #
        # Create data connection
        #
        if self.read_data_:
            self.logger_.debug("read_data_ <True>")
            self.connect_data()
        else:
            self.logger_.debug("read_data_ <False>")

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

        self.logger_.debug("LEAVE")
        return valid

    def disable(self):
        """
        Use this method to turn data off

        :return:
            N/A

        :raises RuntimeError: when there is a problem:
        """

        self.logger_.debug("ENTER")

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
        self.logger_.debug("rxdata.run valid <{}>, <{}>".format(valid, data))

        if not valid:
            self.disconnect_data()
            self.logger_.debug("LEAVE")
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
        self.logger_.debug("rxdata.conEnable valid <{}>, <{}>".format(valid, data))

        if not valid:
            self.disconnect_data()
            self.logger_.debug("LEAVE")
            raise RuntimeError("Unable to update rxdata.conEnable, received <{}>".format(data))

        #
        # Disconnect the data port
        #
        self.disconnect_data()
        self.logger_.debug("LEAVE")


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
        self.logger_.debug("ENTER")

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
                        "useV49":    useV49,
                        "useBE":     False
                    },
                    "rx" :
                    {
                        "sampleRate": the_sample_rate,
                        "freq":       the_center_frequency,
                    }
                }
            ]

        self.logger_.debug("LEAVE")
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

        self.logger_.debug("ENTER")

        self.connect_control()

        self.bandwidth_        = None
        self.center_frequency_ = the_center_frequency
        self.sample_rate_      = the_sample_rate

        self.logger_.debug("output_format_ <{}>".format(self.output_format_))

        the_request = self._create_tune_request\
            (
            self.data_port_,
            self.center_frequency_,
            self.sample_rate_,
            self.output_format_
            )

        valid, data = self.send_command(the_request)

        self.sri_change_flag_ = True

        #
        # Query the device for the current master sample rate.
        # This value will be used when calculating the fractional sample rate when receiving vita49 packets
        #
        try:
            self.query_master()
        except Exception as the_error:
            self.logger_.debug("LEAVE")
            self.logger_.error("Unable to obtain master sample rate, because {}.".format(str(the_error)))
            return False

        self.logger_.debug("LEAVE")
        return valid

    def delete_tune(self):
        self.logger_.debug("ENTER")

        #
        # FIXME: Not sure what I should do here
        #

        self.logger_.debug("LEAVE")
        return True

    def query_rx(self):
        """
        Use this method to make a request to the Device Controller for the current rx information

        :return:
           RX: an object representing the rx information

        :raises RunTimeError: Unable to communciate with Device Controller
        """
        self.logger_.debug("ENTER")

        self.connect_control()

        the_request = ['get', ['rx']]

        valid, data = self.send_command(the_request)
        self.logger_.debug("data <{}>".format(data))

        if valid:
            self.rx_.update(data)
        else:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Daemon refused status request.")

        self.logger_.debug("LEAVE")
        return self.rx_

    def query_rxstat(self):
        """
        Use this method to make a request to the Device Controller for the current rxstatus information.

        :return:
           RxStatus: an object representing the rxstat status

        :raises RunTimeError: Unable to communicate to Device Controller
        """
        self.logger_.debug("ENTER")

        self.connect_control()

        the_request = ['get', ['rxstat']]

        valid, data = self.send_command(the_request)
        self.logger_.debug("    data <{}>".format(data))

        if valid:
            self.rx_stat_.update(data)
        else:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Daemon refused status request.")

        self.logger_.debug("LEAVE")
        return self.rx_stat_

    def query_txstatus(self):
        """
        Use this method to make a request to the Device Controller for the current txstatus information.

        :return:
            TxStatus: an object representing the tx status

        :raises NotImplementedError: Unable to communicate to Device Controller
        """
        self.logger_.debug("ENTER")

        raise NotImplementedError("TX statusing is not available yet.")
        self.logger_.debug("LEAVE")

    def query_gps(self):
        """

        :return:
        """
        self.logger_.debug("ENTER")

        self.connect_control()

        #
        # Tell device to create data socket
        #
        the_request = ["get", ["gps"]]

        valid, data = self.send_command(the_request)
        self.logger_.debug("data <{}>".format(data))

        if valid:
            self.gps_.update(data)
        else:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Daemon refused status request.")

        self.logger_.debug("LEAVE")
        return self.gps_

    def query_master(self):
        """
        Use this method to make a request to the

        :return:
        """
        self.logger_.debug("ENTER")

        self.connect_control()

        #
        # Tell device to create data socket
        #
        the_request = ["get", ["master"]]

        valid, data = self.send_command(the_request)
        self.logger_.debug("data <{}>".format(data))

        if valid:
            self.master_.update(data)
        else:
            self.logger_.debug("LEAVE")
            raise RuntimeError("Daemon refused status request.")

        self.logger_.debug("LEAVE")
        return self.master_

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

        self.logger_.debug("ENTER")

        current_view = memoryview(self.complex_buffer_)

        toread = len(self.complex_buffer_)

        self.logger_.debug("waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("waiting for data")
                        nbytes = self.data_socket_.recv_into(current_view, toread)
                        self.logger_.debug("received nbytes <{}>".format(nbytes))

                    except socket.error as the_error:
                        self.logger_.debug("recieved <{}>".format(str(the_error)))
                        self.logger_.debug("LEAVE")
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("LEAVE")
                        return None

                    current_view = current_view[nbytes:] # slicing views is cheap
                    toread -= nbytes

                #
                # The following is used to unpack
                #
                #the_num_shorts = len(self.complex_buffer_) / 2
                #the_list = struct.unpack('h' * the_num_shorts, self.complex_buffer_)

                the_list = struct.unpack(self._le_complex_unpack_str_, self.complex_buffer_)

                self.logger_.debug("LEAVE")
                return the_list

            else:
                self.logger_.debug("LEAVE")
                return None

        self.logger_.debug("LEAVE")
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
        self.logger_.debug("ENTER")

        the_packet_list = []

        current_view = memoryview(self.vita49_data_buffer_)
        full_view    = current_view

        toread = len(self.vita49_data_buffer_)

        self.logger_.debug("waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("waiting for data")
                        nbytes = self.data_socket_.recv_into( current_view, toread)
                        self.logger_.debug("received nbytes <{}>".format(nbytes))

                    except socket.error as the_error:
                        self.logger_.debug("recieved <{}>".format(str(the_error)))
                        self.logger_.debug("LEAVE")
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("LEAVE")
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

                    self.logger_.debug("start <{}>, end <{}>".format(start,end))
                    data =  full_view[start:end]
                    self.logger_.debug("data length <{}> type <{}> ".format(len(data), data))
                    self.logger_.debug("view is type <{}>".format( current_view))

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
                        self.logger_.debug("{} = {}".format(the_vrl.faw(), Vita49.VRL.EXPECTED_FAW))
                        self.logger_.debug\
                             (
                                "Invalid faw <{0:#010x}>, VRL: \n<{1}>, \nEXPECTED <{2:#010x}>".format
                                (
                                    the_vrl.faw(),
                                    the_vrl,
                                    Vita49.VRL.EXPECTED_FAW
                                )
                            )
                        self.logger_.debug("LEAVE")
                        return None

                    if the_vrt.packet_size() != Vita49.VRT.EXPECTED_PACKET_SIZE:
                        self.logger_.debug("Invalid packet_size, VRL: <{}>".format(the_vrt))
                        self.logger_.debug("LEAVE")
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
                                "packet_size <{}>, buffer size <{}>, the_num_shorts <{}>".format
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

                self.logger_.debug("good data")
                self.logger_.debug("LEAVE")
                return the_packet_list

            else:
                self.logger_.debug("data_socket_ == None")
                self.logger_.debug("LEAVE")
                return None

        #
        # Here for completeness
        #
        self.logger_.debug("while loop failed.")
        self.logger_.debug("LEAVE")
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
        self.logger_.debug("ENTER")

        the_packet_list = []

        current_view = memoryview(self.vita49_data_buffer_)
        full_view = current_view

        toread = len(self.vita49_data_buffer_)

        self.logger_.debug("waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                the_packet = None
                while toread > 0:
                    try:
                        self.logger_.debug("waiting for data")
                        nbytes = self.data_socket_.recv_into(current_view, toread)
                        self.logger_.debug("received nbytes <{}>".format(nbytes))

                    except socket.error as the_error:
                        self.logger_.debug("recieved <{}>".format(str(the_error)))
                        self.logger_.debug("LEAVE")
                        return None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("Read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("LEAVE")
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

                    self.logger_.debug("start <{}>, end <{}>".format(start, end))
                    data = full_view[start:end]
                    self.logger_.debug("data length <{}> type <{}> ".format(len(data), data))
                    self.logger_.debug("view is type <{}>".format(current_view))

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
                        self.logger_.debug("{} = {}".format(the_vrl.faw(), Vita49.VRL.EXPECTED_FAW))
                        self.logger_.debug \
                                (
                                "invalid faw <{0:#010x}>, VRL: \n<{1}>, \nEXPECTED <{2:#010x}>".format
                                    (
                                    the_vrl.faw(),
                                    the_vrl,
                                    Vita49.VRL.EXPECTED_FAW
                                )
                            )
                        self.logger_.debug("LEAVE")
                        return None

                    if the_vrt.packet_size() != Vita49.VRT.EXPECTED_PACKET_SIZE:
                        self.logger_.debug("invalid packet_size, VRL: <{}>".format(the_vrt))
                        self.logger_.debug("LEAVE")
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
                                "packet_size <{}>, buffer size <{}>, the_num_shorts <{}>".format
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

                self.logger_.debug("good data")
                self.logger_.debug("LEAVE")
                return [the_packet]

            else:
                self.logger_.debug("data_socket_ == None")
                self.logger_.debug("LEAVE")
                return None

        #
        # Here for completeness
        #
        self.logger_.debug("while loop failed.")
        self.logger_.debug("LEAVE")
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
        self.logger_.debug("ENTER")

        view = memoryview(self.vita49_packet_buffer_)

        toread = len(self.vita49_packet_buffer_)

        self.logger_.debug("waiting for lock")
        with self.data_lock_:
            if self.data_socket_ is not None:
                while toread > 0:
                    try:
                        self.logger_.debug("waiting for data")
                        nbytes = self.data_socket_.recv_into(view, toread)
                        self.logger_.debug("received nbytes <{}>".format(nbytes))

                    except socket.error as the_error:
                        self.logger_.debug("recieved <{}>".format(str(the_error)))
                        self.logger_.debug("LEAVE")
                        return None, None

                    #
                    # Added this in the instance when the data socket is closed by the device controller
                    # because I called set "rxdata.conenable false" in a different thread.  This causes
                    # the recv_into to return a 0.
                    #
                    if nbytes == 0:
                        self.logger_.debug("read returned back 0 bytes, indicating data socket closed.")
                        self.logger_.debug("LEAVE")
                        return None, None

                    view = view[nbytes:] # slicing views is cheap
                    toread -= nbytes

                self.logger_.debug("good data")
                self.logger_.debug("LEAVE")
                return None, self.vita49_packet_buffer_

            else:
                self.logger_.debug("data_socket_ == None")
                self.logger_.debug("LEAVE")
                return None, None

        #
        # Here for completeness
        #
        self.logger_.debug("while loop failed.")
        self.logger_.debug("LEAVE")
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
        return self.rx_stat_

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
        self.logger_.debug("ENTER")

        the_result = self.sri_change_flag_
        self.sri_change_flag_ = False

        self.logger_.debug("LEAVE")
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

        self.logger_.debug("ENTER")

        self.logger_.debug("read_data_ <{}>".format(the_value))
        self.read_data_ = the_value

        self.logger_.debug("LEAVE")

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
        self.logger_.debug("ENTER, the_type <{}>".format(the_type))

        if the_type == COMPLEXOutputFormat:
            self.output_format_ = COMPLEXOutputFormat

        elif the_type == VITA49OutputFormat:
            self.output_format_ = VITA49OutputFormat

        else:
            self.logger_.debug("LEAVE")
            raise ValueError("invalid output type of <{}> requested.".format(the_type))

        self.logger_.debug("output_format <{}>".format(self.output_format_))
        self.logger_.debug("LEAVE")


if __name__ == '__main__':
    the_dm = DeviceManager()
    the_dc_map = the_dm.get_controllers()

    print("Number of DC's <{}>".format(len(the_dc_map)))

