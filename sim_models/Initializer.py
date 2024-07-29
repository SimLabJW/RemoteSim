from pyevsim import BehaviorModelExecutor, Infinite, SysMessage

class Initializer(BehaviorModelExecutor) :
    def __init__(self,  instance_time, destruct_time, name, engine_name, conn):
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Wait")
        self.insert_state("Wait", Infinite)
        self.insert_state("Init", 1)

        self.insert_input_port("start")
        self.insert_output_port("init_done")

        self.grid_scale = 3 # 사용자 입력 받도록 변경 가능함
        self.start_point = None
        self.end_point = None
        self.key_dict = {
            "W" : "back",
            "S" : "front",
            "A" : "left",
            "D" : "right"
        }

        self.conn = conn

    def ext_trans(self, port, msg) :
        if port == "start" :
            print("Simulator Start")
            self.unity_fisrt_data = msg.retrieve()[0][0]
            self._cur_state = "Init"
    
    def output(self) :
        if self._cur_state == "Init" :

            while self.start_point == None and self.end_point == None:                

                try : 
        
                    print(f"initalize input data : {self.unity_fisrt_data}")

                    x_str, y_str = self.unity_fisrt_data.split(',')
                    x = int(x_str.strip())
                    y = int(y_str.strip())

                    self.start_point = self.number_to_coordinates(x)
                    self.end_point = self.number_to_coordinates(y)
                    print(self.start_point, self.end_point)
                except ValueError :
                    print("Please enter the correct format.")
                    continue
                
            msg = SysMessage(self.get_name(), "init_done")
            msg.insert(self.grid_scale)
            msg.insert(self.start_point)
            msg.insert(self.end_point)
            msg.insert(self.key_dict)
            return msg

    def int_trans(self):
        if self._cur_state == "Wait" :
            self._cur_state = "Wait"
        elif self._cur_state == "Init" :
            self._cur_state = "Wait"

    def number_to_coordinates(self, num):
        if num < 1 or num > 9:
            raise ValueError("Input number must be between 1 and 9")
        
        # Calculate column and row
        col = (num - 1) // 3
        row = (num - 1) % 3

        return (row, col)