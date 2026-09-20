import socket
from threading import Thread
from datetime import datetime
from dataclasses import dataclass

# Create and Bind a TCP Server Socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
s_ip = socket.gethostbyname(host_name)
port = 18000
serverSocket.bind(("localhost", port))

# Outputs Bound Contents
print("Socket Bound")
print("Server IP: ", s_ip, " Server Port:", port)

# Listens for 10 Users
serverSocket.listen(10)

# define constants
capacity = 3

# Creates a set of clients
client_List = set()
# every message, chat history
msgList = []

# includes all client sockets and whether they have msged at least once
client_first_msg = {}
# includes all client sockets and their usernames
client_names = {} 

#### have to add these flags to replace current logic
# serverMessage = {
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
#     "USERNAME": "" # if join_request, join_accept, new_user, or quit_accept are 1, then this field is filled otherwise it is empty
#     "FILENAME": "", # if attachment, includes filename and its path set by client.
#     "PAYLOAD_LENGTH": 0, # length of msg including \n, 0 when no msg, set by client
#     "PAYLOAD": "" # includes contents of msg, set by client
# }
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
    

# Function to constantly listen for an client's incoming messages and sends them to the other clients
#cs is client socket
def clientWatch(cs):
    adminFlag = 0

    # if new client socket, set that they haven't messaged yet.
    if cs not in client_first_msg:
        client_first_msg[cs] = False

    while True:
        try:
            # Constantly listens for incoming message from a client
            msg = cs.recv(1024).decode()

            # If msg is empty, it means client has disconnected
            if not msg:
                handle_client_disconnection(cs)
                break  # Break out of the loop

            # if user enters admin as user name set admin Flag to 1, let server and client know admin connected
            if msg == "admin":
                adminFlag = 1
                print("Admin Connected")
                adminMsg = "Type 'viewall' to view all recorded messages"
                cs.send(adminMsg.encode())
                client_first_msg[cs] = True  # mark that the client has sent a message
                client_names[cs] = msg # save the msg/name of client
                continue

            # Check if it is the first message from this client
            if not client_first_msg[cs] and msg != "q" and msg != "report request": # != "q" when we send q from the client side 
                # reject if chatroom is full
                if(len(client_List) > capacity):
                    print("Client was rejected b/c the chatroom has reached capacity.")
                    cs.send("cap limit".encode())
                    handle_client_disconnection(cs) 
                    break
                # reject if client username is taken
                if msg in client_names.values():
                    print("Client was rejected b/c the username " + msg + " is already taken.")
                    cs.send("name taken".encode())
                    handle_client_disconnection(cs)
                    # client_List.remove(cs) # rejecting the client
                    # cs.close()
                    #del client_first_msg[cs]  # Remove from tracking dictionary
                    break
                join_chat(cs, msg)
                continue # continue so you don't save the name entry as chat log / msgList

            # if q is entered remove the client from the client list and close connection
            if msg == "q":
                handle_client_disconnection(cs)
                break
                
            if msg == "report request":
                send_report(cs)
                break

        # except Exception as e:
        #     print("Error")
        #     client_List.remove(cs)

            # splits of last word of message (due to username and time being sent)
            newMsg = msg.split()
            # checks if user is an admin and has entered 'viewall', sends messageList to the admin client
            if adminFlag and newMsg[-1] == "viewall":
                send_chatlog(cs)
                continue

            # otherwise broadcast message to chat room
            broadcast_message(msg)

        except Exception as e:
            print(f"Error: {e}")
            handle_client_disconnection(cs)
            break  # Exit the loop to stop processing for this client


###################################################################
#functions

def send_report(cs):
    #Generates and sends a report of active users to the requesting client.
    report = f"There are {len(client_names)} active users in the chatroom.\n"
    for i, (client, username) in enumerate(client_names.items(), start=1):
        ip, port = client.getpeername()
        report += f"{i}. {username} at IP: {ip} and port: {port}\n"
    
    cs.send(report.encode())  # Send the report back to the requesting client
    handle_client_disconnection(cs)

def send_chatlog(cs):
    """Sends the entire chatlog to the admin."""
    print("Admin accessed chat log.")
    cs.send("----------Chatlog----------\n".encode())
    for msgs in msgList:
        cs.send((msgs + "\n").encode())
    cs.send("\n----------EndLog----------\n".encode())

def broadcast_message(msg):
    """Broadcasts a message to all connected clients."""
    msgList.append(msg)
    for client_socket in client_List:
        client_socket.send(msg.encode())

def handle_client_disconnection(cs):
    """Handles a client's disconnection by removing them from the server and notifying others."""
    if cs in client_names:
        removeMsg = f"Server: {client_names[cs]} has disconnected."
        date_now = datetime.now().strftime("[%H:%M] ")
        removeMsg = date_now + removeMsg
        msgList.append(removeMsg)
        print(removeMsg)
        for client_socket in client_List:
            client_socket.send(removeMsg.encode())
        del client_names[cs]
    if cs in client_List:
        client_List.remove(cs)
    if cs in client_first_msg:
        del client_first_msg[cs]
    cs.close()

def join_chat(cs, username):
    """Handles the joining process for a new user."""
    # sends welcome message to newly added user
    cs.send("welcome".encode())
    # sending the chat history to the newly added user
    for x in msgList: 
        cs.send((x + "\n").encode()) 
    
    # join message to be printed on server end and on clients side
    joinMsg = f"Server: {username} has joined the chat room."
    date_now = datetime.now().strftime("[%H:%M] ")
    joinMsg = date_now + joinMsg
    # print join message in server
    print(joinMsg)
    # add join message to chat history
    msgList.append(joinMsg)
    # send join message to all the clients in the chat room
    for client_socket in client_List:
        client_socket.send(joinMsg.encode())
    client_names[cs] = username # save the msg/name of client
    client_first_msg[cs] = True  # mark that the client has sent a message


###################################################################



#chatroom_full = False
while True:
    # if len(client_List) >= capacity:
    #     if not chatroom_full:
    #         print("Chatroom is full. New clients cannot connect.")
    #         chatroom_full = True  # Set the flag to True after the message is printed
    #     continue  # Skip the connection process until there's room

         # Continues to listen / accept new clients
    client_socket, client_address = serverSocket.accept()
    print(client_address, "Connected!")

    # Adds the client's socket to the client set
    client_List.add(client_socket)

    # Reset the flag when there's room again
    # if chatroom_full:
    #     chatroom_full = False

    # Create a thread that listens for each client's messages
    t = Thread(target=clientWatch, args=(client_socket,))

    # Make a daemon so thread ends when main thread ends
    t.daemon = True

    t.start()

# Close out clients
for cs in client_List:
    cs.close()
# Close socket
s.close()
