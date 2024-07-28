from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
import json
import socket

class Initializer(BehaviorModelExecutor) :
    def __init__(self, instantiate_time, destruct_time, name, engine_name):
        BehaviorModelExecutor.__init__(self, instantiate_time, destruct_time, name, engine_name)
        self.init_state("Wait")
        self.insert_state("Wait", Infinite)
        self.insert_state("Init", 1)

        self.insert_input_port("start")
        self.insert_output_port("init_done")

        self.grid_scale = 3 # 사용자 입력 받도록 변경 가능함
        self.start_point = 0
        self.end_point = 0
        self.key_dict = {}




    def ext_trans(self, port, msg) :
        if port == "start" :
            print("Simulator Start")
            self._cur_state = "Init"
    
    def output(self) :
        if self._cur_state == "Init" :


            while self.start_point == 0 :                
                # input_data = input("Input Start Point x, y. (ex : 0, 0) : ")
                try : 
                    
                    data = load_json_template()
                    data['msg'] = "Input Start Point x, y. (ex : 0, 0)"
                    json_data = json.dumps(data).encode('utf-8')
                    self.client_socket.sendall(json_data)

                    input_data = self.client_socket.recv(1024).decode('utf-8')

                    if not input_data :
                        sys.exit()

                    x_str, y_str = input_data.split(',')
                    x = int(x_str.strip())
                    y = int(y_str.strip())

                    self.start_point = (x, y)
                except ValueError :
                    print("Please enter the correct format.")
                    continue
            while self.end_point == 0 :
                # input_data = input("Input End Point x, y. (ex : 2, 2) : ")
                try : 
                    
                    data = load_json_template()
                    data['msg'] = "Input End Point x, y. (ex : 2, 2)"
                    json_data = json.dumps(data).encode('utf-8')
                    self.client_socket.sendall(json_data)

                    input_data = self.client_socket.recv(1024).decode('utf-8')

                    if not input_data :
                        sys.exit()
                    
                    x_str, y_str = input_data.split(',')
                    x = int(x_str.strip())
                    y = int(y_str.strip())

                    self.end_point = (x, y)
                except ValueError :
                    print("Please enter the correct format.")
                    continue
                
            msg = SysMessage(self.get_name(), "init_done")
            msg.insert(self.grid_scale)
            msg.insert(self.start_point)
            msg.insert(self.end_point)
            msg.insert(self.key_dict)
            msg.insert(self.client_socket)
            return msg

    def int_trans(self):
        if self._cur_state == "Wait" :
            self._cur_state = "Wait"
        elif self._cur_state == "Init" :
            self._cur_state = "Wait"