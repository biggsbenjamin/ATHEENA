import random
from modules.module_runner import ModuleRunner

class ConcatFixed_runner(ModuleRunner):

    def __init__(self, max_runners=1000):
        super().__init__("ConcatFixed", max_runners)
        self.parameters = {
            "data_width" : 0,
            "binary_point" : 0,
            "ports_in": 0,
            "channels": ""
        }
        self.channels_int = []

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = int(self.parameters["data_width"]/2)
        self.parameters["ports_in"] = random.randint(1, 8)
        self.channels_int = []
        for i in range(self.parameters["ports_in"]):
            self.channels_int.append(str(random.randint(1, 128)))
        self.parameters["channels"] = self.gen_scala_list()

    def gen_scala_list(self):
        elements = ",".join([str(val) for val in self.channels_int])
        return "List({0})".format(elements)

    def get_param_names(self):
        #overide
        param_names = []
        channels_str = ",".join([str(val) for val in self.channels_int])
        for key, val in self.parameters.items():
            if key != "channels":
                param_names.append(key + "_" + str(val))
        
        return "_".join(param_names) + "_channels_" + channels_str



  

if __name__ == "__main__":

    runner = ConcatFixed_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()