import random
from modules.module_runner import ModuleRunner

class MaxPoolFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("MaxPoolFixed")
        self.parameters = {
            "data_width" : 0,
            "binary_point" : 0,
            "kernel_size": 0
        }

    def gen_parameters(self): 
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        self.parameters["kernel_size"] = [ random.randint(1,4), random.randint(1,4) ]

    # def gen_parameters(self):
    #     self.parameters["data_width"] = 32
    #     self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
    #     self.parameters["kernel_size"] = random.randint(2,6)
  

if __name__ == "__main__":

    runner = MaxPoolFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()
