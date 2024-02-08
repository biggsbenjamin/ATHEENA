import random
from modules.module_runner import ModuleRunner

def run_compare():
    # create runner
    runner = ModuleRunner("compare")

    #max runners
    runner.max_runners = 50
    print("runners:",runner.max_runners)

    for _ in range(runner.max_runners):
        # generate parameters
        runner.gen_parameters()
        runner.parameters['threshold'] = 0.9#round(random.random(), 4)
        runner.parameters['cmp_type'] = "gt" #greater than comparison
        runner.parameters['freq'] = 150#random.randint(125,175)
        runner.parameters['data_int_width']=8#random.randint(1,30)
        runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)

        print("Batch size:{} Threshold:{}".format(runner.parameters['batch_size'],
            runner.parameters['threshold']))
        # run tests
        runner.run()

if __name__ == "__main__":
    run_compare()
