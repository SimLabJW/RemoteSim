from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite
import threading
from .sim_models.thread_commnuicator import ThreadCommnuicator
from .sim_models.scenario_generator import ScenarioGenerator

class Simulator():
    def __init__(self, _recv_queue= None, _send_queue= None, sm_event= None) -> None:        
        self.engine_name = "Sim"
        
        self._recv_queue = _recv_queue
        self._send_queue = _send_queue
        self.sm_event = sm_event
        
        ss = SystemSimulator()
        ss.register_engine(self.engine_name, "VIRTUAL_TIME", 1)
        
        self.sm_engine = ss.get_engine(self.engine_name)
        
        # Set Engine Port
        self.engine_init_port()
        
        # Set Engine entity
        self.engine_register_entity()

        # Set Model's Relation
        self.engine_coupling_relation()
        
        # self.engine_start()

    def engine_init_port(self) -> None:
        """
        시뮬레이션 엔진 입출력 포트 설정
        """
        
        self.sm_engine.insert_input_port("generate")
        self.sm_engine.insert_input_port("fin")
    
        self.sm_engine.insert_output_port("generate")   
        self.sm_engine.insert_output_port("fin")   
        
    def engine_register_entity(self) -> None:
        """
        시뮬레이션 엔진에 등록할 모델 설정
        """        
        self.thread_cm_model = ThreadCommnuicator(instance_time = 0, destruct_time = Infinite,\
            name = "thread_cm_model", engine_name = self.engine_name, \
                _recv_queue=self._recv_queue, _send_queue = self._send_queue, event= self.sm_event)
        self.scenario_generate_model = ScenarioGenerator(instance_time = 0, destruct_time = Infinite,\
            name = "scenario_generate_model", engine_name = self.engine_name)
        
        self.sm_engine.register_entity(self.thread_cm_model)
        self.sm_engine.register_entity(self.scenario_generate_model)
    

    def engine_coupling_relation(self) -> None:
        """
        시뮬레이션 엔진 내의 모델 간의 상호작용 설정
        """        
        self.sm_engine.coupling_relation(self.thread_cm_model, "generate",\
            self.scenario_generate_model, "generate")
        self.sm_engine.coupling_relation(self.scenario_generate_model, "fin",\
            self.thread_cm_model, "fin")
    
    def engine_start(self) -> None:
        # self.engine.insert_external_event("start","start")
        print(" * Simulation Engine Start Succesfully.")
        
        # 쓰레드간 Signal 충돌이 나므로 _tm을 False로 설정해야 Main Thread가 아닌 상태여도 시뮬레이션 엔진이 동작함
        self.sm_engine.simulate(_tm = False)
        
    def engine_thread_start(self) -> None:
        print("Sim Thread Start")
        threading.Thread(target=self.engine_start, daemon=True).start()
        
if __name__ == '__main__':
    Simulator().engine_thread_start()