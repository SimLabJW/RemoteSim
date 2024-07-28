import socket
import threading
import json
# from ..models.simulator import Simulator
import json
import queue
import threading

class Simulator:
    def __init__(self, send_queue, recv_queue, event):
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self.event = event

    def engine_thread_start(self):
        thread = threading.Thread(target=self.simulator_engine)
        thread.start()

    def simulator_engine(self):
        while True:
            # Wait for a request
            request = self.send_queue.get()
            # Process the request (this is a placeholder for actual processing)
            response = {"status": "processed", "data": request}
            # Put the response in the receive queue
            self.recv_queue.put(response)
            # Set the event to signal that processing is complete
            self.event.set()
            
sim_send_queue = queue.Queue()
sim_recv_queue = queue.Queue()
sim_event = threading.Event()


sim = Simulator(sim_send_queue, sim_recv_queue, sim_event)
sim_flag = False
sim.engine_thread_start()

def handle_client(client_socket):
    request = client_socket.recv(4096)
    print(f"Received: {request}")

    try:
        state_request = json.loads(request.decode('utf-8'))
        sim_send_queue.put(state_request)

        sim_event.wait()
        sim_event.clear()

        state_response = sim_recv_queue.get()
        response = json.dumps(state_response).encode('utf-8')
    except json.JSONDecodeError:
        response = json.dumps({"error": "Invalid JSON"}).encode('utf-8')

    client_socket.sendall(response)
    client_socket.close()

def start_server(host='0.0.0.0', port=11015):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()