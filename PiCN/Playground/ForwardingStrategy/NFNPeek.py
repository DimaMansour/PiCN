"""NFN Peek"""

import argparse
import socket
import sys
import time

from PiCN.Layers.PacketEncodingLayer.Encoder import SimpleStringEncoder
from PiCN.Layers.PacketEncodingLayer.Encoder import NdnTlvEncoder
from PiCN.Layers.PacketEncodingLayer.Printer.NdnTlvPrinter import NdnTlvPrinter
from PiCN.Packets import Interest



def main(args):
    # Packet encoder
    encoder = NdnTlvEncoder() if args.format == 'ndntlv' else SimpleStringEncoder

    # Generate interest packet
    interest: Interest = Interest(args.name)
    encoded_interest = encoder.encode(interest)

    # Send interest packet
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))

    resolved_hostname = socket.gethostbyname(args.ip)

    sock.sendto(encoded_interest, (resolved_hostname, args.port))

    # Receive content object
    try:
        wire_packet, addr = sock.recvfrom(8192)
    except:
        print("Timeout.")
        sys.exit(-1)

    # Print
    if args.plain is False:
        printer = NdnTlvPrinter(wire_packet)
        printer.formatted_print()
    else:
        encoder = NdnTlvEncoder()
        if encoder.is_content(wire_packet):
            sys.stdout.buffer.write(encoder.decode_data(wire_packet)[1])
        else:
            sys.exit(-2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NFN Peek Tool')
    parser.add_argument('-i', '--ip', type=str, default='127.0.0.1',
                        help="IP address or hostname of forwarder (default: 127.0.0.1)")
    parser.add_argument('-p', '--port', type=int, default=9000, help="UDP port (default: 9000)")
    parser.add_argument('-f', '--format', choices=['ndntlv', 'simple'], type=str, default='ndntlv',
                        help='Packet Format (default: ndntlv)')
    parser.add_argument('--plain', help="plain output (writes payload to stdout or returns -2 for NACK)",
                        action="store_true")
    parser.add_argument('name', type=str, help="Computation")
    args = parser.parse_args()
    main(args)
