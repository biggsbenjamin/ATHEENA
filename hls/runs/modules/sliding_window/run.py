import random
from modules.module_runner import ModuleRunner

def run_sw():
# create runner
    runner = ModuleRunner("sliding_window")

    for _ in range(runner.max_runners):
        # generate parameters
        #runner.gen_parameters()

        runner.parameters['freq'] = 150

        runner.parameters['channels'] = random.randint(1, 256)

        runner.parameters['batch_size'] = 256
        runner.parameters['rows']       = random.randint(1,min(224,int(224*256/runner.parameters['channels'])))
        runner.parameters['cols']       = runner.parameters['rows']

        runner.parameters['kernel_size_x'] = random.randint(1, min(11,runner.parameters['rows']))
        runner.parameters['kernel_size_y'] = random.randint(1, min(11,runner.parameters['cols']))

        runner.parameters['pad_top']  = random.randint(0,runner.parameters['kernel_size_x']-1)
        runner.parameters['pad_left'] = random.randint(0,runner.parameters['kernel_size_y']-1)
        runner.parameters['pad_bottom'] = runner.parameters['pad_top']
        runner.parameters['pad_right']  = runner.parameters['pad_left']
        runner.parameters['stride_x'] = random.choice(
            runner.get_factors( max(1,int(runner.parameters['rows'] - runner.parameters['kernel_size_x'] +2*runner.parameters['pad_top'])) ))
        runner.parameters['stride_y'] = random.choice(
            runner.get_factors( max(1,int(runner.parameters['cols'] - runner.parameters['kernel_size_y'] +2*runner.parameters['pad_left'])) ))

        runner.parameters['data_int_width']=random.randint(1,30)
        runner.parameters['data_width']=random.randint(runner.parameters['data_int_width']+1,32)

        # run tests
        runner.run()

if __name__ == "__main__":
    run_sw()
