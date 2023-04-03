import random 
from modules.module_runner import ModuleRunner

class GlueFixed_runner(ModuleRunner):
    def __init__(self, max_runners=100):
        super().__init__("GlueFixed", max_runners)
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "coarse_in": 0,
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        self.parameters["coarse"] = random.randint(1,128)


if __name__ == "__main__":

    runner = GlueFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()


