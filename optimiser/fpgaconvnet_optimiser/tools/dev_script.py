#from graphviz import Digraph
import pydot
import os
import random
import copy
import onnx
import networkx as nx
import argparse
from datetime import datetime as dt

import fpgaconvnet_optimiser.tools.onnx_helper as onnx_helper
from fpgaconvnet_optimiser.tools.layer_enum import LAYER_TYPE

import fpgaconvnet_optimiser.tools.parser as parser

from fpgaconvnet_optimiser.models.network import Network
from fpgaconvnet_optimiser.models.partition import Partition
from fpgaconvnet_optimiser.optimiser.simulated_annealing import SimulatedAnnealing

#for optimiser
import yaml
#for graphing
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as mcol
import matplotlib.lines as mlines
import matplotlib.patches as mpat
import json

###########################################################
####################### optimiser expr ####################
###########################################################

def optim_expr(args,filepath,is_branchy,opt_path,plat_path):
    #opt_path is path of optimiser example config .yml file

    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
        print("gen op path")

    #add optimiser config
    with open(opt_path,"r") as f:
        optimiser_config = yaml.load(f, Loader=yaml.Loader)
        print("loading opt conf")

    print("Starting optimisation")
    net = SimulatedAnnealing(
            args.save_name,
            filepath,#args.model_path,
            T=float(optimiser_config["annealing"]["T"]),
            T_min=float(optimiser_config["annealing"]["T_min"]),
            k=float(optimiser_config["annealing"]["k"]),
            cool=float(optimiser_config["annealing"]["cool"]),
            iterations=int(optimiser_config["annealing"]["iterations"]),
            transforms_config=optimiser_config["transforms"],
            checkpoint=bool(optimiser_config["general"]["checkpoints"]),
            checkpoint_path=os.path.join(args.output_path,"checkpoint"),
            rsc_allocation=float(optimiser_config["general"]["resource_allocation"])
            )
    net.DEBUG=True #NOTE this is required, object doesnt have DEBUG unless declared
    net.objective  = 1 #NOTE throughput objective (default is latency)
    print("generated simulated annealing object")

    #updating params
    net.batch_size = args.batch_size
    net.update_platform(plat_path)
    # update partitions
    net.update_partitions()

    # complete fine transform for conv layers is more resource efficient
    if bool(optimiser_config["transforms"]["fine"]["start_complete"]):
        print("applying fine max transform")
        for partition_index in range(len(net.partitions)):
            net.partitions[partition_index].apply_complete_fine()

    #print("Saving Network - no partition")
    #net.save_all_partitions(args.output_path) # NOTE saves as one partition
    #net.get_schedule_csv("scheduler.csv") #for scheduler for running on board
    #print("#################### Finished saving full network #######################")

    if is_branchy:

        #print("Pre Number of partitions:",len(net.partitions))
        #saving un-optimised, unsplit network
        old_name = net.name
        net.name = old_name+"-noOpt-noESplit"
        net.save_all_partitions(args.output_path)
        print("Saved no opt, no exit split")
        #NOTE removing for time being

        # network function to create ee partitions
        net.name = old_name+"-noOpt"
        # NOTE very important function!
        net.exit_split(partition_index=0)
        print("Exit split complete")
        net.save_all_partitions(args.output_path)
        print("Saved no opt")
        print("Post Number of partitions:",len(net.partitions))
        # resetting name before optimisation
        net.name = old_name

    auto_flag=True #carry out lots of runs at different rsc if true
    #if not auto_flag: #one run on partitions at optimiser_example specified rsc usage
    #    net.rsc_allocation = 0.75 #forcing low rsc usage for debug
    #    print(f"Attempting optim @ rsc:{net.rsc_allocation}")
    #    net.run_optimiser()
    #    print("Optimiser done, attempting partition update")
    #    net.update_partitions()
    #    print("Update done, attempting results saving")

    #    #create folder to store results - percentage/iteration
    #    post_optim_path = os.path.join(args.output_path,
    #            "post_optim-rsc{}p".format(int(net.rsc_allocation*100)))
    #    if not os.path.exists(post_optim_path):
    #        os.makedirs(post_optim_path)
    #    # save all partitions
    #    net.save_all_partitions(post_optim_path)
    #    print("Partitions saved")
    #    # create report
    #    net.create_report(os.path.join(post_optim_path,
    #        "report_{}.json".format(net.name)))
    #    # visualise network
    #    #net.visualise(os.path.join(post_optim_path,"topology.png"))

    ### FOR LOOP FOR REPEATED OPTIMISATION ###
    #NOTE expose these to the expr top level
    #rsc_limits = [0.1,0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    rsc_limits = [0.1,0.2,0.3,0.4,0.5,0.6]
    full_sa_runs = 10
    print(f"Using Resource limits:{} for {} runs each.".format(rsc_limits,full_sa_runs))

    if auto_flag:
        if is_branchy:
            for rsc in rsc_limits:
                for sa_i in range(full_sa_runs):
                    #deep copy the network
                    nets = [copy.deepcopy(net), copy.deepcopy(net)]
                    #remove other partition
                    nets[0].partitions.pop(0)
                    nets[1].partitions.pop(1)

                    #change the network name
                    if len(nets[0].partitions[0].graph.nodes) > len(nets[1].partitions[0].graph.nodes):
                        nets[0].name = nets[0].name+"-ee1-rsc{}p-iter{}".format(int(rsc*100),sa_i)
                        nets[1].name = nets[1].name+"-eef-rsc{}p-iter{}".format(int(rsc*100),sa_i)
                    else:
                        nets[0].name = nets[0].name+"-eef-rsc{}p-iter{}".format(int(rsc*100),sa_i)
                        nets[1].name = nets[1].name+"-ee1-rsc{}p-iter{}".format(int(rsc*100),sa_i)

                    for split in nets:
                        split.rsc_allocation = rsc
                        print("\nRunning split: {}".format(split.name))

                        # NOTE implements eef only when wrapped around pass flag cond
                        #if "eef" in split.name:
                            #print("WARNING: EEF ONLY")
                        # NOTE implements eef only when wrapped around pass flag cond

                        pass_flag = split.run_optimiser() #true = pass
                        if pass_flag:
                            # update all partitions
                            split.update_partitions()
                            #create folder to store results - percentage/iteration
                            post_optim_path = os.path.join(args.output_path,
                                    "post_optim-rsc{}p".format(int(rsc*100)))
                            if not os.path.exists(post_optim_path):
                                os.makedirs(post_optim_path)

                            # save all partitions
                            split.save_all_partitions(post_optim_path)
                            print("Partitions saved")
                            # create report
                            split.create_report(os.path.join(post_optim_path,
                                "report_{}.json".format(split.name)))
                            # NOTE following not used
                            # visualise network
                            #split.visualise(os.path.join(post_optim_path,"topology.png"))
                            # create scheduler
                            #split.get_schedule_csv(os.path.join(args.output_path,"scheduler.csv"))
        else:
            # not branchy optimisation loop
            for rsc in rsc_limits:
                for sa_i in range(full_sa_runs):
                    runner = copy.deepcopy(net)
                    runner.name = runner.name+"-rsc{}p-iter{}".format(int(rsc*100),sa_i)
                    runner.rsc_allocation = rsc
                    print("\nRunning net: {}".format(runner.name))
                    pass_flag = runner.run_optimiser() #true = pass
                    if pass_flag:
                        # update all partitions
                        runner.update_partitions()
                        #create folder to store results - percentage/iteration
                        post_optim_path = os.path.join(args.output_path,
                                "post_optim-rsc{}p".format(int(rsc*100)))
                        if not os.path.exists(post_optim_path):
                            os.makedirs(post_optim_path)

                        # save all partitions
                        runner.save_all_partitions(post_optim_path)
                        print("Partitions saved")
                        # create report
                        runner.create_report(os.path.join(post_optim_path,
                            "report_{}.json".format(runner.name)))
                        # NOTE following not used
                        # visualise network
                        #runner.visualise(os.path.join(post_optim_path,"topology.png"))
                        # create scheduler
                        #runner.get_schedule_csv(os.path.join(args.output_path,"scheduler.csv"))

#pull out throughput info, rsc usage
#"network"
#    "performance"
#    "throughput"
#"max_resource_usage"
#    "LUT"
#    "FF"
#    "BRAM"
#    "DSP"
def extract_rpt_data(data_dict, input_path, report_str=""):
    #resources to search through
    rsc_names = ["LUT","FF","BRAM","DSP"]
    dirs_list = os.listdir(input_path)
    platform_dict={}
    for dirs in dirs_list:
        current_path = os.path.join(input_path,dirs)
        if (not os.path.isfile(current_path)) and\
            ("post_optim" in dirs):
            reports = os.listdir(current_path)
            rsc_p = int(dirs.split("-")[1][3:-1])
            print("In directory:",dirs,"\nResource percentage:",rsc_p)

            for repf in reports:
                # check for report and report contains specified string in the title
                if 'report' in repf and report_str in repf:
                    #open report file
                    open_repf = open(os.path.join(current_path,repf),"r")
                    #load report into json (dict)
                    repf_json = json.loads(open_repf.read())
                    #get dict of available resources for platform used
                    platform_dict = repf_json["platform"]["constraints"]
                    #get overall throughput
                    throughput = float(repf_json["network"]["performance"]["throughput"])
                    #get overall resource usage
                    rsc_dict = repf_json["network"]["max_resource_usage"]
                    #get the percentage of available resources for all the resource types
                    actual_rsc = []
                    for rn in rsc_names:
                        res_percent = float(rsc_dict[rn])/float(platform_dict[rn])
                        #data_dict[rn].append(res_percent)
                        data_dict[rn].append(rsc_dict[rn]) #store actual resource value
                        actual_rsc.append([res_percent,rn])
                    #get maximum of each of the resource types (limiting resource possibly)
                    idx_max = max(range(len(actual_rsc)), key=actual_rsc.__getitem__)
                    #print(repf,"::",actual_rsc,"::",actual_rsc[idx_max])
                    #append lists with report data
                    data_dict["throughput"].append(throughput)
                    data_dict["resource_max"].append(actual_rsc[idx_max][0])
                    data_dict["limiting_resource"].append(actual_rsc[idx_max][1])
                    data_dict["report_name"].append(repf)
    #need the platform stats
    return platform_dict

def combine_network_sections(args, ee1_data, eef_data,
        platform_dict, baseline_data, eef_exit_fraction=0.5):
    rsc_names = ["LUT","FF","BRAM","DSP"]

    combined_dict ={"report_name":[],"throughput":[],
                    "ee1_throughput":[], "eef_throughput":[],
                    "eef_throughput_scaled":[],
                    "resource_max":[], "limiting_resource":[],
                    "LUT":[], "FF":[], "BRAM":[], "DSP":[]}

    ee1_len = len(ee1_data["report_name"])
    eef_len = len(eef_data["report_name"])
    for ee1_idx in range(ee1_len):
        for eef_idx in range(eef_len):
            ee1_thru = ee1_data["throughput"][ee1_idx]
            eef_thru = float(eef_data["throughput"][eef_idx])/eef_exit_fraction
            #pair up each
            combined_dict["report_name"].append(
                    (ee1_data["report_name"][ee1_idx],eef_data["report_name"][eef_idx]))
            #raw throughputs
            combined_dict["ee1_throughput"].append(ee1_thru)
            combined_dict["eef_throughput"].append(eef_data["throughput"][eef_idx])
            combined_dict["eef_throughput_scaled"].append(eef_thru)
            #minimum of the exit throughputs (limiting thr)
            combined_dict["throughput"].append(min(ee1_thru, eef_thru))
            #for getting the limiting rsc
            actual_rsc = []
            for rn in rsc_names:
                rsc_sum = ee1_data[rn][ee1_idx]+eef_data[rn][eef_idx]
                res_percent = rsc_sum/float(platform_dict[rn])
                combined_dict[rn].append(res_percent)
                actual_rsc.append([res_percent,rn])
            idx_max = max(range(len(actual_rsc)), key=actual_rsc.__getitem__)
            combined_dict["resource_max"].append(actual_rsc[idx_max][0])
            combined_dict["limiting_resource"].append(actual_rsc[idx_max][1])
    #change to numpy arrays
    for key in combined_dict.keys():
        combined_dict[key] = np.array(combined_dict[key])
    return combined_dict

def pareto_front(data_dict, resource_string):
    #generate list of indices for pareto front
    #get list of throughputs and resource(s)
    point_len = len(data_dict["throughput"])
    #construct numpy array of throughput and resource max
    np_data = np.empty((point_len,2))
    for i,(thr,rsc) in enumerate(
            zip(data_dict["throughput"],
                data_dict[resource_string])):
        np_data[i][0] = 1/float(thr)
        np_data[i][1] = rsc
    #print("PARETO\n",np_data)

    is_efficient = np.arange(np_data.shape[0])
    point_total = np_data.shape[0]
    next_point_index = 0
    while next_point_index<len(np_data):
        nd_point_mask = np.any(np_data<np_data[next_point_index], axis=1)
        nd_point_mask[next_point_index] = True
        is_efficient = is_efficient[nd_point_mask]
        np_data = np_data[nd_point_mask]
        next_point_index = np.sum(nd_point_mask[:next_point_index])+1
    #return mask
    is_efficient_mask = np.zeros(point_total, dtype=bool)
    is_efficient_mask[is_efficient] = True
    #print("efficieny mask\n", is_efficient_mask)
    #print("is eff\n",is_efficient)

    #sort along the pareto front
    sort_xy = np.lexsort((data_dict['resource_max'][is_efficient_mask],
                            data_dict["throughput"][is_efficient_mask]))

    return is_efficient, is_efficient_mask, sort_xy


#function to reduce copy pasting code for graph gen
def _gen_graph(args,ee_flag,baseline_flag,rsc_str,
        ee1_data,eef_data,baseline_data):
    #generate graphs of chosen resource vs throughput
    #plot baseline or otherwise as chosen
    rsc_markers = {"LUT":'o',"FF":'s',"BRAM":'d',"DSP":'h'}
    fig, ax = plt.subplots()
    subtitle_str = ""
    if ee_flag:
        print("ee1 len:{}".format(len(ee1_data[rsc_str])))
        print("eef len:{}".format(len(eef_data[rsc_str])))
        ax.scatter(ee1_data[rsc_str], ee1_data["throughput"], c="blue", label='EE1')
        ax.scatter(eef_data[rsc_str], eef_data["throughput"], c="black", label='EEF')
        subtitle_str+= "-EE-"

    if baseline_flag:
        print("base len:{}".format(len(baseline_data[rsc_str])))
        ax.scatter(baseline_data[rsc_str], baseline_data["throughput"], c="red", label='BASE')
        subtitle_str+="-BASE-"

    #fix the title of the plot
    ax.set(xlabel='Fraction of {}s'.format(rsc_str), ylabel='Throughput (samples/s)',
            title='Exit resource throughput plot {}\n({})'.format(subtitle_str,args.save_name))
    ax.legend(loc='best')
    ax.grid()
    plt.xlim(0.05,1.0)
    #save plot
    if args.save_name is not None:
        fig.savefig(os.path.join(args.output_path,"plot_{}_{}.pdf".format(args.save_name,rsc_str)))
    else:
        fig.savefig(os.path.join(args.output_path,"plot_{}.pdf".format(rsc_str)))
    print("Saved {} Graph".format(rsc_str))

def gen_graph(args):
    '''
    function for graphing optimiser results for EE and baseline

    if -bi only then only do baseline results
        red colour
        graph labelled baseline

    if -i then just do EE results
        EE1 is blue
        EEF is black
        graph labelled early exit

    if -i ... -bi ... then plot both

    make folder paths part of the saving process somehow, report?
        network name
        -i path
        number of points for EE1 and EEF
        -bi path
        number of points for baseline
    '''
    rsc_names = ["LUT","FF","BRAM","DSP"]
    if not os.path.exists(args.output_path):
        print("Creating output path:",args.output_path)
        os.makedirs(args.output_path)

    if args.input_path is None:
        #doing baseline
        assert(args.baseline_input_path is not None)
        baseline_flag=True
        ee_flag=False
    elif args.baseline_input_path is None:
        #do EE only
        assert(args.input_path is not None)
        baseline_flag=False
        ee_flag=True
    else:
        #neither are none so do joint graph
        print("Joint graph")
        baseline_flag=True
        ee_flag=True

    #init data dicts
    ee1_data = {"report_name":[], "throughput":[],
                "resource_max":[], "limiting_resource":[],
                "LUT":[], "FF":[], "BRAM":[], "DSP":[]}
    eef_data = copy.deepcopy(ee1_data)
    baseline_data = copy.deepcopy(ee1_data)

    if ee_flag:
        platform_dict=extract_rpt_data(ee1_data, args.input_path, 'ee1')
        extract_rpt_data(eef_data, args.input_path, 'eef')
    if baseline_flag:
        platform_dict=extract_rpt_data(baseline_data,
                args.baseline_input_path)
    #gen max graph
    _gen_graph(args,ee_flag,baseline_flag,"resource_max",
            ee1_data,eef_data,baseline_data)
    #generate individual rsc graph
    #for rsc in rsc_names:
    #    _gen_graph(args,ee_flag,baseline_flag,rsc,
    #       ee1_data,eef_data,baseline_data)
    # switch lists to numpy arrays
    for key in ee1_data.keys():
        ee1_data[key] = np.array(ee1_data[key])
    for key in eef_data.keys():
        eef_data[key] = np.array(eef_data[key])
    for key in baseline_data.keys():
        baseline_data[key] = np.array(baseline_data[key])

    #create combined plot
    rsc_markers = {"LUT":'s',"FF":'d',"BRAM":'x',"DSP":'o'}
    if baseline_flag or ee_flag:
        #get the numpy masks for the pareto front for ee1 and baseline
        if ee_flag:
            _, pareto_ee1_mask,srt_ee1_idx = pareto_front(ee1_data, "resource_max")
            _, pareto_eef_mask,srt_eef_idx = pareto_front(eef_data, "resource_max")
        _, pareto_base_mask,srt_base_idx = pareto_front(baseline_data, "resource_max")

        #save to csv
        base_x=baseline_data['resource_max'][pareto_base_mask][srt_base_idx]
        base_y=baseline_data['throughput'][pareto_base_mask][srt_base_idx]
        base_xy=np.vstack((base_x,base_y)).T
        np.savetxt(os.path.join(args.output_path,"baseline.csv"),
                base_xy, #fmt='%10.5f',
                delimiter=',',
                #header='x,y'
                )
        base_rn=baseline_data["report_name"][pareto_base_mask][srt_base_idx]
        with open(os.path.join(args.output_path,'baseline_rpt.txt'), 'w') as f:
            f.write("###### BASELINE REPORT NAMES #####\n")
            for rn,rsc_thr in zip(base_rn, base_xy):
                f.write("report name:"+rn+"\n")
                f.write("xy:"+str(rsc_thr)+"\n")
        #generate separate plots for EEF fraction
        #NOTE GENERATING SINGLE PLOTS
        #eef_exit_fraction_l = [0.25,0.34, 0.37,0.5]
        eef_exit_fraction_l = []
        # FIXME only for 2 stage networks
        eef_exit_fraction_l.append(1.0-float(args.profiled_probability))

        subop_fraction = [-0.05,0.05] #lines representing suboptimal EEF %
        for eef_frac in eef_exit_fraction_l:
            if ee_flag:
                combined_data = combine_network_sections(args, ee1_data, eef_data,
                    platform_dict, baseline_data, eef_exit_fraction=eef_frac)
                #gen pareto front for combined data
                _, pareto_comb_mask,srt_comb_idx = pareto_front(combined_data, "resource_max")
            #print graph of combined vs baseline vs ee1
            rsc_str = "resource_max"
            fig = plt.figure()
            ax = plt.subplot(111)

            #plot the pareto front with a line
            #ax.plot(ee1_data['resource_max'][pareto_ee1_mask][srt_ee1_idx],
            #        ee1_data['throughput'][pareto_ee1_mask][srt_ee1_idx],
            #        c="blue",label=f'EE1')
            #for rsc,mrkr in rsc_markers.items():
            #    mask = pareto_ee1_mask & (ee1_data["limiting_resource"]==rsc)
            #    ax.scatter(ee1_data[rsc_str][mask], ee1_data["throughput"][mask],
            #            c="blue",marker=mrkr)#,label=f'{rsc}s')
            #plot eef just for bants
            #ax.plot(eef_data['resource_max'][pareto_eef_mask][srt_eef_idx],
            #        eef_data['throughput'][pareto_eef_mask][srt_eef_idx],
            #        c="#78ff9c",label=f'EEF')

            base_col='red'
            #plot the pareto front with a line
            ax.plot(base_x,base_y,c=base_col,label=f'Baseline')
            #plot the points and limiting resource for baseline
            for rsc,mrkr in rsc_markers.items():
                mask = pareto_base_mask & (baseline_data["limiting_resource"]==rsc)
                #generating csv for each resource
                rsc_x=baseline_data[rsc_str][mask]
                rsc_y=baseline_data["throughput"][mask]
                rsc_xy=np.vstack((rsc_x,rsc_y)).T
                np.savetxt(os.path.join(args.output_path,
                            'baseline_{}.csv'.format(rsc)),
                        rsc_xy,delimiter=',')
                ax.scatter(rsc_x, rsc_y, c=base_col,marker=mrkr)#,label=f'{rsc}s')


            if ee_flag:
                #combined network data
                comb_x=combined_data['resource_max'][pareto_comb_mask][srt_comb_idx]
                comb_y=combined_data['throughput'][pareto_comb_mask][srt_comb_idx]
                comb_xy = np.vstack((comb_x,comb_y)).T

                comb_rn=combined_data["report_name"][pareto_comb_mask][srt_comb_idx]

                #with open(os.path.join(args.output_path,'baseline_rpt.txt'), 'w') as f:
                #    f.write("###### BASELINE REPORT NAMES #####\n")
                #    for rn,rsc_thr in zip(base_rn, base_xy):
                #        f.write("report name:"+rn+"\n")
                #        f.write("xy:"+str(rsc_thr)+"\n")

                #comb_rn = comb_rn.T
                with open(os.path.join(args.output_path,'combined_rpt_eefrac{}.txt'.format(int((1-eef_frac)*100))), 'w') as f:
                    f.write("###### COMBINED REPORT NAMES #####\n")
                    for rn,rsc_thr in zip(comb_rn, comb_xy):
                        f.write(f"report name:{rn} \n")
                        f.write(f"xy:{rsc_thr} \n")

                comb_ee1=combined_data["ee1_throughput"][pareto_comb_mask][srt_comb_idx]
                comb_eef=combined_data["eef_throughput"][pareto_comb_mask][srt_comb_idx]
                comb_eefsc=combined_data["eef_throughput_scaled"][pareto_comb_mask][srt_comb_idx]
                comb_all = np.vstack((comb_x,comb_y, comb_ee1,comb_eef,comb_eefsc)).T

                #NOTE can't put strings in numpy array for savetxt
                #comb_all_proto2 = comb_all_proto.astype(str)
                #print("proto shape", comb_all_proto2.shape)
                #comb_all = np.concatenate( (comb_all_proto2, comb_rn), axis=1)
                #print("comb all", comb_all.shape)

                #save to csv for latex pgfplots
                np.savetxt(os.path.join(args.output_path,
                            'Opt_{}_curve.csv'.format(str(int(100*(1-eef_frac) ))) ),
                        comb_xy,delimiter=',')

                np.savetxt(os.path.join(args.output_path,
                            'INVESTIGATION_Opt_{}_curve.csv'.format(str(int(100*(1-eef_frac) ))) ),
                        comb_all,delimiter=',')

                #plot the pareto front with a line
                comb_col = "#9a57FF"
                ax.plot(comb_x,comb_y,c=comb_col,label='Opt ({:.1f}%)'.format(100*(1-eef_frac) ))
                #plot the points and limiting resource for combined exits
                for rsc,mrkr in rsc_markers.items():
                    mask = pareto_comb_mask & (combined_data["limiting_resource"]==rsc)
                    #generating csv for each resource
                    rsc_x=combined_data[rsc_str][mask]
                    rsc_y=combined_data["throughput"][mask]
                    rsc_xy=np.vstack((rsc_x,rsc_y)).T
                    np.savetxt(os.path.join(args.output_path,
                                'Opt_{}_{}.csv'.format(str(int(100*(1-eef_frac) )),rsc )),
                            rsc_xy,delimiter=',')
                    #matplotlibbing
                    ax.scatter(rsc_x, rsc_y,c=comb_col,marker=mrkr)#,label=f'{rsc}s')

                for subop_frac,ls in zip(subop_fraction,['dashed','dotted']):
                    scaling = eef_frac/(eef_frac+subop_frac)
                    #sort out the scaled throughput
                    bounded_thru = np.minimum(combined_data['ee1_throughput'][pareto_comb_mask][srt_comb_idx],
                        combined_data['eef_throughput_scaled'][pareto_comb_mask][srt_comb_idx]*scaling)
                    bound_xy = np.vstack((comb_x,bounded_thru)).T
                    #save to csv for latex pgfplots
                    np.savetxt(os.path.join(args.output_path,
                                'Opt_{}_bound_{}.csv'.format(
                                    str(int(100*(1-eef_frac))),
                                    str(int(100*((1-(eef_frac+subop_frac) ) )))) ),
                            bound_xy,delimiter=',')
                    #plot the pareto front with a line
                    ax.plot(comb_x,bounded_thru, c=comb_col, linestyle=ls,
                            label='{:.1f}%'.format(100*((1-(eef_frac+subop_frac)) )) ) #change the names
                    #don't worry about the limiting resource fo the suboptimal plot

            #fix the title of the plot
            ax.set( xlabel='Fraction of Maximum Limiting Resource', #.format(rsc_str),
                    ylabel='Throughput (samples/s)',
                    )
            ax.grid()
            ax.set_xlim(right=1.0)
            #ax.set_ylim(top=85000)
            #get figure position
            box = ax.get_position()
            #adjust figure width to fit legend
            ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])
            # Put a legend to the right of the current axis
            handles, labels = ax.get_legend_handles_labels()
            #add title type thing for the resource limiters
            l_w = mpat.Patch(color='white')
            handles.append(l_w)
            handles.append(l_w)
            labels.append('Limiting')
            labels.append('Resource:')
            #add resource markers to legend
            for rsc,mrkr in rsc_markers.items():
                new_hd = mlines.Line2D([0], [0], marker=mrkr, color='black', label=rsc)
                handles.append(new_hd)
                labels.append(f'{rsc}s')
            ax.legend(handles,labels, loc='center left', bbox_to_anchor=(1.01, 0.5))
            #save plot
            fig.savefig(os.path.join(args.output_path,"plot_{}_{}_{}eepr.pdf".format(
                args.save_name, rsc_str, str(int(100*(1-eef_frac) )))))
            print("Saved Combined {} Graph. EE Frac: {}".format(rsc_str,str(100*(1-eef_frac) )))

###########################################################
#################        main         #####################
###########################################################

def main():
    parser = argparse.ArgumentParser(description="script for running experiments")
    parser.add_argument('--expr',
            choices=['opt_brn','opt', 'gen_graph'],
            help='for experiments')

    parser.add_argument('--save_name', type=str, help='save name for json file or graph')

    parser.add_argument('-o','--output_path', metavar='PATH', required=True,
            help='Path to output directory')

    # NOTE added for cli control
    parser.add_argument('-mp', '--model_path', metavar='PATH',
            help='location of onnx model')
    parser.add_argument('-pp','--platform_path', metavar='PATH',
            help='location of platform description path')
    parser.add_argument('--optimiser_path', metavar='PATH',
            help='location of optimiser configuration path')
    parser.add_argument('-bs','--batch_size', metavar='N',type=int, default=1, required=False,
                    help='batch size for hardware optimisation')

    ### NOTE inputs for graph generation
    parser.add_argument('-i', '--input_path', metavar='PATH',
            help='folder location for report JSONs')
    parser.add_argument('-bi', '--baseline_input_path', metavar='PATH',
            help='folder location for baseline report JSONs')
    parser.add_argument('-pr','--profiled_probability', type=float, default=0.5, required=False,
            help='Probability of samples that will early-exit. E.g. 0.75 means 75% of values will early-exit')

    args = parser.parse_args()

    #model path
    filepath = args.model_path

    #optimiser path
    optpath = args.optimiser_path

    #platform path
    platpath = args.platform_path

    if args.expr == 'opt_brn':
        if filepath is None or optpath is None or platpath is None:
            raise ValueError("Missing model path, optimiser config path or platform resource path")
        print(filepath)
        print(platpath)
        optim_expr(args, filepath, True, optpath, platpath)
    elif args.expr == 'opt':
        optim_expr(args, filepath, False, optpath, platpath)
    elif args.expr == 'gen_graph':
        gen_graph(args)
    else:
        raise NameError("Experiment doesn\'t exist")

if __name__ == "__main__":
    main()
