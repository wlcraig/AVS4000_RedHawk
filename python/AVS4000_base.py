#!/usr/bin/env python
#
# AUTO-GENERATED CODE.  DO NOT MODIFY!
#
# Source: AVS4000.spd.xml
from ossie.cf import CF
from ossie.cf import CF__POA
from ossie.utils import uuid

from frontend import FrontendTunerDevice
from frontend import digital_tuner_delegation
from frontend import rfinfo_delegation
from ossie.threadedcomponent import *
from ossie.properties import simple_property
from ossie.properties import simpleseq_property
from ossie.properties import struct_property
from ossie.properties import structseq_property

import Queue, copy, time, threading
from ossie.resource import usesport, providesport, PortCallError
import bulkio
import frontend
from frontend import FRONTEND
from ossie.properties import struct_to_props
BOOLEAN_VALUE_HERE=False
from omniORB import any as _any

class enums:
    # Enumerated values for avs4000_output_configuration::
    class avs4000_output_configuration__:
        # Enumerated values for avs4000_output_configuration::output_format
        class output_format:
            COMPLEX = "COMPLEX_Format"
            VITA49 = "VITA49_Format"

class AVS4000_base(CF__POA.Device, FrontendTunerDevice, digital_tuner_delegation, rfinfo_delegation, ThreadedComponent):
        # These values can be altered in the __init__ of your derived class

        PAUSE = 0.0125 # The amount of time to sleep if process return NOOP
        TIMEOUT = 5.0 # The amount of time to wait for the process thread to die when stop() is called
        DEFAULT_QUEUE_SIZE = 100 # The number of BulkIO packets that can be in the queue before pushPacket will block

        def __init__(self, devmgr, uuid, label, softwareProfile, compositeDevice, execparams):
            FrontendTunerDevice.__init__(self, devmgr, uuid, label, softwareProfile, compositeDevice, execparams)
            ThreadedComponent.__init__(self)

            self.listeners={}
            # self.auto_start is deprecated and is only kept for API compatibility
            # with 1.7.X and 1.8.0 devices.  This variable may be removed
            # in future releases
            self.auto_start = False
            # Instantiate the default implementations for all ports on this device
            self.port_RFInfo_in = frontend.InRFInfoPort("RFInfo_in", self)
            self.port_RFInfo_in._portLog = self._baseLog.getChildLogger('RFInfo_in', 'ports')
            self.port_DigitalTuner_in = frontend.InDigitalTunerPort("DigitalTuner_in", self)
            self.port_DigitalTuner_in._portLog = self._baseLog.getChildLogger('DigitalTuner_in', 'ports')
            self.port_dataVITA49_out = bulkio.OutVITA49Port("dataVITA49_out")
            self.port_dataVITA49_out._portLog = self._baseLog.getChildLogger('dataVITA49_out', 'ports')
            self.port_dataShort_out = bulkio.OutShortPort("dataShort_out")
            self.port_dataShort_out._portLog = self._baseLog.getChildLogger('dataShort_out', 'ports')
            self.device_kind = "FRONTEND::TUNER"
            self.device_model = "AVS-4000"
            self.frontend_listener_allocation = frontend.fe_types.frontend_listener_allocation()
            self.frontend_tuner_allocation = frontend.fe_types.frontend_tuner_allocation()

        def start(self):
            self._baseLog.info("--> start()")

            FrontendTunerDevice.start(self)
            ThreadedComponent.startThread(self, pause=self.PAUSE)

            self._baseLog.info("<-- start()")

        def stop(self):
            self._baseLog.info("--> stop()")

            FrontendTunerDevice.stop(self)
            if not ThreadedComponent.stopThread(self, self.TIMEOUT):
                self._baseLog.info("<-- stop()")

                raise CF.Resource.StopError(CF.CF_NOTSET, "Processing thread did not die")

            self._baseLog.info("<-- stop()")

        def releaseObject(self):
            self._baseLog.info("--> releaseObject()")

            try:
                self.stop()
            except Exception:
                self._baseLog.exception("Error stopping")

            FrontendTunerDevice.releaseObject(self)

            self._baseLog.info("<-- releaseObject()")

        ######################################################################
        # PORTS
        # 
        # DO NOT ADD NEW PORTS HERE.  You can add ports in your derived class, in the SCD xml file, 
        # or via the IDE.

        port_RFInfo_in = providesport(name="RFInfo_in",
                                      repid="IDL:FRONTEND/RFInfo:1.0",
                                      type_="data")

        port_DigitalTuner_in = providesport(name="DigitalTuner_in",
                                            repid="IDL:FRONTEND/DigitalTuner:1.0",
                                            type_="control")

        port_dataVITA49_out = usesport(name="dataVITA49_out",
                                       repid="IDL:BULKIO/dataVITA49:1.0",
                                       type_="data",
                                       description="""Vita-49 data packets"""
                                       )

        port_dataShort_out = usesport(name="dataShort_out",
                                      repid="IDL:BULKIO/dataShort:1.0",
                                      type_="data",
                                      description="""16 bit I/Q data """
                                      )

        ######################################################################
        # PROPERTIES
        # 
        # DO NOT ADD NEW PROPERTIES HERE.  You can add properties in your derived class, in the PRF xml file
        # or by using the IDE.
        class frontend_tuner_status_struct_struct(frontend.default_frontend_tuner_status_struct_struct):
            complex = simple_property(
                                      id_="FRONTEND::tuner_status::complex",
                                      
                                      name="complex",
                                      type_="boolean")
        
            decimation = simple_property(
                                         id_="FRONTEND::tuner_status::decimation",
                                         
                                         name="decimation",
                                         type_="long")
        
            gain = simple_property(
                                   id_="FRONTEND::tuner_status::gain",
                                   
                                   name="gain",
                                   type_="double")
        
            tuner_number = simple_property(
                                           id_="FRONTEND::tuner_status::tuner_number",
                                           
                                           name="tuner_number",
                                           type_="short")
        
            def __init__(self, allocation_id_csv="", bandwidth=0.0, center_frequency=0.0, complex=False, decimation=0, enabled=False, gain=0.0, group_id="", rf_flow_id="", sample_rate=0.0, tuner_number=0, tuner_type=""):
                frontend.default_frontend_tuner_status_struct_struct.__init__(self, allocation_id_csv=allocation_id_csv, bandwidth=bandwidth, center_frequency=center_frequency, enabled=enabled, group_id=group_id, rf_flow_id=rf_flow_id, sample_rate=sample_rate, tuner_type=tuner_type)
                self.complex = complex
                self.decimation = decimation
                self.gain = gain
                self.tuner_number = tuner_number
        
            def __str__(self):
                """Return a string representation of this structure"""
                d = {}
                d["allocation_id_csv"] = self.allocation_id_csv
                d["bandwidth"] = self.bandwidth
                d["center_frequency"] = self.center_frequency
                d["complex"] = self.complex
                d["decimation"] = self.decimation
                d["enabled"] = self.enabled
                d["gain"] = self.gain
                d["group_id"] = self.group_id
                d["rf_flow_id"] = self.rf_flow_id
                d["sample_rate"] = self.sample_rate
                d["tuner_number"] = self.tuner_number
                d["tuner_type"] = self.tuner_type
                return str(d)
        
            @classmethod
            def getId(cls):
                return "FRONTEND::tuner_status_struct"
        
            @classmethod
            def isStruct(cls):
                return True
        
            def getMembers(self):
                return frontend.default_frontend_tuner_status_struct_struct.getMembers(self) + [("complex",self.complex),("decimation",self.decimation),("gain",self.gain),("tuner_number",self.tuner_number)]

        class avs4000_output_configuration___struct(object):
            tuner_number = simple_property(
                                           id_="avs4000_output_configuration::tuner_number",
                                           
                                           name="tuner_number",
                                           type_="long",
                                           defvalue=0
                                           )
        
            output_format = simple_property(
                                            id_="avs4000_output_configuration::output_format",
                                            
                                            name="output_format",
                                            type_="string",
                                            defvalue="COMPLEX_Format"
                                            )
        
            def __init__(self, tuner_number=0, output_format="COMPLEX_Format"):
                self.tuner_number = tuner_number
                self.output_format = output_format
        
            def __str__(self):
                """Return a string representation of this structure"""
                d = {}
                d["tuner_number"] = self.tuner_number
                d["output_format"] = self.output_format
                return str(d)
        
            @classmethod
            def getId(cls):
                return "avs4000_output_configuration::"
        
            @classmethod
            def isStruct(cls):
                return True
        
            def getMembers(self):
                return [("tuner_number",self.tuner_number),("output_format",self.output_format)]

        avs4000_output_configuration = structseq_property(id_="avs4000_output_configuration",
                                                          structdef=avs4000_output_configuration___struct,
                                                          defvalue=[avs4000_output_configuration___struct(tuner_number=0,output_format="COMPLEX_Format")],
                                                          configurationkind=("property",),
                                                          mode="readwrite")



        # Rebind tuner status property with custom struct definition
        frontend_tuner_status = FrontendTunerDevice.frontend_tuner_status.rebind()
        frontend_tuner_status.structdef = frontend_tuner_status_struct_struct

        def frontendTunerStatusChanged(self,oldValue, newValue):
            self._baseLog.info("--> frontendTunerStatusChanged()")

            self._baseLog.info("<-- frontendTunerStatusChanged()")
            pass

        def getTunerStatus(self, allocation_id):
            self._baseLog.info("--> getTunerStatus()")

            tuner_id = self.getTunerMapping(allocation_id)

            if tuner_id < 0:
                self._baseLog.info("<-- getTunerStatus()")

                raise FRONTEND.FrontendException(("ERROR: ID: " + str(allocation_id) + " IS NOT ASSOCIATED WITH ANY TUNER!"))

            _props = self.query([CF.DataType(id='FRONTEND::tuner_status',value=_any.to_any(None))])

            self._baseLog.info("<-- getTunerStatus()")

            return _props[0].value._v[tuner_id]._v

        def assignListener(self,listen_alloc_id, allocation_id):
            # find control allocation_id
            existing_alloc_id = allocation_id
            if self.listeners.has_key(existing_alloc_id):
                existing_alloc_id = self.listeners[existing_alloc_id]
            self.listeners[listen_alloc_id] = existing_alloc_id



        def removeListener(self,listen_alloc_id):
            if self.listeners.has_key(listen_alloc_id):
                del self.listeners[listen_alloc_id]


        def removeAllocationIdRouting(self,tuner_id):
            pass

