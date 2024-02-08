import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("mem_write")

while 1:
    # generate parameters
    runner.gen_parameters()
    runner.parameters['cols_out']     = runner.parameters['cols']
    runner.parameters['rows_out']     = runner.parameters['rows']
    runner.parameters['channels_out'] = runner.parameters['channels']
    runner.parameters['coarse_out']   = random.choice(
        runner.get_factors(runner.parameters['channels']))
    runner.parameters['weights_reloading_factor'] = random.choice(
        runner.get_factors(int(runner.parameters['channels']/runner.parameters['coarse_out'])))
    runner.parameters['weights_reloading_index'] = random.randint(0,runner.parameters['weights_reloading_factor']-1)
    # run tests
    runner.run()
