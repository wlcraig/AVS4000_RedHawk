Date: 	04/Aug/2020
Driver: avs4000-0.51-1.el7.x86_64

Notes:
	- This version of the device driver writes data out the data port in 
          Little Endian Byte format.

General:
	The device supports the following:
	 1. Reading complex data from the avs4000d data port
	 2. Reading vita49 packets from teh avs4000d data port
	 3. Controlling the AVS400d to produce a TCP/IP stream of complex data to 
            be consumed by waveform using sourceSocket.

	See Also:
	    Project			Type		Description
	    -------			----		------------
	 1. AVS4000_Vita49_Bulkio	Node		Sets up device to produce vita49 data and 
							push data out the datashort port via bulkio.
							Use avs4000_test_01 waveform to test.

	 2. AVS4000_Complex_Bulkio 	Node		Sets up device to produce complex data and 
							push data out dataShort port via bulkio.
							Use avs4000_test_01 waveform to test.

	 3. AVS4000_Complex_Socket 	Node		Sets up defice to produce complex data, 
							expects waveform to read from data port
							Use avs4000_test_03 waveform to test.

	 4. avs4000_test_01        	Waveform	Used to test the AVS4000_{Vita49,Complex)_Bulkio 
							nodes

	 5. avs4000_test_03		Waveform	Used to test the AVS4000_Complex_Socket node.

