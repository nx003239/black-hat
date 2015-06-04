__author__ = 'Shane Bourne'
__email__ = 'shane.n.bourne@gmail.com'

import socket, threading

bind_ip     = "127.0.0.1"
bind_port   = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip, bind_port))

server.listen(5)

print "[*] Listening on {0}:{1}".format(bind_ip, bind_port)

# Client-handling thread
def handle_client(client_socket):

    # Print out what client sends
    request = client_socket.recv(1024)

    print "[*] Received: {0}".format(request)

    # Send back a packet
    client_socket.send("ACK!")

    client_socket.close()

while True:
        client, addr = server.accept()

        print "[*] Accepted connection from: {0}:{1}".format(addr[0], addr[1])

        # Spin up client to handle incoming data
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()
