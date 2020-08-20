import AVS4000Transceiver
import logging

if __name__ == "__main__":
    the_device_controller = AVS4000Transceiver.DeviceController("1", "", "UNK", "AVS4000", "USB", logging.DEBUG)

    if the_device_controller.query_master():
        print("master <{}>".format(the_device_controller.master()))
