"""NFN Peek"""

import argparse
import socket
import sys
import time
from PiCN.Logger import Logger
from threading import Thread
from PiCN.Layers.PacketEncodingLayer.Encoder import SimpleStringEncoder
from PiCN.Layers.PacketEncodingLayer.Encoder import NdnTlvEncoder
from PiCN.Layers.PacketEncodingLayer.Printer.NdnTlvPrinter import NdnTlvPrinter
from PiCN.Packets import Interest
from PiCN.Packets import Name
import random

def run_singel_interest(format, ip, port, plain, interestName, logger, sock):
    # Packet encoder
    # print("\n Sending Interest "+ str(interestName)+"\n")
    t1=time.time()
    encoder = NdnTlvEncoder() if format == 'ndntlv' else SimpleStringEncoder
    # Generate interest packet
    interest: Interest = Interest(interestName)
    encoded_interest = encoder.encode(interest)

    # Send interest packet
    try:
        resolved_hostname = socket.gethostbyname(ip)
    except:
        print("Resolution of hostname failed.")
        sys.exit(-2)
    sock.sendto(encoded_interest, (resolved_hostname, port))

    # Receive content object
    try:
        wire_packet, addr = sock.recvfrom(8192)
    except:
        print("Timeout.")
        sys.exit(-1)

    # Print
    # if plain is False:
    #     printer = NdnTlvPrinter(wire_packet)
    #     printer.formatted_print()
    # else:
    #     encoder = NdnTlvEncoder()
    #     if encoder.is_content(wire_packet):
    #         sys.stdout.buffer.write(encoder.decode_data(wire_packet)[1])
    #     else:
    #         sys.exit(-2)

    # logger.info("Content Received "+ str(interestName))
    #print("\n Content Received "+ str(interestName)+"\n")
    t2 = time.time()
    print("The response time for"+str(interestName)+","+ str(t1) + "," + str(t2) + "," +str(t2-t1))


def main(args):
    thread_list = []
    logger = Logger("ExpLogger", 255)
    params = list(range(201, 701))
    #random.shuffle(params)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(20000)
    sock.bind(("0.0.0.0", 0))
    for i in list(params):
        ip = args.ip
        plain = args.plain
        port = args.port
        format = args.format
        interestName = Name("/the/prefix/bernoulli/" + str(i) + "/1/pNFN")
        arguments = [format, ip, port, plain, interestName, logger, sock]
        thread = Thread(target = run_singel_interest, args= arguments)
        time.sleep(0.5)
        thread.start()
        thread_list.append(thread)

    # Packet encoder, interestName)
        # run_singel_interest(args, interestName)

    for t in thread_list:
        t.join()

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

