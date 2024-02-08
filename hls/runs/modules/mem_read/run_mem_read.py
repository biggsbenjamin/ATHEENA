import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("mem_read")

while 1:
    # generate parameters
    runner.gen_parameters()
    runner.parameters['cols_in']     = runner.parameters['cols']
    runner.parameters['rows_in']     = runner.parameters['rows']
    runner.parameters['channels_in'] = runner.parameters['channels']
    runner.parameters['coarse_in']   = random.choice(
        runner.get_factors(runner.parameters['channels']))
    # run tests
    runner.run()
