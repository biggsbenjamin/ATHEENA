import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("pool")

while 1:
    # generate parameters
    runner.gen_parameters()
    runner.parameters['kernel_size'] = random.randint(1,11)

    runner.parameters['data_int_width']=random.randint(1,30)
    runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)
    # run tests
    runner.run()
