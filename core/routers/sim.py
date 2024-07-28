import socket
import threading
import json
import queue
from ..models.simulator import Simulator

sim_send_queue = queue.Queue()
sim_recv_queue = queue.Queue()
sim_event = threading.Event()

sim = Simulator(sim_send_queue, sim_recv_queue, sim_event)
sim_flag = False
sim.engine_thread_start()

def handle_simulation_client(client_socket):
    request = client_socket.recv(4096)
    print(f"Received from simulation client: {request}")

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

def start_simulation_server(host='0.0.0.0', port=11015):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Simulation server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_simulation_client, args=(client_socket,))
            client_handler.start()
    except KeyboardInterrupt:
        print("Simulation server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_simulation_server()
