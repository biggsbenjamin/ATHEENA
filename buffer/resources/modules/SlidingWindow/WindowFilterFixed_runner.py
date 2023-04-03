import random
from modules.module_runner import ModuleRunner
from functools import reduce

class WindowFilterFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("WindowFilterFixed")
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "channels": 0,
            "rows": 0,
            "cols": 0,
            "kernel_size": 0,
            "stride": 0
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        self.parameters["channels"] = random.randint(2,96)
        self.parameters["kernel_size"] = random.randint(2,11) #Todo: need to address SlidingWindow issues with generating kernel_size=1
        self.parameters["rows"] = random.randint(self.parameters["kernel_size"],128)
        self.parameters["cols"] = self.parameters["rows"]
        pad = random.randint(0,10)
        self.parameters['stride'] = random.choice(self.get_factors(self.parameters['cols'] - self.parameters['kernel_size'] +2*pad))

    def get_factors(self, n):
        #ToDo: fix reduce of empty sequence
        return list(set(reduce(list.__add__, ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0))))
  

if __name__ == "__main__":

    runner = WindowFilterFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()


