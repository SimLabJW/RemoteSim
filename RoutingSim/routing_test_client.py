import socket
import threading
import sys
import json

def receive_messages(client_socket : socket.socket, stop_event : threading.Event):
    while not stop_event.is_set():
        try:
            message = client_socket.recv(4096)
            receive_dict = json.loads(message.decode('utf-8'))
            if not message:
                print("Server Disconnected.")
                stop_event.set()
                break
            print(f"\nServer : {receive_dict}")

            # 도착하면 클라이언트 꺼지는 부분입니다! 필요하시면 주석 해제 해주세요!

            #if receive_dict['msg'] == 'Goal!' :
            #   print("Client Stop")
            #   stop_event.set()

        except Exception as e:
            print(f"Recv Error : {e}")
            stop_event.set()
            break

def send_messages(client_socket : socket.socket, stop_event : threading.Event):
    while not stop_event.is_set():
        try:
            message = input("\nInput Your Message : ")
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Send Error : {e}")
            stop_event.set()
            break

def start_tcp_client(host='localhost', port=11015):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    stop_event = threading.Event()

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, stop_event))
    send_thread = threading.Thread(target=send_messages, args=(client_socket, stop_event))
    
    receive_thread.start()
    send_thread.start()
    
    receive_thread.join()
    send_thread.join()
    
    client_socket.close()

# 클라이언트 시작
start_tcp_client()