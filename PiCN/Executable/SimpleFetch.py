"""Tool to Fetch Content"""

import socket
import sys
from random import randint

from PiCN.Layers.PacketEncodingLayer.Encoder import SimpleStringEncoder
from PiCN.Packets import Content, Interest


def main(argv):
    if len(argv) != 4:
        print("usage: ", argv[0], "ip, port, name")
        return

    #parameter
    ip = argv[1]
    port = int(argv[2])
    name = argv[3]

    encoder = SimpleStringEncoder()

    # create interest
    interest: Interest = Interest(name)
    encoded_interest = encoder.encode(interest)
    # send interest
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_port = randint(10000, 64000)
    sock.bind(("0.0.0.0", send_port))
    sock.sendto(encoded_interest, (ip, port))

    encoded_content, addr = sock.recvfrom(8192)
    content: Content = encoder.decode(encoded_content)

    print(content.content)


if __name__ == "__main__":
    main(sys.argv)