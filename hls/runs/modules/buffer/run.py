import random
from modules.module_runner import ModuleRunner
#from module_runner import ModuleRunner

def run_buffer():
    # create runner
    runner = ModuleRunner("buffer")

    #max runners
    runner.max_runners = 50
    print("runners:",runner.max_runners)

    for _ in range(runner.max_runners):
        # generate parameters
        runner.gen_parameters()
        runner.parameters['freq'] = 150#random.randint(125,175)
        runner.parameters['drop_mode'] = random.choice(['true','false'])
        runner.parameters['data_int_width']=8#random.randint(1,30)
        runner.parameters['data_width']=16#random.randint(runner.parameters['data_int_width']+1,32)
        # run tests
        runner.run()

if __name__ == "__main__":
    run_buffer()
