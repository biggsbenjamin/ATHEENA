'''
Functions to compute all your buffering needs!
'''

### imports ###
import numpy as np
import math

def get_bram_allowance(max_rsc_pc, bram_usage, platform_bram):
    # return the bram allowance and the new bram usage
    bram_pc = float(bram_usage)/float(platform_bram)
    bram_available = math.floor(max_rsc_pc*platform_bram - bram_usage)
    return bram_available

# Calculating remaining space available to buffers
# returns bram (and equivalent min delay), q depth
def get_buffer_size(input_shape,batch_size,
                    bram_available,
                    zbrd_flag=True):
    # should deduct much smaller results buffer
    # input_shape is the rows,cols,chans of intermediate feature map
    # batch_size - for small networks might be better to jsut max out
    # bram_used - list of stages and their predicted bram utilisaiton
    # bram_total - from the board info, how much total available (under constraints)
    # should have flag for board type (older boards require nearset pow2)
    fm_size = input_shape[0]*input_shape[1]*input_shape[2] / input_shape[3]
    if zbrd_flag:
        # for very close to bram limit
        if bram_available == 0:
            return 0, 0, 1
        max_bram_size = 2**math.floor(math.log2(bram_available/float(input_shape[3])))
    else:
        # for very close to bram limit
        if bram_available == 0:
            return 0, 0, 1
        max_bram_size = math.floor(bram_available/float(input_shape[3]))
    # NOTE assumes 16bits data width
    q_depth = math.floor((max_bram_size*1024)/fm_size)
    # for very close to bram limit
    if q_depth == 0:
        return 0, 0, 1
    # recalc additional bram used
    # calcs value for 1 instance (coarse-1) remaining
    bram = 2**math.ceil(math.log2((q_depth*fm_size)/1024))
    # FIXME total bram consumption will be slightly larger
    # IO fifos not included in model, smaller buffer not factored in
    if bram >= bram_available: #max_bram_size:
        q_depth-=1
        # for very close to bram limit
        if q_depth == 0:
            return 0, 0, 1
        bram = 2**math.ceil(math.log2((q_depth*fm_size)/1024))
        #raise ValueError(f"BRAM calc mismatch. bram:{bram}, max:{max_bram_size}")
    # calc min delay (include 16 min fms)
    min_delay = fm_size*q_depth
    # re-scale the bram use by coarse factor (separate buffers)
    return bram*input_shape[3], min_delay, q_depth

### MG1K Smith approximation of throughput dependent on q size
def get_svt_coef(svt_ls,svt_probs):
    # svt - service time
    mean_service_time = 0.0
    var_service_time = 0.0
    for svt,prob in zip(svt_ls,svt_probs):
        mean_service_time += prob*svt
        var_service_time += prob*(svt**2)
    var_service_time -= mean_service_time**2
    # s: variance over expected service time (in 1/(samples/second))
    # squared coef of var of service time
    s2 = var_service_time/(mean_service_time**2)
    return s2,mean_service_time,var_service_time

def get_p_K(rho, s2, q_s):
    pk_com = 2 + (math.sqrt(rho)*s2) - math.sqrt(rho)
    p_K_num_pow = (pk_com + (2*q_s))/pk_com
    p_K_den_pow = (2*(pk_com + q_s))/pk_com

    # basic overflow compensation
    if math.isclose((p_K_num_pow+1),p_K_den_pow,abs_tol=1e-12) and \
            p_K_den_pow > 300 and rho>1:
        #print(p_K_num_pow+1, p_K_den_pow)
        p_K = 1.0 - (1/rho)
    else:
        p_K = ((rho**p_K_num_pow) * (rho - 1))/((rho**p_K_den_pow) - 1 )
    return p_K

# p0 prob, derived from thruput in = thruput out (steady state)
def get_p_0(rho, s2, q_s):
    c = (math.sqrt(rho)*s2) - math.sqrt(rho)
    rho_pow_num = 2*(c + q_s + 2)
    rho_pow_den = c+2
    main_power = (rho_pow_num/rho_pow_den)
    # basic overflow compensation - TODO do envelope calc for pow lim
    if rho > 1 and main_power > 300:
        #print(main_power)
        p_0 = 0.0
    else:
        p_0 = (rho-1)/((rho**main_power)-1)
    return p_0

def get_throughput_pred(s1_thru,s2_thru,s2_exit_frac,freq_mhz,q_depth):
    cycle_time=freq_mhz*(10**6)
    #print(f"cycle time:{cycle_time:0.2e}, s2 late: {(1/s2_thru):0.2e}")
    s2_servicetimes = [(1.0/cycle_time),(1.0/s2_thru)]
    s2_probs = [1-s2_exit_frac,s2_exit_frac]
    # M/G/1/N calculated results - note worse s^2,compared to poi
    s2,mean,var = get_svt_coef(s2_servicetimes,s2_probs)
    rho = s1_thru * mean  # lambda/mu, avg traffic intensity
    #print(f"rho : {rho}, s2: {s2}, qd: {q_depth}")
    p_0_smith = get_p_0(rho,s2,q_depth)
    p_n_smith = get_p_K(rho,s2,q_depth)
    thru_smith = 1-p_n_smith
    #print(f"thru: {thru_smith}, thrus1: {s1_thru}, thrus2: {1/mean}")
    thru_smith_alt = (1-p_0_smith)/rho
    if not math.isclose(thru_smith,thru_smith_alt,abs_tol=1e-12):
        raise ValueError(f"Throughput approx. mismatch {thru_smith}, {p_n_smith}, {thru_smith_alt}")
    return s1_thru*thru_smith, rho
