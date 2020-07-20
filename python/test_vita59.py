import unittest
import Vita49
import logging

class TestVita49VRL_methods(unittest.TestCase):
    def setUp(self):
        the_list = [0x56, 0x52, 0x4c, 0x50, 0x00, 0x20, 0x08, 0x00]
        the_bytes = bytearray(the_list)

        self.vrl = Vita49.VRL(the_bytes)

    def test_faw(self):
        if self.vrl.faw() != 0x56524c50:
            return False

        return True

    def test_frame_count(self):
        if self.vrl.frame_count() != 0x20:
            return False

        return True

    def test_frame_size(self):
        if self.vrl.frame_size() != 0x0800:
            return False

        return True


class TestVita49VRT_methods(unittest.TestCase):
    def setUp(self):

        the_list =\
            [
                0x10, 0x53, 0x07, 0xFD,  # Header
                0x00, 0x00, 0x00, 0x00,  # Stream Id
                0x11, 0x22, 0x33, 0x44,  # Integer Seconds Timestamp
                0x55, 0x55, 0x55, 0x55,  # Fractional Seconds Timestamp MSW
                0x66, 0x66, 0x66, 0x66   # Fractional Seconds Timestamp LSW
            ]

        the_bytes = bytearray(the_list)
        try:
            self.vrt = Vita49.VRT(the_bytes, Vita49.BIG_ENDIAN, logging.INFO)
        except RuntimeError as the_error:
            print("Unable to create vrt because <{}>".format(str(the_error)))


    def test_header(self):
        if self.vrt.header() != 0x105207fd:
            return False

        return True

    def test_stream_id(self):
        if self.vrt.stream_id() != 0:
            return False

        return True

    def test_ist(self):
        if self.vrt.integer_seconds_timestamp() != 0x11223344:
            return False

        return True

    def test_fst_msw(self):
        if self.vrt.fractional_seconds_timestamp_msw() != 0x55555555:
            return False

        return True

    def test_fst_lsw(self):
        if self.vrt.fractional_seconds_timestamp_lsw() != 0x66666666:
            return False

        return True

    def test_packet_type(self):
        if self.vrt.packet_type() != 1:
            return False

        return True

    def test_c(self):
        if self.vrt.c() != 0:
            return False

        return True

    def test_t(self):
        if self.vrt.t() != 0:
            return False

        return True

    def test_rr(self):
        if self.vrt.rr() != 0:
            return False

        return True

    def test_tsi(self):
        if self.vrt.tsi() != 1:
            return False

        return True

    def test_tsf(self):
        if self.vrt.tsf() != 1:
            return False

        return True

    def test_packet_count(self):
        if self.vrt.packet_count() != 0x3:
            return False

        return True

    def test_packet_size(self):
        if self.vrt.packet_size() != 0x07FD:
            return False

        return True

if __name__ == '__main__':
    unittest.main()