__author__ = 'Shane Bourne'
__email__ = 'shane.n.bourne@gmail.com'

import sys
import socket
import getopt
import threading
import subprocess

# Define some global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print """
    SB Net Tool

        Usage: sbnet.py -t target_host -p port"
        -l --listen                 - listen on [host]:[port] for
                                      incoming connections
        -e --execute=file_to_run    - execute a given file upon
                                      recieving a connection
        -c --command                - initalise a command shell
        -u --upload destination     - upon recieving connection, upload
                                      a file and write to [destination]

        Examples:
        sbnet.py -t 192.168.0.1 -p 5555 -l -c
        sbnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe
        sbnet.py -t 192.168.0.1 -p 5555 -l -e=\cat /etc/passwd echo 'ABCDEFGHI' | ./sbnet.py -t 192.168.0.1 -p 135
    """
    sys.exit(0)


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # Read the commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    # Are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        # Read in the buffer from commandline, this will block, so send CTRL-D if not sending input to stdin
        buffer = sys.stdin.read()

        # Send data off
        client_sender(buffer)

    # We are going to listen and potentially upload things, execute commands and drop a shell back depending
    # on our command line options above
    if listen:
        server_loop()

    main()


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer)
        while True:
            # Now wait for data back
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print response,

            # Wait for more input
            buffer = raw_input("")
            buffer += "\n"

            # Send it off
            client.send(buffer)

    except:
        print "[*] Exception! Exiting..."

        # Tear down the connection
        client.close()


def server_loop():
    global target

    # If no defined target then listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(target, port)
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # Spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def run_command(command):
    # Trim the newline
    command = command.rstrip()

    # Run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    # Send the output back to the client
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # Check for upload
    if len(upload_destination):

        # Read in all bytes and write to our destination
        file_buffer = ""

        # Keep reading data until none is available
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # Now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # ACK that the file has been successfully written
            client_socket.send("Successfully saved file to {0}\r\n".format(upload_destination))
        except:
            client_socket.send("Failed to save file to {0}\r\n".format(upload_destination))

    # Check for command execution
    if len(execute):
        # Run the command
        output = run_command(execute)

        client_socket.send(output)

    # Now we go to another loop if command shell was requested

    if command:

        while True:
            # Show a simple prompt
            client_socket.send("<SNB:#> ")

            # Now we recieve until we see a line feed (enter key)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # Send back command output
            response = run_command(cmd_buffer)

            # Send back the response
            client_socket.send(response)

if __name__ == "__main__":
    main()