import random
from modules.module_runner import ModuleRunner

class VectorDotFixed_runner(ModuleRunner):

    def __init__(self):
        super().__init__("VectorDotFixed")
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "filters": 0,
            "fine": 0
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        kernel_size = random.randint(1,10)
        self.parameters["fine"] = kernel_size * kernel_size
        self.parameters["filters"] = random.randint(1,128)

if __name__ == "__main__":

    runner = VectorDotFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()

