import random
from modules.module_runner import ModuleRunner


class WeightsFromStreamFixed_runner(ModuleRunner):

    def __init__(self, max_runners=600):
        super().__init__("WeightsFromStreamFixed", max_runners)
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "size": 0,
            "fine": 0
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        channels = random.randint(1,96)
        kernel_size = random.randint(1,5) 
        filters = random.randint(1, 128)
        self.parameters["fine"] = filters
        self.parameters["size"] = kernel_size * kernel_size * channels


    
  

if __name__ == "__main__":

    runner = WeightsFromStreamFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()


