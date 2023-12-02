"""
This file contains a function to test the availability of a host using ICMP.
"""

import socket
import struct
import time


def icmp_test(host, packets=20, tos=None):
    """
    Function to test the availability of a host using ICMP and set TOS.
    Returns the loss and latency of the packet.
    """

    # Create ICMP socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    # Set TOS if provided
    if tos:
        icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)

    # Create ICMP header
    icmp_header = struct.pack("!BBHHH", 8, 0, 0, 0, 0)

    # Create checksum function
    def checksum(packet):
        # Initialize variables
        sum = 0
        count_to = (len(packet) // 2) * 2
        count = 0

        # Calculate the sum of each 16-bit word
        while count < count_to:
            this_val = packet[count + 1] * 256 + packet[count]
            sum = sum + this_val
            sum = sum & 0xffffffff
            count = count + 2

        # If there is an extra byte
        if count_to < len(packet):
            sum = sum + packet[len(packet) - 1]
            sum = sum & 0xffffffff

        # Add high 16 bits to low 16 bits
        sum = (sum >> 16) + (sum & 0xffff)
        sum = sum + (sum >> 16)

        # Take one's complement
        answer = ~sum
        answer = answer & 0xffff

        # Swap bytes
        answer = answer >> 8 | (answer << 8 & 0xff00)

        return answer

    # Create sequence number
    seq_num = 1

    # Initialize variables
    loss = 0
    total_time = 0

    # Send ICMP packets
    for i in range(packets):
        # Create ICMP packet
        packet = icmp_header + struct.pack("!HH", seq_num, i) + b"test data"

        # Calculate checksum
        packet = packet[:2] + struct.pack("!H", checksum(packet)) + packet[4:]

        # Start timer
        start_time = time.time()

        # Send packet
        icmp_socket.sendto(packet, (host, 1))

        # Set timeout
        icmp_socket.settimeout(1)

        # Try to receive packet
        try:
            recv_packet, addr = icmp_socket.recvfrom(1024)

            # Calculate round trip time
            rtt = time.time() - start_time

            # Print results
#           print("Reply from {}: bytes={} time={:.2f}ms".format(host, len(packet), rtt * 1000))

        # If timeout
        except socket.timeout:
            # Increase loss count
            loss += 1

            # Print result
#           print("Request timed out.")

        # Increase sequence number
        seq_num += 1

        # Add round trip time to total time
        total_time += rtt

    # Calculate average round trip time in ms.
    avg_rtt = round((total_time / (packets - loss) * 1000), 2)

    # Close socket
    icmp_socket.close()

    return (loss, avg_rtt)

# Test function
loss, rtt = icmp_test("127.0.0.1")

print(f"LOSS: {loss}\nRTT: {rtt}")
