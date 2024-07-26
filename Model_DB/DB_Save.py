import os
import json
import gridfs
from pymongo import MongoClient

class MongoDBUploader:
    def __init__(self, db_host='localhost', db_port=27017):
        self.client = MongoClient(db_host, db_port)
        self.current_directory = os.path.dirname(os.path.abspath(__file__))

    def upload_data(self, json_file, image_folder_path):
        json_file_path = os.path.join(self.current_directory, json_file)
        image_folder_path = os.path.join(self.current_directory, image_folder_path)

        with open(json_file_path, 'r') as file:
            data = json.load(file)

        for it in data:
            image_path = os.path.join(image_folder_path, it['imageData'])
            name = it['id']
            db = self.client[name]
            collection = db['Data']
            fs = gridfs.GridFS(db)

            if os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    img_id = fs.put(img_file, filename=it['imageData'])
                    it['imageData'] = img_id  # 이미지 데이터를 GridFS ID로 대체
            else:
                print(f"Image {it['imageData']} not found in the specified folder.")

            collection.insert_one(it)

        print("Data upload completed")
