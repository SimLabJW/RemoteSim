import socket
import json

class communication_tcp:
    def __init__(self, host='localhost', port=11015):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")

    # def send(self, data):
    #     packet = {
    #         "id": data
    #     }
    #     json_data = json.dumps(packet) + '\n'  # 패킷 구분을 위한 '\n' 추가
    #     self.socket.send(json_data.encode('utf-8'))
    #     print(f"Sent data: {json_data}")

    def send(self, data):
        packet = data
        
        json_data = json.dumps(packet) + '\n'  # 패킷 구분을 위한 '\n' 추가
        self.socket.send(json_data.encode('utf-8'))


    def recv(self):
        try:
            data = self.socket.recv(4096)
            if data:
                message = data.decode('utf-8')
                return message
            else:
                print("No data received.")
                return None
        except Exception as e:
            print(f"Receive Error: {e}")
            return None

    def close(self):
        self.socket.close()
        print("Connection closed")
