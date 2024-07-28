from pyevsim import SystemSimulator, Infinite
from sim_models.CommunicationTCP import communication_tcp
from sim_models.CommunicationModel import CommunicationModel
from sim_models.Initializer import Initializer
from sim_models.Predictor import Predictor
from sim_models.Mover import Mover

class Simulator:
    def __init__(self) -> None:        
        self.engine_name = "Sim"
        self.conn = communication_tcp()
        
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
        self.sm_engine.insert_input_port("start")

        
    def engine_register_entity(self) -> None:
        """
        시뮬레이션 엔진에 등록할 모델 설정
        """        
        self.thread_cm_model = CommunicationModel(instance_time = 0, destruct_time = Infinite,\
            name = "thread_cm_model", engine_name = self.engine_name, conn = self.conn)
        
        
        self.initializer_model = Initializer(instance_time = 0, destruct_time = Infinite,\
            name = "initializer_model", engine_name = self.engine_name, conn = self.conn)
        
        self.predictor_model = Predictor(instance_time = 0, destruct_time = Infinite,\
            name = "predictor_model", engine_name = self.engine_name, conn = self.conn)
        
        self.mover_model = Mover(instance_time = 0, destruct_time = Infinite,\
            name = "mover_model", engine_name = self.engine_name, conn = self.conn)
        

        self.sm_engine.register_entity(self.thread_cm_model)
        self.sm_engine.register_entity(self.initializer_model)
        self.sm_engine.register_entity(self.predictor_model)
        self.sm_engine.register_entity(self.mover_model)

    def engine_coupling_relation(self) -> None:
        """
        시뮬레이션 엔진 내의 모델 간의 상호작용 설정
        """        
        self.sm_engine.coupling_relation(None, "start",\
            self.thread_cm_model, "start")
        self.sm_engine.coupling_relation(self.thread_cm_model, "control_data",\
            self.initializer_model, "start")
        
        self.sm_engine.coupling_relation(self.initializer_model, "init_done",\
            self.predictor_model, "init_done")
        self.sm_engine.coupling_relation(self.initializer_model, "init_done",\
            self.mover_model, "init_done")

        self.sm_engine.coupling_relation(self.predictor_model, "pred_done",\
            self.mover_model, "pred_done")
        self.sm_engine.coupling_relation(self.mover_model, "move_done",\
            self.predictor_model, "move_done")

    
    def engine_start(self) -> None:
        print("copul")
        self.sm_engine.insert_external_event("start","start")
        print(" * Simulation Engine Start Succesfully.")
        
        self.sm_engine.simulate(_tm = False)
        # self.sm_engine.simulate()
        

# if __name__ == "__main__":
#     Simulator().engine_start()

