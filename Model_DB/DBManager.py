#db
from pyevsim import BehaviorModelExecutor, Infinite, SysMessage
from pymongo import MongoClient
import os
import gridfs

class DBManagerModel(BehaviorModelExecutor):
    def __init__(self, instance_time, destruct_time, name, engine_name, db_server, image_folder, db_name):
        super().__init__(instance_time, destruct_time, name, engine_name)
        
        # MongoDB 연결
        self.client = MongoClient(db_server)
        self.image_folder = image_folder
        self.db_name = db_name

        self.init_state("Idle")
        self.insert_state("Idle", Infinite)
        self.insert_state("Load", 0)

        self.insert_input_port("load_command")
        self.insert_output_port("load_done")

    def ext_trans(self, port, msg):
        if port == "load_command":
            self._cur_state = "Load"

    def output(self):
        if self._cur_state == "Load":
            self.load()
            msg = SysMessage(self.get_name(), "load_done")
            msg.insert("Load operation completed")
            return msg

    def int_trans(self):
        if self._cur_state == "Load":
            self._cur_state = "Idle"

    def load(self):
        db = self.client[self.db_name]
        collection = db['Data']
        fs = gridfs.GridFS(db)

        data_path = self.image_folder # 저장할 경로
        data_cursor = collection.find()

        for it in data_cursor:
            image_id = it['imageData']
            image_data = fs.get(image_id).read()

            image_filename = fs.get(image_id).filename
            image_path = os.path.join(data_path, image_filename)

            with open(image_path, 'wb') as f:
                f.write(image_data)

            print(f"ID: {it['id']}")
            print(f"time: {it['item']}")
            print(f"Image Path: {it['imageData']}")
            print(f"Distance: {it['distance']}")
            print(f"Hit Info: {it['hitInfo']}")
            print()

        print("load data")

