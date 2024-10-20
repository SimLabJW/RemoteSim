import json

class ResponseFormat:
    @staticmethod
    def ok_command(ip, cmd):
        return json.dumps({"status": "ok", "msg" : f"{ip} : {cmd} Commanded."}), 200

    @staticmethod
    def err_command(ip):
        return json.dumps({"status": "err", "msg" : f"{ip} : Object did not responsed."}), 202

    @staticmethod
    def err_found(ip):
        return json.dumps({"status": "err", "msg" : f"{ip} : No Object IP Found."}), 202

    @staticmethod
    def err_except():
        return json.dumps({"status ": "except", "msg" : "Exception found in server."}), 500
    
    @staticmethod
    def err_stream(ip):
        return json.dumps({"status ": "err", "msg" : f"{ip} : Object is not streaming."}), 202
    
    @staticmethod
    def err_no_data(ip):
        return json.dumps({"status ": "err", "msg" : f"{ip} : Object data not found."}), 202
    
    @staticmethod
    def err_convert():
        return json.dumps({"status": "err", "msg" : f"Could not convert img."}), 202

    @staticmethod
    def ok_delete(ip):
        return json.dumps({"status": "ok", "msg" : f"{ip} : Object Deleted."}), 200

    @staticmethod
    def ok_scan(_ip_dict):
        return json.dumps(_ip_dict), 200
        
    # @staticmethod
    # def ok_info(id, time, imageData, distance):
    #     return json.dumps({
    #         "id": id,
    #         "time": time,
    #         "imageData": imageData,
    #         "distance": distance           
    #     }), 200
        
    @staticmethod
    def ok_info(id, hit, distance):
        return json.dumps({
            "id": id,
            "hit": hit,
            "distance": distance           
        }), 200        
        
        
    @staticmethod
    def ok_state(ip, state):
        return json.dumps({
            "ip": ip,
            "state": state
        }), 200
        
    # @staticmethod
    # def err_obj_response():
    #     pass

