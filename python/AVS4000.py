#!/usr/bin/env python
#
#
# AUTO-GENERATED
#
# Source: AVS4000.spd.xml
from ossie.device import start_device
import logging

from AVS4000_base import *

import AVS4000Transceiver

class AVS4000_i(AVS4000_base):
    """
    This device interfaces with an AVS4000 transceiver
    """

    def constructor(self):
        """
        This is called by the framework immediately after your device registers with the system.
        
        In general, you should add customization here and not in the __init__ constructor.  If you have 
        a custom port implementation you can override the specific implementation here with a statement
        similar to the following:
          self.some_port = MyPortImplementation()

        For a tuner device, the structure frontend_tuner_status needs to match the number
        of tuners that this device controls and what kind of device it is.
        The options for devices are: TX, RX, RX_DIGITIZER, CHANNELIZER, DDC, RX_DIGITIZER_CHANNELIZER
     
        For example, if this device has 5 physical
        tuners, 3 RX_DIGITIZER and 2 CHANNELIZER, then the code in the construct function 
        should look like this:

        self.addChannels(3, "RX_DIGITIZER");
        self.addChannels(2, "CHANNELIZER");
     
        The incoming request for tuning contains a string describing the requested tuner
        type. The string for the request must match the string in the tuner status.
        """
        self._baseLog.info("--> constructor()")
        
        self.host_                 = 'localhost'
        self.devices_              = {}
        self.dm_                   = AVS4000Transceiver.DeviceManager(the_host=self.host_, loglevel=logging.DEBUG)
        self.expected_frame_count_ = -1

        #
        # Query the number of controllers available
        #
        self.devices_ = self.dm_.get_controllers()

        #
        # Setup and property listeners
        #
        self.addPropertyChangeListener("avs4000_output_configuration", self.avs4000_output_configuration_changed)

        #
        # NOTE: The property structs have been created already, so I need to make sure to configure the devices
        #       created with the appropriate configuration.
        #
        for configuration in self.avs4000_output_configuration:
            self._baseLog.debug("    type <{}>, configuration <{}>".format(type(configuration), configuration))
            tuner_number = configuration.tuner_number
            output_source = configuration.output_source
            output_format = configuration.output_format

            self._baseLog.debug\
                (
                    "    \n"\
                    "tuner_number <{}>\n"\
                    "output_source <{}>\n"\
                    "output_format <{}>"\
                    .format(tuner_number, output_source, output_format)
                )

            if int(tuner_number) in self.devices_:
                self._baseLog.debug("    Updating device configuration.")
                if output_format == enums.avs4000_output_configuration__.output_format.VITA49:
                    self.devices_[tuner_number].set_output_format(AVS4000Transceiver.VITA49OutputFormat)
                else:
                    self.devices_[tuner_number].set_output_format(AVS4000Transceiver.COMPLEXOutputFormat)

                if output_source == enums.avs4000_output_configuration__.output_source.TCP:
                    self.devices_[tuner_number].set_read_data_flag(False)
                else:
                    self.devices_[tuner_number].set_read_data_flag(True)

        #
        # Identify the number of devices found.
        #
        self.addChannels(len(self.devices_.keys()), "RX_DIGITIZER")

        self._baseLog.info("    Found <{}>".format(len(self.devices_.keys())))
        self._baseLog.info("<-- constructor()")

    def start(self):
        """
        This method overrides the parent classes start method. It is called when the device in being
        brought into existence, started up, by the device manager

        :return:
            N/A
        """

        self._baseLog.info("--> start()")

        for tuner_id in self.devices_.keys():
            self.devices_[tuner_id].setup()

            #
            # Display how the devices are configured by default.
            #
            self._baseLog.info("    {}".format(self.devices_[tuner_id]))

        super(AVS4000_i, self).start()

        self._baseLog.info("<-- start()")

    def stop(self):
        """
        This method overrides the parent method.  It is called when the device manager is shutting down
        the device.

        :return:
            N/A
        """
        self._baseLog.info("--> stop()")

        super(AVS4000_i, self).stop()

        #
        # Call the parent's stop method
        #
        for tuner_id in self.devices_.keys():
            self.devices_[tuner_id].teardown()

        self._baseLog.info("<-- stop()")

    def avs4000_output_configuration_changed(self, propid, oldval, newval):
        self._baseLog.info("--> avs4000_output_configuration_changed()")
        self._baseLog.info("    propid <{}>".format(propid))
        self._baseLog.info("    oldval <{}>, length <{}>".format(oldval, len(oldval)))
        self._baseLog.info("    oldval[0] <{}>".format(oldval[0]))
        self._baseLog.info("    newval <{}>, length <{}>".format(newval, len(newval)))
        self._baseLog.info("    newval[0] <{}>".format(newval[0]))

        for index in range(0, len(newval)):
            the_tuner  = newval[index].tuner_number
            the_format = newval[index].output_format
            the_source = newval[index].output_source

            if the_tuner < len(self.devices_):
                #
                # What format the device should send the data:
                #  COMPLEX:  Data will be pushed out the dataShort_out port as 16bit I and Q complex samples
                #            Timestamps will be generated from the current processor time.
                #
                #  VITA49:   Data will be pushed out the dataShort_out port as 16bit I and Q complex samples.
                #            Timestampes will be generated from the integer-seconds-timestamp +
                #            fractional_seconds_timestamp_lsw of the VRT header.
                #
                # NOTE:
                #   Raw VITA49 ports were removed because currently there are no BULKIO VITA49 components that
                #   are able to read Vita49 packets.
                #
                if the_format == enums.avs4000_output_configuration__.output_format.COMPLEX:
                    self.devices_[the_tuner].set_output_format(AVS4000Transceiver.COMPLEXOutputFormat)

                if the_format == enums.avs4000_output_configuration__.output_format.VITA49:
                    self.devices_[the_tuner].set_output_format(AVS4000Transceiver.VITA49OutputFormat)

                #
                # Where will the data come from:
                #   TCP:     A component will have to read from the avs4000d TCP port
                #   BULKIO: A component will read from the standard bulkio port (see output_format)
                #
                if the_source == enums.avs4000_output_configuration__.output_source.BULKIO:
                    self.devices_[the_tuner].set_read_data_flag(True)

                if the_source == enums.avs4000_output_configuration__.output_source.TCP:
                    self.devices_[the_tuner].set_read_data_flag(False)
            else:
                self._baseLog.error("Ignoring request to set output format for tuner <{}>".format(the_tuner))

        self._baseLog.info("<-- avs4000_output_configuration_changed()")

    def process(self):
        """
        Basic functionality:
        
            The process method should process a single "chunk" of data and then return. This method
            will be called from the processing thread again, and again, and again until it returns
            FINISH or stop() is called on the device.  If no work is performed, then return NOOP.
            
        StreamSRI:
            To create a StreamSRI object, use the following code (this generates a normalized SRI that does not flush the queue when full):
                sri = bulkio.sri.create("my_stream_id")

            To create a StreamSRI object based on tuner status structure index 'idx' and collector center frequency of 100:
                sri = frontend.sri.create("my_stream_id", self.frontend_tuner_status[idx], self._id, collector_frequency=100)

        PrecisionUTCTime:
            To create a PrecisionUTCTime object, use the following code:
                tstamp = bulkio.timestamp.now() 
  
        Ports:

            Each port instance is accessed through members of the following form: self.port_<PORT NAME>
            
            Data is passed to the serviceFunction through by reading from input streams
            (BulkIO only). UDP multicast (dataSDDS and dataVITA49) ports do not support
            streams.

            The input stream from which to read can be requested with the getCurrentStream()
            method. The optional argument to getCurrentStream() is a floating point number that
            specifies the time to wait in seconds. A zero value is non-blocking. A negative value
            is blocking.  Constants have been defined for these values, bulkio.const.BLOCKING and
            bulkio.const.NON_BLOCKING.

            More advanced uses of input streams are possible; refer to the REDHAWK documentation
            for more details.

            Input streams return data blocks that include the SRI that was in effect at the time
            the data was received, and the time stamps associated with that data.

            To send data using a BulkIO interface, create an output stream and write the
            data to it. When done with the output stream, the close() method sends and end-of-
            stream flag and cleans up.

            If working with complex data (i.e., the "mode" on the SRI is set to 1),
            the data block's complex attribute will return True. Data blocks provide a
            cxdata attribute that gives the data as a list of complex values:

                if block.complex:
                    outData = [val.conjugate() for val in block.cxdata]
                    outputStream.write(outData, block.getStartTime())

            Interactions with non-BULKIO ports are left up to the device developer's discretion.

        Messages:
    
            To receive a message, you need (1) an input port of type MessageEvent, (2) a message prototype described
            as a structure property of kind message, (3) a callback to service the message, and (4) to register the callback
            with the input port.
        
            Assuming a property of type message is declared called "my_msg", an input port called "msg_input" is declared of
            type MessageEvent, create the following code:
        
            def msg_callback(self, msg_id, msg_value):
                print msg_id, msg_value
        
            Register the message callback onto the input port with the following form:
            self.port_input.registerMessage("my_msg", AVS4000_i.MyMsg, self.msg_callback)
        
            To send a message, you need to (1) create a message structure, and (2) send the message over the port.
        
            Assuming a property of type message is declared called "my_msg", an output port called "msg_output" is declared of
            type MessageEvent, create the following code:
        
            msg_out = AVS4000_i.MyMsg()
            this.port_msg_output.sendMessage(msg_out)

    Accessing the Application and Domain Manager:
    
        Both the Application hosting this Component and the Domain Manager hosting
        the Application are available to the Component.
        
        To access the Domain Manager:
            dommgr = self.getDomainManager().getRef();
        To access the Application:
            app = self.getApplication().getRef();
        Properties:
        
            Properties are accessed directly as member variables. If the property name is baudRate,
            then accessing it (for reading or writing) is achieved in the following way: self.baudRate.

            To implement a change callback notification for a property, create a callback function with the following form:

            def mycallback(self, id, old_value, new_value):
                pass

            where id is the property id, old_value is the previous value, and new_value is the updated value.
            
            The callback is then registered on the component as:
            self.addPropertyChangeListener('baudRate', self.mycallback)

        Logging:

            The member _baseLog is a logger whose base name is the component (or device) instance name.
            New logs should be created based on this logger name.

            To create a new logger,
                my_logger = self._baseLog.getChildLogger("foo")

            Assuming component instance name abc_1, my_logger will then be created with the 
            name "abc_1.user.foo".
            
        Allocation:
            
            Allocation callbacks are available to customize a Device's response to an allocation request. 
            Callback allocation/deallocation functions are registered using the setAllocationImpl function,
            usually in the initialize() function
            For example, allocation property "my_alloc" can be registered with allocation function 
            my_alloc_fn and deallocation function my_dealloc_fn as follows:
            
            self.setAllocationImpl("my_alloc", self.my_alloc_fn, self.my_dealloc_fn)
            
            def my_alloc_fn(self, value):
                # perform logic
                return True # successful allocation
            
            def my_dealloc_fn(self, value):
                # perform logic
                pass
            
        Example:
        
            # This example assumes that the device has two ports:
            #   - A provides (input) port of type bulkio.InShortPort called dataShort_in
            #   - A uses (output) port of type bulkio.OutFloatPort called dataFloat_out
            # The mapping between the port and the class if found in the device
            # base class.
            # This example also makes use of the following Properties:
            #   - A float value called amplitude
            #   - A boolean called increaseAmplitude
            
            inputStream = self.port_dataShort_in.getCurrentStream()
            if not inputStream:
                return NOOP

            outputStream = self.port_dataFloat_out.getStream(inputStream.streamID)
            if not outputStream:
                outputStream = self.port_dataFloat_out.createStream(inputStream.sri)

            block = inputStream.read()
            if not block:
                if inputStream.eos():
                    outputStream.close()
                return NOOP

            if self.increaseAmplitude:
                scale = self.amplitude
            else:
                scale = 1.0
            outData = [float(val) * scale for val in block.data]

            if block.sriChanged:
                outputStream.sri = block.sri

            outputStream.write(outData, block.getStartTime())
            return NORMAL
            
        """
        #
        # When the avs4000Transceiver is just providing control, then just
        # FIXME: Need to test to see what happens when the this loop is just
        #        left to run, it should just work.
        #
        # This should be a configurable parameter!
        # 
        self._baseLog.debug("--> process()")

        for index in self.devices_:
            streamID = self.devices_[index].stream_id()

            #
            # If the device was setup to NOT read data from avs4000d device controller then
            # return NOOP to indicate no data.
            #
            if self.devices_[index].read_data_flag() is False:
                self._baseLog.debug("    read_data <FALSE>")
                self._baseLog.debug("<-- process()")
                return NOOP

            if self.devices_[index].output_format() == AVS4000Transceiver.COMPLEXOutputFormat:
                """
                Physical device is configured to prduce complex samples of unsigned short I & Q.  These
                will be passed along to consumer via BulkIO
                """
                self._baseLog.debug("    Before read {:.4f}".format(time.time()))
                data = self.devices_[index].get_data_complex()
                self._baseLog.debug("    After  read {:.4f}".format(time.time()))

                if data is None:
                    self._baseLog.debug("   data is None")
                    self._baseLog.debug("<-- process()")
                    return NOOP

                utcNow = bulkio.timestamp.now()

                if self.devices_[index].sri_changed():
                    sri = bulkio.sri.create(streamID)
                    sri.xdelta = 1.0/self.devices_[index].sample_rate()
                    sri.mode   = 1  # Tell follow on processing that the mode is complex
                    self.port_dataShort_out.pushSRI(sri)

                    self._baseLog.info("    Pushed SRI <{}>".format(sri))

                self._baseLog.debug("    streamId <{}>, len <{}>, type data[0] <{}>".format(streamID, len(data), type(data[0])))
                self._baseLog.debug("    Before push {:.4f}".format(time.time()))
                self.port_dataShort_out.pushPacket(data, utcNow, False, streamID)
                self._baseLog.debug("    After  push {:.4f}".format(time.time()))

            elif self.devices_[index].output_format() == AVS4000Transceiver.VITA49OutputFormat:
                the_start_time = time.time()

                """
                Physical device is configured to produce Vita49 Pakcets that contain complex samples unsigned short 
                I & Q.  The samples will be extracted from the packet and passed to the consumer via BulkIO.  The
                timestamp information in the packet will be extracted and used to calculate the timestamp.
                """
                self._baseLog.debug("    Before read {:.4f}".format(time.time()))
                #
                # NOTE:
                #   The following line is commented out because during testing it was discovered that pushing
                #   small packets over BULKIO caused jumping audio from the FM demod. The DeviceController object
                #   will bundle the payload of 64 Vita49 Packets together with a signle timestamp.
                #
                #the_list = self.devices_[index].get_data_vita49()
                the_list = self.devices_[index].get_data_vita49_single_timestamp()
                self._baseLog.debug("    After  read {:.4f}".format(time.time()))

                if the_list is None:
                    self._baseLog.debug("    data is None")
                    self._baseLog.debug("<-- process()")
                    return NOOP

                #
                # Create the timestamp, because I am vita49, pull the integer portion from vrt
                # calculate the fractional portion from the master.sampleRate.
                #
                # NOTE:
                #   The value for the master.sampleRate is obtained whenever the devices tune() method is
                #   called
                #
                the_master_info = self.devices_[index].master()

                if len(the_list) != 1:
                    self._baseLog.error("Received more than one packet!!!!")

                for the_packet in the_list:
                    the_vrt = the_packet.vrt_header()

                    the_frame_count = the_packet.vrl().frame_count()

                    if self.expected_frame_count_ == -1:
                        self.expected_frame_count_ = 0

                    if the_frame_count != self.expected_frame_count_:
                        self._baseLog.error("Missing frame expected {} received {}".format(self.expected_frame_count_, the_frame_count))
                        self.expected_frame_count_ = the_frame_count + 1
                    else:
                        self.expected_frame_count_ += 64 # FIXME: need to increment by the number of buffered packets.

                    if self.expected_frame_count_ > 4095:
                        self.expected_frame_count_ = 0

                    the_data = the_packet.payload()
                    the_fractional_seconds = the_vrt.fractional_seconds_timestamp_lsw() * (1.0 / the_master_info.sampleRate())
                    the_timestamp = bulkio.timestamp.create(the_vrt.integer_seconds_timestamp(), the_fractional_seconds, tsrc=0)

                    if self.devices_[index].sri_changed():
                        sri = bulkio.sri.create(streamID)
                        sri.xdelta = 1.0/self.devices_[index].sample_rate()
                        sri.mode   = 1  # Tell follow on processing that the mode is complex

                        self._baseLog.info("    Pushing SRI: <{}>".format(sri))
                        self.port_dataShort_out.pushSRI(sri)

                    self._baseLog.debug("    streamId <{}>, len <{}>, type data[0] <{}>".format(streamID, len(the_data), type(the_data[0])))
                    self._baseLog.debug("    Before push {:.4f}".format(time.time()))
                    self.port_dataShort_out.pushPacket(the_data, the_timestamp, False, streamID)
                    self._baseLog.debug("    After  push {:.4f}".format(time.time()))

                #self._baseLog.info("Total time for call <{}>".format(time.time() - the_start_time))
            else:
                self._baseLog.debug("    Unknown format()")
                self._baseLog.debug("<-- process()")
                return NOOP

        self._baseLog.debug("<-- process()")
        return NORMAL

    '''
    *************************************************************
    Functions servicing the tuner control port
    *************************************************************'''
    def getTunerType(self,allocation_id):

        self._baseLog.info("--> getTunerType()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerType()")

        return self.frontend_tuner_status[idx].tuner_type

    def getTunerDeviceControl(self,allocation_id):
        self._baseLog.info("--> getTunerDeviceControl()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")
        if self.getControlAllocationId(idx) == allocation_id:

            self._baseLog.info("<-- getTunerDeviceControl()")

            return True

        self._baseLog.info("<-- getTunerDeviceControl()")

        return False

    def getTunerGroupId(self,allocation_id):
        self._baseLog.info("--> getTunerGroupId()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerGroupId()")

        return self.frontend_tuner_status[idx].group_id

    def getTunerRfFlowId(self,allocation_id):
        self._baseLog.info("--> getTunerRfFlowId()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerRfFlowId()")

        return self.frontend_tuner_status[idx].rf_flow_id


    def setTunerCenterFrequency(self,allocation_id, freq):
        self._baseLog.info("--> setTunerCenterFrequency()")

        idx = self.getTunerMapping(allocation_id)

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        if allocation_id != self.getControlAllocationId(idx):
            raise FRONTEND.FrontendException(("ID "+str(allocation_id)+" does not have authorization to modify the tuner"))

        if freq<0:
            raise FRONTEND.BadParameterException("Center frequency cannot be less than 0")

        # set hardware to new value. Raise an exception if it's not possible
        self.frontend_tuner_status[idx].center_frequency = freq

        self._baseLog.info("<-- getTunerCenterFrequency()")

    def getTunerCenterFrequency(self,allocation_id):
        self._baseLog.info("--> getTunerCenterFrequency()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerCenterFrequency()")

        return self.frontend_tuner_status[idx].center_frequency

    def setTunerBandwidth(self, allocation_id, bw):
        self._baseLog.info("--> setTunerBandwidth()")

        idx = self.getTunerMapping(allocation_id)

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        if allocation_id != self.getControlAllocationId(idx):
            raise FRONTEND.FrontendException(("ID "+str(allocation_id)+" does not have authorization to modify the tuner"))

        if bw < 0:
            raise FRONTEND.BadParameterException("Bandwidth cannot be less than 0")

        # set hardware to new value. Raise an exception if it's not possible
        self.frontend_tuner_status[idx].bandwidth = bw

        self._baseLog.info("<-- setTunerBandwidth()")

    def getTunerBandwidth(self, allocation_id):
        self._baseLog.info("--> getTunerBandwidth()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerBandwidth()")

        return self.frontend_tuner_status[idx].bandwidth

    def setTunerAgcEnable(self, allocation_id, enable):
        self._baseLog.info("--> setTunerAgcEnable()")

        self._baseLog.info("<-- setTunerAgcEnable()")

        raise FRONTEND.NotSupportedException("setTunerAgcEnable not supported")

    def getTunerAgcEnable(self, allocation_id):
        self._baseLog.info("--> getTunerAgcEnable()")

        self._baseLog.info("<-- getTunerAgcEnable()")

        raise FRONTEND.NotSupportedException("getTunerAgcEnable not supported")

    def setTunerGain(self,allocation_id, gain):
        self._baseLog.info("--> setTunerGain()")

        self._baseLog.info("<-- setTunerGain()")

        raise FRONTEND.NotSupportedException("setTunerGain not supported")

    def getTunerGain(self,allocation_id):
        self._baseLog.info("--> getTunerGain()")

        self._baseLog.info("<-- getTunerGain()")

        raise FRONTEND.NotSupportedException("getTunerGain not supported")

    def setTunerReferenceSource(self,allocation_id, source):
        self._baseLog.info("--> setTunerReferenceSource()")

        self._baseLog.info("<-- setTunerReferenceSource()")

        raise FRONTEND.NotSupportedException("setTunerReferenceSource not supported")

    def getTunerReferenceSource(self, allocation_id):
        self._baseLog.info("--> getTunerReferenceSource()")

        self._baseLog.info("<-- getTunerReferenceSource()")

        raise FRONTEND.NotSupportedException("getTunerReferenceSource not supported")

    def setTunerEnable(self,allocation_id, enable):
        idx = self.getTunerMapping(allocation_id)

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        if allocation_id != self.getControlAllocationId(idx):
            raise FRONTEND.FrontendException(("ID "+str(allocation_id)+" does not have authorization to modify the tuner"))

        # set hardware to new value. Raise an exception if it's not possible
        self.frontend_tuner_status[idx].enabled = enable

        self._baseLog.info("<-- setTunerEnable()")

    def getTunerEnable(self,allocation_id):
        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerEnable()")

        return self.frontend_tuner_status[idx].enabled

    def setTunerOutputSampleRate(self,  allocation_id, sr):
        self._baseLog.info("--> setTunerOutputSampleRate()")
        self._baseLog.info("    allocation_id <{}>, sr <{}>".format(allocation_id, sr))

    def setTunerOutputSampleRate(self,allocation_id, sr):
        idx = self.getTunerMapping(allocation_id)

        self._baseLog.info("    idx <{}>".format(idx))

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        if allocation_id != self.getControlAllocationId(idx):
            raise FRONTEND.FrontendException(("ID "+str(allocation_id)+" does not have authorization to modify the tuner"))

        if sr < 0:
            raise FRONTEND.BadParameterException("Sample rate cannot be less than 0")

        #
        # set hardware to new value. Raise an exception if it's not possible
        #

        self.frontend_tuner_status[idx].sample_rate = sr

        self._baseLog.info("<-- setTunerOutputSampleRate()")

    def getTunerOutputSampleRate(self, allocation_id):
        self._baseLog.info("--> getTunerOutputSampleRate()")

        idx = self.getTunerMapping(allocation_id)

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerOutputSampleRate()")

        return self.frontend_tuner_status[idx].sample_rate

    '''
    *************************************************************
    Functions servicing the RFInfo port(s)
    - port_name is the port over which the call was received
    *************************************************************'''
    def get_rf_flow_id(self,port_name):
        self._baseLog.info("--> get_rf_flow_id()")

        self._baseLog.info("<-- get_rf_flow_id()")
        return ""

    def set_rf_flow_id(self,port_name, _id):
        self._baseLog.info("--> set_rf_flow_id()")

        self._baseLog.info("<-- set_rf_flow_id()")
        pass

    def get_rfinfo_pkt(self,port_name):
        self._baseLog.info("--> get_rfinfo_pkt()")

        _antennainfo    = FRONTEND.AntennaInfo('','','','')
        _freqrange      = FRONTEND.FreqRange(0,0,[])
        _feedinfo       = FRONTEND.FeedInfo('','',_freqrange)
        _sensorinfo     = FRONTEND.SensorInfo('','','',_antennainfo,_feedinfo)
        _rfcapabilities = FRONTEND.RFCapabilities(_freqrange,_freqrange)
        _rfinfopkt      = FRONTEND.RFInfoPkt('',0.0,0.0,0.0,False,_sensorinfo,[],_rfcapabilities,[])

        self._baseLog.info("<-- get_rfinfo_pkt()")

        return _rfinfopkt

    def set_rfinfo_pkt(self,port_name, pkt):
        pass

    '''
    *************************************************************
    Functions supporting tuning allocation
    *************************************************************'''
    def deviceEnable(self, fts, tuner_id):
        '''
        ************************************************************
        modify fts, which corresponds to self.frontend_tuner_status[tuner_id]
        Make sure to set the 'enabled' member of fts to indicate that tuner as enabled
        ************************************************************
        '''

        self._baseLog.info("--> deviceEnable()")
        self._baseLog.info("    fts<{}>".format(fts))
        self._baseLog.info("    tuner_id<{}>".format(tuner_id))

        try:
            #
            # The following commented code was put here to make sure that the
            # AVS4000Transceiver software was not connecting to the data port
            #
            # FIXME: This should be removed later
            #
            #the_level = self.devices_[tuner_id].get_loglevel()
            #self.devices_[tuner_id].set_loglevel(logging.DEBUG)

            self.devices_[tuner_id].enable()

            #
            # FIXME: I should create an initializtion method to centralize setting up values.
            #
            self.expected_frame_count_ = -1

            self._baseLog.info("Device:\n{}".format(self.devices_[tuner_id]))

            #self.devices_[tuner_id].set_loglevel(the_level)

        except RuntimeError as the_error:
            self._baseLog.error("Unable to start because: <{}>".format(str(the_error)))
            fts.enabled = False
            return

        fts.enabled = True

        self._baseLog.info("<-- deviceEnable()")
        return

    def deviceDisable(self,fts, tuner_id):
        '''
        ************************************************************
        modify fts, which corresponds to self.frontend_tuner_status[tuner_id]
        Make sure to reset the 'enabled' member of fts to indicate that tuner as disabled
        ************************************************************'''
        self._baseLog.info("--> deviceDisable()")
        self._baseLog.info("    fts<{}>".format(fts))
        self._baseLog.info("    tuner_id<{}>".format(tuner_id))

        try:
            self._baseLog.info("    calling disable()")
            self.devices_[tuner_id].disable()

        except RuntimeError as the_error:
            self._baseLog.error("There was a problem stopping the device, because <{}>".format(str(the_error)))

        fts.enabled = False

        self._baseLog.info("<-- deviceDisable()")
        return

    def deviceSetTuning(self, request, fts, tuner_id):
        '''
        ************************************************************
        modify fts, which corresponds to self.frontend_tuner_status[tuner_id]
        
        The bandwidth, center frequency, and sampling rate that the hardware was actually tuned
        to needs to populate fts (to make sure that it meets the tolerance requirement. For example,
        if the tuned values match the requested values, the code would look like this:
        
        fts.bandwidth = request.bandwidth
        fts.center_frequency = request.center_frequency
        fts.sample_rate = request.sample_rate
        
        return True if the tuning succeeded, and False if it failed
        ************************************************************'''

        self._baseLog.info("--> deviceSetTuning()")
        self._baseLog.info("    Evaluate whether or not a tuner is added  *********")
        self._baseLog.info("    request <{}>, type<{}>".format(request, type(request)))
        self._baseLog.info("    fts <{}>, type<{}>".format(fts, type(fts)))
        self._baseLog.info("    tuner_id <{}>, type<{}>".format(tuner_id, type(tuner_id)))

        '''
        FIXME:
            - Check to make sure the parameters are within range of the physical device,  
              If there is a problem then return BadParameterException.
            - Should I just ignore the bandwidth?
        '''
        the_bandwidth        = request.bandwidth
        the_center_frequency = request.center_frequency
        the_sampe_rate       = request.sample_rate

        try:
            #
            # Send the tune request to the device
            #    I am mapping the tuner id directly to how the devices are found and added to the
            #    devices_ map.  As an example the first device found has id 0, and the next device
            #    found has turner id 1, etc.
            #
            loglevel = self.devices_[tuner_id].loglevel()
            #self.devices_[tuner_id].set_loglevel(logging.DEBUG)
            self.devices_[tuner_id].set_tune(the_center_frequency, the_bandwidth, the_sampe_rate)
            #self.devices_[tuner_id].set_loglevel(loglevel)
            #
            # NOTE:
            #    It is no longer necessary to tell the transceiver whether it should read the data
            #    or let a component make the TCP/IP connection to the device controller.
            #    This is now being handled during construction or via the output_configuration change callback.
            #    Previously had to perform the following: self.devices_[tuner_id].set_read_data(False)
            #

            #
            # Update internal status information
            #
            fts.bandwidth        = the_bandwidth
            fts.center_frequency = the_center_frequency
            fts.sample_rate      = the_sampe_rate
            fts.complex          = True

            self._baseLog.info("Device:\n{}".format(self.devices_[tuner_id]))

        except RuntimeError as the_error:
            self._baseLog.error("Tune failed, because: {}".format(str(the_error)))
            return False

        self._baseLog.info("<-- deviceSetTuning()")
        return True

    def deviceDeleteTuning(self, fts, tuner_id):
        '''
        ************************************************************
        modify fts, which corresponds to self.frontend_tuner_status[tuner_id]
        return True if the tune deletion succeeded, and False if it failed
        ************************************************************
        '''
        self._baseLog.info("--> deviceDeleteTuning()")
        self._baseLog.info("    Deallocate an allocated tuner  *********")

        '''
        FIXME:  What is the difference between a deleteTune and a deviceDelete?
        '''

        self.devices_[tuner_id].delete_tune()

        fts.enabled = False

        self._baseLog.info("<-- deviceDeleteTuning()")
        return True


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.debug("Starting Device")
    start_device(AVS4000_i)

