import os
import json

filepath = "modules/sliding_window/logs"
result_files = os.listdir(filepath)
for result_file in result_files:
    if result_file.endswith(".json"):
        try:
            with open(f"{filepath}/{result_file}","r") as f:
                tmp = json.load(f)
            rsc = tmp["resources"]
            if rsc["LUT"] == 0 and rsc["FF"] == 0 and rsc["BRAM"] == 0 and rsc["DSP"] == 0:
                os.remove(f"{filepath}/{result_file}")
        except:
            print(f"Cannot open {result_file}") 


