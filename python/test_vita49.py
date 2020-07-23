import unittest
import Vita49
import logging

class TestVita49VRL_methods(unittest.TestCase):
    def setUp(self):
        the_list = [0x56, 0x4c, 0x52, 0x50, 0x00, 0x20, 0x08, 0x00]
        the_bytes = bytearray(the_list)

        self.vrl = Vita49.VRL(the_bytes)

    def test_faw(self):
        self.assertEqual("{0:#010x}".format(self.vrl.faw()), "0x564c5250", "Wrong")

    def test_frame_count(self):
        self.assertEqual(self.vrl.frame_count(), 2, "Actual {}".format(self.vrl.frame_count()))

    def test_frame_size(self):
        self.assertEqual(self.vrl.frame_size(), 2048, "Actual <{}>".format(self.vrl.frame_size()))


class TestVita49VRT_methods(unittest.TestCase):
    def setUp(self):

        the_list =\
            [
                0x10, 0x53, 0x07, 0xFD,  # Header
                0x00, 0x00, 0x00, 0x00,  # Stream Id
                0x11, 0x22, 0x33, 0x44,  # Integer Seconds Timestamp
                0x50, 0x51, 0x52, 0x53,  # Fractional Seconds Timestamp MSW
                0x60, 0x61, 0x62, 0x63   # Fractional Seconds Timestamp LSW
            ]

        the_bytes = bytearray(the_list)
        try:
            self.vrt = Vita49.VRT(the_bytes, Vita49.BIG_ENDIAN, logging.INFO)
        except RuntimeError as the_error:
            print("Unable to create vrt because <{}>".format(str(the_error)))


    def test_header(self):
        self.assertEqual(self.vrt.header(), 0x105307fd, "Actual <{}>".format(hex(self.vrt.header())))

    def test_stream_id(self):
        self.assertEqual(self.vrt.stream_id(), 0, "Actual <{}>".format(self.vrt.stream_id()))

    def test_ist(self):
        self.assertEqual(self.vrt.integer_seconds_timestamp(), 0x11223344, "Actual <{}>".format(self.vrt.integer_seconds_timestamp()))

    def test_fst_msw(self):
        self.assertEqual(self.vrt.fractional_seconds_timestamp_msw(), 0x50515253, "Actual <{}>".format(self.vrt.fractional_seconds_timestamp_msw()))

    def test_fst_lsw(self):
        self.assertEqual(self.vrt.fractional_seconds_timestamp_lsw(), 0x60616263, "Actual <{}".format(self.vrt.fractional_seconds_timestamp_lsw()))

    def test_packet_type(self):
        self.assertEqual(self.vrt.packet_type(), 1, "Actual <{}>".format(self.vrt.packet_type()))

    def test_c(self):
        self.assertEqual(self.vrt.c(), 0, "Actual <{}>".format(self.vrt))

    def test_t(self):
        self.assertEqual(self.vrt.t(), 0, "Actual <{}>".format(self.vrt.t()))

    def test_rr(self):
        self.assertEqual(self.vrt.rr(), 0, "Actual <{}>".format(self.vrt.rr()))

    def test_tsi(self):
        self.assertEqual(self.vrt.tsi(), 1, "Actual <{}>".format(self.vrt.tsi()))

    def test_tsf(self):
        self.assertEqual(self.vrt.tsf(), 1, "Actual <{}>".format(self.vrt.tsf()))

    def test_packet_count(self):
        self.assertEqual(self.vrt.packet_count(), 3, "Actual <{}>".format(self.vrt.packet_count()))

    def test_packet_size(self):
        self.assertEqual(self.vrt.packet_size(), 0x07FD, "Actual <{}>".format(self.vrt.packet_size()))

if __name__ == '__main__':
    unittest.main()