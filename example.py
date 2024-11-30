import argparse
from datamax_printer import DPLPrinter


def main():
    parser = argparse.ArgumentParser(description='Example program on how to control a DPL printer with the datamax_'
                                                 'printer module')

    parser.add_argument('ip', help='IP address or hostname of the datamax oneil printer in your network')
    parser.add_argument('--port', '-p', help='The port the printer listens (default: 9100)', type=int, default=9100)
    # if using comport comment ip-port and unccomment com/baudrate
    # parser.add_argument('com_port', helps='Set your printer COM-port')
    # parser.add_argument('baudrate', helps='Set your COM-port baudrate', type=int, default=9600)
    args = parser.parse_args()

    printer = DPLPrinter(args.ip, args.port)
    # printer = DLPPrinter(args.com_port, args.baudrate)
    printer.configure()
    printer.start_document()
    printer.set_encoding("CP")
    printer.set_qr_code(285, 120, 'https://www.innetag.ch/', 9)
    printer.set_label(300, 60, 'innetag.ch', 9, 10)
    printer.print()
    # if COM port
    # printer.close_connection()

if __name__ == '__main__':
    main()
