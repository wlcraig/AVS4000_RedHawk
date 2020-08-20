# Description
This project contains the redhawk components devices, nodes and waveforms that exercise the AVS4000 transciever.

# Layout
I have seperated the REDHAWK components into seperate directories.

## devices
This directory contains the AVS4000 device that works within the REDHAWK SDK. 

## nodes
This directory contains the nodes that are used to instantiate the device within the REDHAWK SDK.  There are three of them for now to exercise the different configurations of complex data out a BULKIO port, vita49 out a BULKIO port, and complex data out a socket.  

## waveforms
This dicrectory contains the waveforms used to test the devices. This is using the standard REDHAWK FM demodulator connected to the AVS4000 device

# Next Steps
## Prequsites:
* I would recommend downloading and installing the latest REDHAWK SDK from the internet URL <???>
* IDE rhide is launched and devices, nodes and waveforms are imported.

## Steps:
* Update the nodes to use the proper domain.
* Launch the AVS4000_Complex_Bulkio node 
* Launch the avs4000_test01 waveform
* Using the rhide select the external port of the waveform, and play the audio port.
