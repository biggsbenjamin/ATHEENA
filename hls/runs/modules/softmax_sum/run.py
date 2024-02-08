import random
from modules.module_runner import ModuleRunner

def run_softmax_sum():
    # create runner
    runner = ModuleRunner("softmax_sum")

    #max runners
    runner.max_runners = 49
    print("runners:",runner.max_runners)

    #generating branchynet layer
    runner.gen_parameters()
    runner.parameters['rows'] = 1
    runner.parameters['cols'] = 1
    runner.parameters['channels'] = 10
    runner.parameters['freq'] = 150#random.randint(125,175)
    runner.parameters['data_int_width']=8#random.randint(1,30)
    runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)
    # run tests
    runner.run()

    for _ in range(runner.max_runners):
        # generate parameters
        runner.gen_parameters()
        runner.parameters['freq'] = 150#random.randint(125,175)
        runner.parameters['data_int_width']=8#random.randint(1,30)
        runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)

        print("Rows:{} Cols:{} Channels:{}".format(runner.parameters['rows'],
            runner.parameters['cols'],runner.parameters['channels']))
        # run tests
        runner.run()

if __name__ == "__main__":
    run_softmax_sum()
