import AVS4000Transceiver
import logging


if __name__ == '__main__':
    the_device = AVS4000Transceiver.DeviceController(1, 12701, "NA", "AVS4000", "usb", logging.INFO)

    the_device.setup();

    the_device.set_read_data(True)
    the_device.set_output_format(AVS4000Transceiver.VITA49OutputFormat)
    the_device.set_tune(101.1e6, 0, 1e6,)

    the_device.enable()

    for index in range(0, 10):
        the_vrt, the_data = the_device.get_vita49_data()

        if the_data is not None:
            print("[{0:2}]: data {1}, the_vrt {2}".format(index, len(the_data), the_vrt))
        else:
            print()

    the_device.disable()