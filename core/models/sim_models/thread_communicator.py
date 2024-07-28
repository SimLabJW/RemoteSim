from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
import time

# 파이썬 파일명이랑 클래스 이름이랑 똑같이!
class ThreadCommnuicator(BehaviorModelExecutor):
    def __init__(self, instance_time, destruct_time, name, engine_name, _recv_queue, _send_queue, event):
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)    
        
        self._recv_queue = _recv_queue
        self._send_queue = _send_queue
        self._event = event
        
        self.recv_data = None
        
        self.return_data = None
        
        # State
        self.set_state()
        
        # Port
        self.set_port()
        
    def set_state(self):
        """ 시뮬레이션 모델의 상태(State) 설정
        """
        self.insert_state("IDLE", Infinite)
        self.insert_state("RECV", 1)
        self.insert_state("RETURN", 1)
        
        self.init_state("RECV")
    
    def set_port(self):
        """ 시뮬레이션 모델의 입출력 포트(Port) 설정
        """
        self.insert_input_port("fin")
        
        self.insert_output_port("generate")
        
        
    def ext_trans(self, port, msg):
        if port == "fin":
            self.return_data = msg.retrieve()[0]
            self._cur_state = "RETURN"
            
        
    def output(self):
        if self._cur_state == "RECV":
            self.recv_data = self._recv_queue.get()

            msg = SysMessage(self.get_name(), "generate")
            msg.insert(self.recv_data)
            return msg            
            
        elif self._cur_state == "RETURN":
            
            if self.return_data:
                self._send_queue.put(self.return_data)
                
            else:
                self._send_queue.put("Err")
                
            self._event.set()
    
    def int_trans(self):
        # 쓰레드로부터 수신 시 Scenario Generator 모델에게 데이터 송신 후 대기(IDLE)
        if self._cur_state == "RECV":
            self._cur_state = "IDLE"
            
        # Generate 후 데이터 전송, 수신 대기 상태 전환
        if self._cur_state == "RETURN":
            self._cur_state = "RECV"