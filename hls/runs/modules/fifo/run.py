import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("fifo")

for _ in range(runner.max_runners):
    # generate parameters
    #runner.gen_parameters()
    runner.parameters['freq'] = 200 

    runner.parameters['depth'] = random.randint(1, 64)
    runner.parameters['coarse'] = random.randint(1, 256)
    runner.parameters['data_width'] = 16
    # run tests
    runner.run()
