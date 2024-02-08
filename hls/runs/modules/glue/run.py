import random
from modules.module_runner import ModuleRunner
import math

# create runner
runner = ModuleRunner("glue")

for _ in range(runner.max_runners):
    # generate parameters
    #runner.gen_parameters()

    runner.parameters['freq'] = 200

    runner.parameters['coarse_in']  =  random.randint(1, 32)
    runner.parameters['coarse_out'] =  random.randint(1, 32)

    runner.parameters['coarse_group'] = random.randint(0,1)
    if runner.parameters['coarse_group'] == 0:
        runner.parameters['coarse_group'] = random.randint(1, int(1024/runner.parameters['coarse_in']/runner.parameters['coarse_out']))


    runner.parameters['filters'] = int(random.randint(1,int(1024/runner.parameters['coarse_group']/runner.parameters['coarse_out'])) * runner.parameters['coarse_group']*runner.parameters['coarse_out'])

    runner.parameters['batch_size'] = 256
    runner.parameters['rows']       = random.randint(1,min(224,int(224*128/runner.parameters['filters'])))
    runner.parameters['cols']       = runner.parameters['rows']

    runner.parameters['data_int_width']=random.randint(1,30)
    runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)
    runner.parameters['acc_int_width']=random.randint(1,30)
    runner.parameters['acc_width']=random.randint(runner.parameters['acc_int_width']+1,32)

    # run tests
    runner.run()
