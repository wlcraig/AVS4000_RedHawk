#!/usr/bin/env python
#
#
# AUTO-GENERATED
#
# Source: AVS4000.spd.xml
from ossie.device import start_device
import logging

import socket
import json

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
        
        self.host_    = 'localhost'
        self.devices_ = {}
        self.dm_      = AVS4000Transceiver.DeviceManager(the_host=self.host_)

        #
        # Query the number of controllers available
        #
        self.devices_ = self.dm_.get_controllers()

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

            #self.devices_[tuner_id].set_loglevel(logging.DEBUG)

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

        # TODO fill in your code here
        self._baseLog.debug("--> process()")

        for index in self.devices_:
            streamID = self.devices_[index].get_stream_id()
            data     = self.devices_[index].get_complex_data()

            if data is None:
                self._baseLog.debug("   data is None")
                self._baseLog.debug("<-- process()")
                return NOOP

            returnCode = NOOP

            if len(data) > 0:
                returnCode = NORMAL

                utcNow = bulkio.timestamp.now()

                if self.devices_[index].changed():
                    self._baseLog.info("    Pushing SRI")
                    sri = bulkio.sri.create(streamID)
                    sri.xdelta = 1.0/self.devices_[index].get_sample_rate()
                    sri.mode   = 1  # Tell follow on processing that the mode is complex

                    self.port_dataShort_out.pushSRI(sri)

                self._baseLog.debug("    streamId <{}>, len <{}>, type data[0] <{}>".format(streamID, len(data), type(data[0])))

                self.port_dataShort_out.pushPacket(data, utcNow, False, streamID)

        self._baseLog.debug("<-- process()")
        return returnCode

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
        self._baseLog.info("--> setTunerEnable()")

        idx = self.getTunerMapping(allocation_id)

        if idx < 0:
            raise FRONTEND.FrontendException("Invalid allocation id")

        if allocation_id != self.getControlAllocationId(idx):
            raise FRONTEND.FrontendException(("ID "+str(allocation_id)+" does not have authorization to modify the tuner"))

        # set hardware to new value. Raise an exception if it's not possible
        self.frontend_tuner_status[idx].enabled = enable

        self._baseLog.info("<-- setTunerEnable()")

    def getTunerEnable(self,allocation_id):
        self._baseLog.info("--> getTunerEnable()")

        idx = self.getTunerMapping(allocation_id)
        if idx < 0: raise FRONTEND.FrontendException("Invalid allocation id")

        self._baseLog.info("<-- getTunerEnable()")

        return self.frontend_tuner_status[idx].enabled

    def setTunerOutputSampleRate(self,  allocation_id, sr):
        self._baseLog.info("--> setTunerOutputSampleRate()")
        self._baseLog.info("    allocation_id <{}>, sr <{}>".format(allocation_id, sr))

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

        _antennainfo=FRONTEND.AntennaInfo('','','','')
        _freqrange=FRONTEND.FreqRange(0,0,[])
        _feedinfo=FRONTEND.FeedInfo('','',_freqrange)
        _sensorinfo=FRONTEND.SensorInfo('','','',_antennainfo,_feedinfo)
        _rfcapabilities=FRONTEND.RFCapabilities(_freqrange,_freqrange)
        _rfinfopkt=FRONTEND.RFInfoPkt('',0.0,0.0,0.0,False,_sensorinfo,[],_rfcapabilities,[])

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
            self.devices_[tuner_id].enable()

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
            #    I am mapping the tuner id directly to how the devices are found and dded to the
            #    devices_ map.  As an example the first device found has id 0, and the next device
            #    found has turner id 1, etc.
            #
            self.devices_[tuner_id].set_tune(the_center_frequency, the_bandwidth, the_sampe_rate)

            #
            # Update internal status information
            #
            fts.bandwidth        = the_bandwidth
            fts.center_frequency = the_center_frequency
            fts.sample_rate      = the_sampe_rate
            fts.complex          = True



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

