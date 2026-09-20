import socket
from threading import Thread
from datetime import datetime
from dataclasses import dataclass

# Sets the preselected IP and port for the chat server
# Eneter your machine's IP address for the host_name. Alternatively, you can enter "localhost"
host_name = "localhost" # changed from "192.168.1.1" to "localhost"
port = 18000

# Creates the TCP socket
# new_socket = null

def reconnect_socket():
    global new_socket
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #print("Connecting to", host_name, port, "...")
    new_socket.connect((host_name, port))
    #print("Connected.")

#### have to add these flags to replace current logic
# 
#     "REPORT_REQUEST_FLAG": 0, # report request, set to 1 by client. 
#     "REPORT_RESPONSE_FLAG": 0, # report resposnse, set to 1 by server.
#     "JOIN_REQUEST_FLAG": 0, # join request, set to 1 by client
#     "JOIN_REJECT_FLAG": 0, # join reject, set to 1 by server
#     "JOIN_ACCEPT_FLAG": 0, # join accept, set to 1 by server
#     "NEW_USER_FLAG": 0, # new user, set to 1 by client.
#     "QUIT_REQUEST_FLAG": 0, # quit request, set to 1 by client
#     "QUIT_ACCEPT_FLAG": 0, # quit accept, set to 1 by server
#     "ATTACHMENT_FLAG": 0, # attachment in msg, set to 1 by client.
#     "NUMBER": 0, # if report, set to 0-3 by server
#     "FILENAME": "", # if attachment, includes filename and its path set by client.
#     "PAYLOAD_LENGTH": 0, # length of msg including \n, 0 when no msg, set by client
#     "PAYLOAD": "" # includes contents of msg, set by client
# 
# unable to get the flags to fully work in time, but the programs still work as intended.
@dataclass
class ClientMessage:
    REPORT_REQUEST_FLAG: int = 0
    REPORT_RESPONSE_FLAG: int = 0
    JOIN_REQUEST_FLAG: int = 0
    JOIN_REJECT_FLAG: int = 0
    JOIN_ACCEPT_FLAG: int = 0
    NEW_USER_FLAG: int = 0
    QUIT_REQUEST_FLAG: int = 0
    QUIT_ACCEPT_FLAG: int = 0
    ATTACHMENT_FLAG: int = 0
    NUMBER: int = 0
    USERNAME: str = ""
    FILENAME: str = ""
    PAYLOAD_LENGTH: int = 0
    PAYLOAD: str = ""

# returns true if successfully added, false if rejected. also displays status message
def join_chatroom():
    global name
    while True:
        # Prompts the client for a username
        name = input("Please enter a username: ")
        new_socket.send(name.encode())
        response = new_socket.recv(1024).decode()
        if "welcome" in response:
            print("The server welcomes you to the chatroom.\nType lowercase 'q' and press enter at any time to quit the chatroom.")
            print("Type lowercase 'a' and press enter at any time to upload an attachment to the chatroom.")
            print("Here is a chat history of the chatroom:")
            return True
        elif "name taken" in response:
            print("Failed to join: Please try a different username.")
            return False
        elif "cap limit" in response:
            print("Failed to join: Chat room is at its capacity.")
            return False
        else:
            break

# main loop for program use
def main_menu():
    global new_socket
    global rec_report
    rec_report = False
    new_socket = None
    while True:
        if new_socket != None:
            new_socket.close()
        print("\nPlease select one of the following options:")
        #### want to be disconnected from server once back in main menu
        #### and want to reconnect once select 1 or 2. 
        #### so we want to make a new socket everytime we select an option
        print("1. Get a report of the chatroom from the server.")
        print("2. Request to join the chatroom.")
        print("3. Quit the program.")
        choice = input("Your choice: ")
        
        if choice == "1":
            reconnect_socket()
            #new_socket.send("report".encode())  # Assumes server understands "report" command
            new_socket.send("report request".encode())
            response = new_socket.recv(1024).decode()
            print(response)
            new_socket = None
            continue
        elif choice == "2":
            reconnect_socket()
            if join_chatroom():
                chat_room()
            new_socket = None
        elif choice == "3":
            print("Quitting program.")
            if new_socket != None:
                new_socket.send("q".encode())
            new_socket = None
            exit()
        else:
            print("Invalid choice. Please select again.")

# Thread to listen for messages from the server
def listen_for_messages():
    try:
        while True:
            message = new_socket.recv(1024).decode()
            if not message:
                break
            # if quit accept don't print
            if not exitFlag:
                print(message)
    except OSError: 
        print("Socket closed or connection error.")  # Graceful handling if socket is closed


def chat_room():
    global exitFlag
    exitFlag = False
    t = Thread(target=listen_for_messages)

    t.daemon = True

    t.start()

    # if user is an admin send the admin name before appending time and username
    if name == "admin":
        print("Welcome Administrator")
        new_socket.send(name.encode())

    while True:
        # Recieves input from the user for a message
        to_send = input()

        # Allows the user to exit the chat room
        if to_send.lower() == "q":
            exitFlag = True
            new_socket.send(to_send.encode())
            break
            #exit()
        # Allows the user to send an attachment
        if to_send.lower() == "a":
            print("insert name of attachment to send:")
            file_path = input()
            # find file and set message to be sent to file
            with open(file_path, 'r') as file:
                to_send = file.read()

        # Appends the username and time to the clients message
        to_send = name + ": " + to_send
        date_now = datetime.now().strftime("[%H:%M] ")
        to_send = date_now + to_send

        # Sends the message to the server
        new_socket.send(to_send.encode())

    # close the socket
    #new_socket.close()
    t.join() # wait for thread to finish before returning to main menu

main_menu()
