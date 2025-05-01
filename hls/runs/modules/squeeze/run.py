import random
from modules.module_runner import ModuleRunner
from math import gcd

# create runner
runner = ModuleRunner("squeeze")

for _ in range(runner.max_runners):
    # generate parameters
    runner.parameters['freq'] = 150
    runner.parameters['batch_size'] = 1024
    runner.parameters['coarse_in']  = random.randint(1,32)
    runner.parameters['coarse_out'] = random.randint(1,32)
    # get lcm
    coarse_lcm = int(runner.parameters['coarse_in']*runner.parameters['coarse_out']/gcd(runner.parameters['coarse_in'],runner.parameters['coarse_out']))

    # get list of channel multiples
    chan_list = [i*coarse_lcm for i in range(1,10) if i*coarse_lcm < 1024]
    if not chan_list:
        continue
    runner.parameters['channels'] = random.choice(chan_list)

    runner.parameters['rows'] = random.randint(1,min(224,int(224*128/runner.parameters['channels'])))
    runner.parameters['cols'] = runner.parameters['rows']

    runner.parameters['data_int_width']=8#random.randint(1,30)
    runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)

    runner.parameters['channels_per_coarse_in'] = int(runner.parameters['channels']/runner.parameters['coarse_in'])
    runner.parameters['channels_per_coarse_out']= int(runner.parameters['channels']/runner.parameters['coarse_out'])
    # run tests
    runner.run()
