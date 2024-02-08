import random
from modules.module_runner import ModuleRunner
#from module_runner import ModuleRunner

def run_conv():
# create runner
    runner = ModuleRunner("accum")

    for _ in range(runner.max_runners):
        # generate parameters
        runner.gen_parameters()
        runner.parameters['filters'] = random.randint(1,1024)
        channels_group_factor = runner.get_factors(runner.parameters['channels'])
        filters_group_factor  = runner.get_factors(runner.parameters['filters'])
        runner.parameters['groups'] = random.choice(list(set(channels_group_factor)&set(filters_group_factor)))
        runner.parameters['data_int_width']=random.randint(1,30)
        runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)
        # run tests
        runner.run()

if __name__ == "__main__":
    run_conv()
