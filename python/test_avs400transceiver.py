#!/usr/bin/python2

import AVS4000Transceiver
import logging

def main(context):
    the_device = AVS4000Transceiver.DeviceController(1, 12701, "NA", "AVS4000", "usb", context['loglevel'])
    the_device.setup()

    the_device.set_read_data_flag(True)
    the_device.set_output_format(AVS4000Transceiver.VITA49OutputFormat)
    the_device.set_tune(101.1e6, 0, 1e6,)

    the_device.enable()

    for index in range(0, 5):
        the_list = the_device.get_data_vita49_single_timestamp()

        if the_list is not None:
            count = 0
            for the_packet in the_list:
                print("[{}] vrl:\n{}\n vrt\n{}".format(count, the_packet.vrl(), the_packet.vrt_header()))
                count = count + 1
        else:
            print("No data returned")

    the_device.disable()

    print(the_device.query_gps())
    print(the_device.query_master())
    print(the_device.query_rx())
    print(the_device.query_rxstat())

if __name__ == '__main__':
    context = {}
    context['loglevel'] = logging.INFO

    main(context)
