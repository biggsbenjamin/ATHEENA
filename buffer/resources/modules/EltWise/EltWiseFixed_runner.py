import random
from modules.module_runner import ModuleRunner

class EltWiseFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("EltWiseFixed")
        self.parameters = {
            "data_width" : 0,
            "binary_point" : 0,
            "ports_in": 0
        }

    def gen_parameters(self):
        self.parameters["ports_in"] = random.randint(1,256) #
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
  

if __name__ == "__main__":

    runner = EltWiseFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()