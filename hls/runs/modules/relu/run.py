import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("relu")

for _ in range(runner.max_runners):
    # generate parameters
    runner.gen_parameters()
    runner.parameters['freq']=150
    runner.parameters['batch_size']=1024
    runner.parameters['data_int_width']=8#random.randint(1,30)
    runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)
    # run tests
    runner.run()
