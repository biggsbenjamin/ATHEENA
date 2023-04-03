import random
from modules.module_runner import ModuleRunner
from functools import reduce

class SlidingWindowFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("SlidingWindowFixed")
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
        self.parameters["kernel_size"] = [ random.randint(2,11), random.randint(2,11) ]
        self.parameters["rows"] = random.randint(self.parameters["kernel_size"][0],128)
        self.parameters["cols"] = random.randint(self.parameters["kernel_size"][1],128)
        self.parameters['stride'] = [
            random.choice(list(filter(lambda x: x < 4, self.get_factors(self.parameters['rows'] - self.parameters['kernel_size'][0])))),
            random.choice(list(filter(lambda x: x < 4, self.get_factors(self.parameters['cols'] - self.parameters['kernel_size'][1]))))
        ]

    def get_factors(self, n):
        #ToDo: fix reduce of empty sequence
        return list(set(reduce(list.__add__, ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0))))
  

if __name__ == "__main__":

    runner = SlidingWindowFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()


