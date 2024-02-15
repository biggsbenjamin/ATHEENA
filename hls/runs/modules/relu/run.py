import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("relu")

while 1:
    # generate parameters
    runner.gen_parameters()
    runner.parameters['data_int_width']=random.randint(1,30)
    runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)
    # run tests
    runner.run()