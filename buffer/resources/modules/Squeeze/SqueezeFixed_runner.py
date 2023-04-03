import random
from modules.module_runner import ModuleRunner

class SqueezeFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("SqueezeFixed")
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "coarse_in": 0,
            "coarse_out": 0
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        self.parameters["coarse_in"] = random.randint(1,12)
        self.parameters["coarse_out"] = random.randint(1,12)

  

if __name__ == "__main__":

    runner = SqueezeFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()


