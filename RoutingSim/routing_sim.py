from pyevsim import SystemSimulator, Infinite
from models import initializer, predictor, mover

def main() :
    try:
        ss = SystemSimulator()
        # ss.register_engine("engine", "REAL_TIME", 1)
        ss.register_engine("engine", "VIRTUAL_TIME", 1)
        se = ss.get_engine("engine")
    
        se.insert_input_port("start")
    
        initializer_model = initializer(0, Infinite, "initializer", "engine", "key_binding.json", "server_binding.json")
        se.register_entity(initializer_model)
        predictor_model = predictor(0, Infinite, "predictor", "engine")
        se.register_entity(predictor_model)
        mover_model = mover(0, Infinite, "mover", "engine")
        se.register_entity(mover_model)

        se.coupling_relation(None, "start", initializer_model, "start")
        se.coupling_relation(initializer_model, "init_done", predictor_model, "init_done")
        se.coupling_relation(initializer_model, "init_done", mover_model, "init_done")
        se.coupling_relation(predictor_model, "pred_done", mover_model, "pred_done")
        se.coupling_relation(mover_model, "move_done", predictor_model, "move_done") 

        se.insert_external_event("start", None)

        print("===== RoutingSim Started =====")
        se.simulate()
    finally :
        print("=====  RoutingSim Ended  =====")

if __name__ == "__main__" :
    main()