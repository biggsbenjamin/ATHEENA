import random
from modules.module_runner import ModuleRunner

# create runner
runner = ModuleRunner("fork")

for _ in range(runner.max_runners):
    # generate parameters

    runner.parameters['freq'] = 200

    runner.parameters['coarse']      = random.randint(1,32)
    runner.parameters['channels'] = int(random.randint(1,int(1024/runner.parameters['coarse'])) * runner.parameters['coarse'])

    runner.parameters['batch_size'] = 256
    runner.parameters['rows']       = random.randint(1,min(224,int(224*128/runner.parameters['channels'])))
    runner.parameters['cols']       = runner.parameters['rows']

    runner.parameters['kernel_size_x'] = random.randint(1,3)
    runner.parameters['kernel_size_y'] = random.choice([1, runner.parameters['kernel_size_x']])

    runner.parameters['data_int_width']=random.randint(1,30)
    runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)

    # run tests
    runner.run()
