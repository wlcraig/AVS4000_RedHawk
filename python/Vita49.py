import struct
import logging

"""
This file is specific to the AVS4000
"""

LITTLE_ENDIAN = "little"
BIG_ENDIAN    = "big"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s @ %(lineno)d')

module_logger = logging.getLogger('Vita49')

VRL_OFFSET          = 0 # Number of bytes from start of frame VRL is located
VRT_OFFSET          = 8 # Number of bytes from start of frame VRT Header is located
VRT_PAYLOAD_OFFSET = 28 # Number of bytes from start of VRL + VRT frame payload in bytes.

VRT_PACKET_SIZE    = 8192

class VRL:
    """
    Use this object to extract the VRL information from a byte stream
    """
    EXPECTED_FAW         = 0x56524c50 # VRLP, in big endian format
    EXPECTED_FEND        = 0x56454E44 # VEND, in big endian format
    EXPECTED_FRAME_SIZE  = 0x800

    SIZE        = 8    # Number of bytes in VRL Header.
    FAW_OFFSET  = 0    # int[0],    byte[0]     contains FAW
    FCFS_OFFSET = 1    # int[1],    byte[4]     contains Frame Counter, Frame Size
    FEND_OFFSET = 8188 # int[2047], byte[8188], contains FEND

    #
    # The bit manipulation constants
    #
    _frame_size_bit_mask_ = 0x0000ffff
    _frame_count_shift_   = 20

    def __init__(self, the_buffer, the_byte_order=BIG_ENDIAN, loglevel=logging.INFO):
        """
        Constructor

        :param the_buffer:      A bytearray of length 8 bytes
        :param the_byte_order:  What order to unpack the bytes
        :param loglevel:        What log level to run object with

        """
        self.logger_ = logging.getLogger('Vita49.VRL')
        self.logger_.setLevel(loglevel)

        self.logger_.debug("--> __init__()")

        if len(the_buffer) < VRL.SIZE:
            assert RuntimeError("Not enough bytes to process VRL")

        if the_byte_order == LITTLE_ENDIAN:
            self.format_ = LITTLE_ENDIAN
            the_format = "<"            # see struct.unpack section

        else:
            self.format_ = BIG_ENDIAN
            the_format = ">"

        the_format += "I" * (VRL.SIZE / 4)
        the_list = struct.unpack(the_format, the_buffer[:VRL.SIZE])

        self.faw_         = the_list[VRL.FAW_OFFSET]                           # First integer in the list
        self.frame_size_  = the_list[VRL.FCFS_OFFSET]  & self._frame_size_bit_mask_   # Second integer in list, first 12 bits
        self.frame_count_ = the_list[VRL.FCFS_OFFSET] >> self._frame_count_shift_     # Second integer in list, last 16 bits.

        self.logger_.debug("<-- __init__()")

    def __str__(self):
        """
        Use this method to provide a string representation of the object.

        :return:
          a string
        """
        the_string = \
            "format      <{3}>\n"\
            "faw         <{0:#010x}>\n"\
            "frame_size  <{1}>\n"\
            "frame_count <{2}>\n"\
            .format\
                (
                    self.faw_,
                    self.frame_size_,
                    self.frame_count_,
                    self.format_
                )
        return the_string

    def faw(self):
        """
        Accessor method, that returns the FAW recovered from the byte array.

        :return:
          an integer representing the faw
        """
        return self.faw_

    def frame_count(self):
        """
        Accessor method that returns the frame number sent by device.

        :return:
           an integer representing the frame_count
        """
        return self.frame_count_

    def frame_size(self):
        """
        Accessor method, that returns the number of 32bit words in the frame

        :return:
          an integer representing the frame_size
        """
        return self.frame_size_


class VRT:
    """
    Use this class to extract the VRT contents of a Vita49.0/2 data stream
    """

    HDR_SIZE              = 20  # The number of bytes comprising the VRT Header

    HDR_OFFSET            = 0 # int[0]contains, PKT Type, C, T, RR, TSI, TSF, PKT Count, PKT Size
    STREAM_ID_OFFSET      = 1 # int[1], Stream ID
    IST_OFFSET            = 2 # int[2], Integer Seconds Timestamp
    FST_MSW_OFFSET        = 3 # int[3], Fractional Timestam  MSW
    FST_LSW_OFFSET        = 4 # int[3], Fractional Timestam  MSW

    EXPECTED_PACKET_TYPE = 0x1
    EXPECTED_C           = 0x0
    EXPECTED_T           = 0x0
    EXPECTED_TSI         = 0x1
    EXPECTED_TSF         = 0x1
    EXPECTED_PACKET_SIZE = 0x7FD # 2045 Words/2045 Complex.

    #
    # The following are the bit masks and shifts used to convert the VITA49 packet to something
    # meaningful.  These values are used to extract the values associated with the respective
    # field of the Vita49.0/1 packet.
    #
    _packet_type_shift_ = 28
    _c_mask_            = 0x08000000
    _c_shift_           = 27
    _t_mask_            = 0x04000000
    _t_shift_           = 26
    _rr_mask_           = 0x03000000
    _rr_shift_          = 24
    _tsi_mask_          = 0x00C00000
    _tsi_shift_         = 22
    _tsf_mask_          = 0x00300000
    _tsf_shift_         = 20
    _pkt_count_mask_    = 0x000F0000
    _pkt_count_shift_   = 16
    _pkt_size_mask_     = 0x0000FFFF

    def __init__(self, the_buffer, the_byte_order=BIG_ENDIAN, loglevel=logging.INFO):
        """
        Constructor

        :param the_buffer:      The byte array containing packet with a length of 20 bytes (5 32bit words).
        :param the_byte_order:  The byte order to use when unpacking the payload.
        :param loglevel:        The loglevel to use for the object.
        """

        self.logger_ = logging.getLogger('Vita49.VRT')
        self.logger_.setLevel(loglevel)

        self.logger_.debug("--> __init__()")

        if len(the_buffer) < VRT.HDR_SIZE:
            self.logger_.debug("<-- __init__() RuntimeError")
            assert RuntimeError("Not enough bytes to process VRL")

        if the_byte_order == LITTLE_ENDIAN:
            self.format_ = LITTLE_ENDIAN
            the_format = "<"  # see struct.unpack section

        else:
            self.format_ = BIG_ENDIAN
            the_format = ">"

        the_format += "I" * (VRT.HDR_SIZE / 4)
        the_list = struct.unpack(the_format, the_buffer[:VRT.HDR_SIZE])

        self.header_    = the_list[VRT.HDR_OFFSET]
        self.stream_id_ = the_list[VRT.STREAM_ID_OFFSET]
        self.ist_       = the_list[VRT.IST_OFFSET]
        self.fst_msw_   = the_list[VRT.FST_MSW_OFFSET]
        self.fst_lsw_   = the_list[VRT.FST_LSW_OFFSET]

        self.logger_.debug("<-- __init__()")

    def __str__(self):
        """
        Used for debugging and printing the contents of the object.

        :return: A string representation of the object.
        """
        the_string = \
            "header     <{0:#010x}>\n"\
            "stream_id  <{1:#010x}>\n"\
            "ist        <{2:#010x}>\n" \
            "fst_msw    <{3:#010x}>\n" \
            "fst_lsw    <{4:#010x}>\n"\
            .format\
                (
                    self.header_,
                    self.stream_id_,
                    self.ist_,
                    self.fst_msw_,
                    self.fst_lsw_
                )

        return the_string

    def header(self):
        """
        Acessor method, that returns integer value of the first 32bit word of the VRT information.

        :return: the integer value fo the header word
        """

        return self.header_

    def packet_type(self):
        """
        Accessor method, that returns value of packet_type field

        :return: integer value of the packet_type field
        """
        the_value = self.header_ >> self._packet_type_shift_
        return the_value

    def c(self):
        """
        Accessor method, that returns value of c field

        :return: integer value of the c field.
        """
        the_value = (self.header_ & self._c_mask_) >> self._c_shift_
        return the_value

    def t(self):
        """
        Accessor method, that returns value of t field
        :return:
        """
        the_value = (self.header_ & self._t_mask_) >> self._t_shift_
        return the_value

    def rr(self):
        """
        Accessor method, that returns value of rr field

        :return:
           integer value of the rr field
        """
        the_value = (self.header_ & self._rr_mask_) >> self._rr_shift_
        return the_value

    def tsi(self):
        """
        Accessor method, that returns the value of the tsi field

        :return:
           integer value of the tsi field
        """
        the_value = (self.header_ & self._tsi_mask_) >> self._tsi_shift_
        return the_value

    def tsf(self):
        """
        Accessor method, that returns the value fo the tsf field

        :return:
             integer value of the tsf field.
        """
        the_value = (self.header_ & self._tsf_mask_) >> self._tsf_shift_
        return the_value

    def packet_count(self):
        """
        Accessor method, that returns the current packet_count field.

        NOTE:
          this value will roll over as it is only 4 bits in length.

        :return:
            integer value of the packet_count field.
        """
        the_value = (self.header_ & self._pkt_count_mask_) >> self._pkt_count_shift_
        return(the_value)

    def packet_size(self):
        """
        Acessor method, that returns the packet_size field.

        :return:
            integer value of the packet_size field
        """
        the_value = self.header_ & self._pkt_size_mask_
        return(the_value)

    def stream_id(self):
        """
        Acessor method, that returns the current stream_id field

        :return:
          integer value of the stream_id field.
        """
        return self.stream_id_

    def integer_seconds_timestamp(self):
        """
        Acessor method, that returns the current integer seconds timestamp field

        :return:
           integer value of the integer_time_stamp field
        """
        return self.ist_

    def fractional_seconds_timestamp_msw(self):
        """
        Accessor method, that returns the current fractiona_seconds_timestamp_msw field

        :return:
          integer value of the fractional_seconds_timestamp_msw field
        """
        return self.fst_msw_

    def fractional_seconds_timestamp_lsw(self):
        """
        Accessor method, that returns the current fractional_seconds_timestamp_lsw field.

        :return:
          integer value of the fractional_seconds_timestamp_lsw fied.
        """
        return self.fst_lsw_

    def number_payload_words(self):
        """
        Accessor method, returns the number of 32bit works contained in the payload

        :return:
           integer
        """
        return self.packet_size() - (self.HDR_SIZE / 4)

class Vita49DataPacket:
    """
    This object encapsulates a the VRL, VRT and Payload components of a Vita49.0/1 packet.
    It is intended to provide a way to treat the extracted information from a data stream
    as a single object.
    """
    def __init__(self, the_vrl, the_vrt_header, the_payload_tuple):
        """
        Constructor
        :param the_vrl:           This is a Vita49.VRL object
        :param the_vrt_header:    This is a Vita49.VRT object
        :param the_payload_tuple: This is the payload extracted from the data stream as a tuple of
                                  signed 16Bit values.
        """
        self.vrl_        = the_vrl
        self.vrt_header_ = the_vrt_header
        self.payload_    = list(the_payload_tuple)

    def vrl(self):
        """
        Accessor method to obtain the VRL object.

        :return: Vita49.VRL object.
        """
        return self.vrl_

    def vrt_header(self):
        """
        Accessor method to obtain the VRT object.

        :return: Vita49.VRT object
        """
        return self.vrt_header_

    def payload(self):
        """
        Accessor method to obtain the payload

        :return: A list of 16bit unsigned shorts.
        """
        return self.payload_

    def extend(self, the_tuple):
        """
        Use this method to extend the payload list with additional items.
        Written to specifically extend the array with the results from struct.unpack.

        :param the_tuple: The tuple of complex values, where I and Q are signed short 16bit values.

        :return:  N/A
        """
        self.payload_.extend(the_tuple)