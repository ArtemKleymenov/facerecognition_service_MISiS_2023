import socket
import numpy as np
import struct


def send_msg(sock: socket, msg: bytes) -> None:
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recvall(sock: socket, n: int) -> bytearray:
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            break
        data.extend(packet)
    return data

def recv_msg(sock: socket) -> bytearray:
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return bytearray()
    msglen = struct.unpack('>I', raw_msglen)[0]
    return recvall(sock, msglen)

server_ip = 'localhost'
server_port = 8888
req = 'stopTracking'

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    send_msg(client, req.encode("utf-8"))
    response = recv_msg(client)
    response = response.decode("utf-8")
    print(f"Received: {response}")
except Exception as e:
    print(f"Client error when handling client: {e}")
finally:
    client.close()
    print("Connection to server closed")
