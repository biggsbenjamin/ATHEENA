import random
from modules.module_runner import ModuleRunner

def run_conv():
# create runner
    runner = ModuleRunner("conv")

    for _ in range(runner.max_runners):
        # generate parameters

        runner.parameters['freq'] = 200

        runner.parameters['groups'] = random.randint(0,1)
        if runner.parameters['groups'] == 0:
            runner.parameters['groups'] = int(2**random.randint(1,7))

        runner.parameters['channels'] = int(random.randint(1,int(128/runner.parameters['groups'])) * runner.parameters['groups'])
        runner.parameters['filters'] = int(random.randint(1,int(128/runner.parameters['groups'])) * runner.parameters['groups'])

        runner.parameters['batch_size'] = 256
        runner.parameters['rows']       = random.randint(1,min(224,int(224*128/max(runner.parameters['channels'],runner.parameters['filters']))))
        runner.parameters['cols']       = runner.parameters['rows']


        kernel_size = []
        for k in [1,3,5,7]:
            if k <= runner.parameters['rows']:
                kernel_size.append(k)

        runner.parameters['kernel_size_x'] = random.choice(kernel_size)
        runner.parameters['kernel_size_y'] = random.choice([1, runner.parameters['kernel_size_x']])
        runner.parameters['fine']        = random.choice(
            [1,runner.parameters['kernel_size_x'],runner.parameters['kernel_size_x']*runner.parameters['kernel_size_y']])

        # create random weights
        runner.parameters['data_int_width']=random.randint(1,16)
        runner.parameters['data_width']=2*runner.parameters['data_int_width']
        runner.parameters['weight_int_width']=random.randint(1,16)
        runner.parameters['weight_width']=2*runner.parameters['weight_int_width']
        runner.parameters['acc_int_width']=random.randint(1,16)
        runner.parameters['acc_width']=2*runner.parameters['acc_int_width']
        max_value = 2**((runner.parameters['acc_width']/2)-1)

        runner.gen_data(
            [
                int(runner.parameters['channels']/runner.parameters['groups']*runner.parameters['filters']),
                runner.parameters['kernel_size_x'],
                runner.parameters['kernel_size_y']

            ],
            "modules/conv/data/weights.csv",
            data_range=[-max_value,max_value])

        # run tests
        runner.run()

if __name__ == "__main__":
    run_conv()
