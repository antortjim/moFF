#!/usr/bin/env python
import numpy as np
import pandas as pd
import argparse
import logging
import os
import multiprocessing
import multithreadlogs

import moff
import moff_mbr



log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def save_moff_result (list_df, result, folder_output, name  ):
    xx=[]
    for df_index in range(0,len(list_df)):
        xx.append( result[df_index].get())
        
    final_res = pd.concat(xx)
    print os.path.join(folder_output,os.path.basename(name).split('.')[0]  + "_moff_result.txt")
    final_res.to_csv( os.path.join(folder_output,os.path.basename(name).split('.')[0]  + "_moff_result.txt"),sep="\t",index=False )    
        

    return (1)





if __name__ == '__main__':

    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description='moFF match between run and apex module input parameter')

    parser.add_argument('--inputF', dest='loc_in', action='store',
                        help='specify the folder of the input MS2 peptide list files ', required=False)

    parser.add_argument('--inputtsv', dest='tsv_list', action='store', nargs='*' ,
                        help='specify the mzid file as a list ', required=False)


    parser.add_argument('--inputraw', dest='raw_list', action='store',  nargs='*' ,
                        help='specify the raw file as a list ', required=False)

    parser.add_argument('--sample', dest='sample', action='store',
                        help='specify witch replicated to use for mbr reg_exp are valid ', required=False)

    parser.add_argument('--ext', dest='ext', action='store', default='txt',
                        help='specify the file extentention of the input like ', required=False)

    parser.add_argument('--log_file_name', dest='log_label', action='store', default='moFF',
                        help='a label name to use for the log file', required=False)

    parser.add_argument('--filt_width', dest='w_filt', action='store', default=2,
                        help='width value of the filter  k * mean(Dist_Malahobis)', required=False)

    parser.add_argument('--out_filt', dest='out_flag', action='store', default=1,
                        help='filter outlier in each rt time allignment', required=False)

    parser.add_argument('--weight_comb', dest='w_comb', action='store', default=0,
                        help='weights for model combination combination : 0 for no weight  1 weighted devised by trein err of the model.',
                        required=False)

    # parser.add_argument('--input', dest='name', action='store',help='specify input list of MS2 peptides ', required=True)

    parser.add_argument('--tol', dest='toll', action='store', type=float, help='specify the tollerance  parameter in ppm',
                        required=True)

    parser.add_argument('--rt_w', dest='rt_window', action='store', type=float, default=3,
                        help='specify rt window for xic (minute). Default value is 3 min', required=False)

    parser.add_argument('--rt_p', dest='rt_p_window', action='store', type=float, default=0.1,
                        help='specify the time windows for the peak ( minute). Default value is 0.1 ', required=False)

    parser.add_argument('--rt_p_match', dest='rt_p_window_match', action='store', type=float, default=0.4,
                        help='specify the time windows for the matched peptide peak ( minute). Default value is 0.4 ',
                        required=False)

    parser.add_argument('--raw_repo', dest='raw', action='store', help='specify the raw file repository ', required=False)

    parser.add_argument('--output_folder', dest='loc_out', action='store', default='', help='specify the folder output',
                        required=False)

    parser.add_argument('--rt_feat_file', dest='rt_feat_file', action='store',
                        help='specify the file that contains the features to use in the match-between-run RT prediction ',
                        required=False)

    args = parser.parse_args()

    ## init globa logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    log.addHandler(ch)

    if (args.tsv_list is None) and  (args.loc_in is None) and  (args.raw_list is None) and (args.raw is None) :
        exit('you must specify the input and raw files ')
    if (args.tsv_list is not None) and  (args.loc_in is not None) and  (args.raw_list is not None) and (args.raw is not None) :
         exit('you must specify the input and raw files or unsing: --inputtsv and --rawlist or --inputF and --rawrepo ')
    else:
        if ((args.tsv_list is None ) and (args.raw_list is not None) ) or ((args.tsv_list is not  None ) and (args.raw_list is  None) ):
            exit('Missing information: using --inputtsv you must specify the raw file with --inputraw ')
        if ((args.loc_in is None ) and (args.raw is not None) ) or ((args.loc_in is not  None ) and (args.raw is  None) ) :
            exit('Missing information: using --inputF you must specify the raw file with --raw_repo ')


    log.critical('Matching between run module (mbr)')


    # fixed variable number of split and also number of CPU presence in the macine
    # change this variable  with repset to the machine setting of the user
    num_CPU=12

    print __name__
    res_state,mbr_list_loc = moff_mbr.run_mbr(args)
    if res_state == -1:
        exit('An error is occurred during the writing of the mbr file')
    if args.tsv_list is not None:
        # input list of raw and tsv file
        if len(args.tsv_list) != len(args.raw_list) :
            exit('Error:  number of the input files is different from the number of raw files' )
        # in case list of file as input , mbr_output is written in local folder
        folder = os.path.join('mbr_output')
    else:
        folder = os.path.join(args.loc_in, 'mbr_output')

    log.critical('Apex module ')
    c=0
    for file_name in mbr_list_loc:
        tol = args.toll
        h_rt_w = args.rt_window
        s_w = args.rt_p_window
        s_w_match = args.rt_p_window_match
        if args.tsv_list is not None:
        ## list of the raw file and their path
            raw_list = args.raw_list[c]
        else:
            raw_list = None
        loc_raw = args.raw
        loc_output = args.loc_out


        ## add multi thredign option
        df = pd.read_csv(file_name,sep="\t")
        ## for debug only
        df= df.ix[0:20,:]

        ll= np.array_split(df, num_CPU)
        #print 'Original size',df.shape
        ## split the file

        ## logging low elevr for debugging
        #print log.name
        #name = os.path.basename(file_name).split('.')[0]
        #multithreadlogs.LoggingInit_apex(os.path.join(loc_output, name + '__moff.log'))

        myPool = multiprocessing.Pool(num_CPU)

        result = {}
        offset = 0
        for df_index in range(0,len(ll)):

            result[df_index] = myPool.apply_async(moff.test01_mth,args = (ll[df_index],raw_list, tol, h_rt_w, s_w, s_w_match, loc_raw, loc_output, offset,log ))
            #result[df_index] = myPool.apply_async(moff.test_mth_base, args=(ll[df_index], offset))
            #print df_index,offset
            offset += len(ll[df_index])


        myPool.close()
        myPool.join()
        save_moff_result (ll, result, loc_output, file_name  )


        #multithreadlogs.WriteLog_critical("test")


        c+=1

        exit('--- Debug --')
        '''
        moff.run_apex(file_name,raw_list ,tol, h_rt_w, s_w, s_w_match, loc_raw, loc_output,log)
        '''
    
