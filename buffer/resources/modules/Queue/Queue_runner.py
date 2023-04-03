import random
from modules.module_runner import ModuleRunner

class Queue_runner(ModuleRunner):

    def __init__(self, max_runners=1000):
        super().__init__("Queue", max_runners)
        self.parameters = {
            "data_width": 0,
            "binary_point": 0,
            "depth": 0
        }

    def gen_parameters(self):
        self.parameters["data_width"] = random.choice([8,16,32])
        self.parameters["binary_point"] = self.parameters["data_width"]//2
        self.parameters["depth"] = random.randint(1,1024)

    def gen_template(self):
        #Dict keys order must corresponds with Chisel Module input parameters
        params = "FixedPoint({0}.W,{1}.BP),".format(
            self.parameters["data_width"],
            self.parameters["binary_point"]
            ) + self.get_params()

        inst = "{module}({params})".format(
            module=self.name,
            params=params
            )

        return inst

if __name__ == "__main__":

    runner = Queue_runner()

    for i in range(runner.max_runners):
        print("="*10, i+1, " run out of ", runner.max_runners, " runs", "="*10)
        runner.gen_parameters()
        runner.run()

    # runner.gen_parameters()
    # runner.run()




