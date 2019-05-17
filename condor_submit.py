#!/usr/bin/env python3

import os, sys
import getpass

'''Usage: ./condor_submit.py <LHE/gridpack filename> year [njobs]
'''

def prep_submit(infile, workpath, year):
    '''A series of actions to prepare submit dir'''

    lhe_dir = '_'.join(infile.split('_')[0:3])

    stage_out_piece = (
        f'remoteDIR="/store/group/lpcmetx/iDM/LHE/2018/signal"\n'
        f'for f in `ls ./{lhe_dir}/*.lhe`; do\n'
        f'    cmd="xrdcp -vf file:///$PWD/$f root://cmseos.fnal.gov/$remoteDIR/$f"\n'
        f'    echo $cmd && eval $cmd\n'
        f'done\n'
    )

    try:
        os.makedirs(workpath + '/submit/gridpacks')
        os.system(f'cp gridpacks/Production/{infile} {workpath}/submit/gridpacks')
        os.system(f'cp runOffGridpack{year}Pileup.sh {workpath}/submit')
        with open(f'{workpath}/submit/runOffGridpack{year}Pileup.sh', 'a') as f:
            f.write(stage_out_piece)
    except:
        print(f"{infile} probably doesn't exist!")
        cmd = ['ls -lrth '+s for s in ('.', 'gridpacks')]
        for c in cmd:
            print(cmd)
            os.system(cmd)
        raise

    #os.system('cp /tmp/x509up_u%d %s/x509up' % (uid, workpath))
    print("Tarring up submit...")
    os.chdir(workpath)
    os.system('tar -chzf submit.tgz submit')
    os.chdir('..')

def prep_exec(infile, workpath, year):
    '''Given the workpath, write a exec.sh in it, to be used by condor'''
    
    with open(workpath + '/exec.sh', 'w') as f:

        exec_sh_string = (
            f'#!/bin/bash\n\n'
            f'export HOME=${{PWD}}\n\n'
            f'tar xvaf submit.tgz\n'
            f'cd submit\n'
            f'sh runOffGridpack{year}Pileup.sh {infile}\n'
            f'cd ${{HOME}}\n'
            f'rm -r submit/\n\n'
            f'exit 0\n'
        )
        
        f.write(exec_sh_string)


def prep_condor(process, workpath, logpath, user, njobs=1):
    '''build the condor file, return the abs path'''

    condor_string = (
        f'universe = vanilla\n'
        f'executable = {workpath}/exec.sh\n'
        f'should_transfer_files = YES\n'
        f'when_to_transfer_output = ON_EXIT\n'
        f'transfer_input_files = {workpath}/submit.tgz\n'
        f'transfer_output_files = ""\n'
        f'input = /dev/null\n'
        f'output = {logpath}/$(Cluster)_$(Process).out\n'
        f'error = {logpath}/$(Cluster)_$(Process).err\n'
        f'log = {logpath}/$(Cluster)_$(Process).log\n'
        f'rank = Mips\n'
        f'request_memory = 8000\n'
        f'arguments = $(Process)\n'
        f'#on_exit_hold = (ExitBySignal == True) || (ExitCode != 0)\n'
        f'notify_user = {user}@cornell.edu\n'
        f'+AccountingGroup = "analysis.{user}"\n'
        f'+AcctGroup = "analysis"\n'
        f'+ProjectName = "DarkMatterSimulation"\n'
        f'queue {njobs}\n'
    )

    condor_filename = f'condor_{process}.jdl'

    with open(logpath + '/' + condor_filename, 'w') as jdl_file:
        jdl_file.write(condor_string)

    return os.path.join(logpath, condor_filename)


if __name__ == "__main__":

    inf = sys.argv[1]
    process = inf.split('/')[-1].split('.')[0]
    print(process)

    if len(sys.argv) < 3:
        print("ERROR! Need at least 2 arguments!")
        print("Usage: ./submit.py <LHE/gridpack filename> year [njobs]")
        sys.exit()
    elif sys.argv[2] != '2017' and sys.argv[2] != '2018':
        print("ERROR! Year (2017/18) is a mandatory argument!")
        print("Usage: ./submit.py <LHE/gridpack filename> year [njobs]")
        sys.exit()
        
    year = sys.argv[2]

    njobs = 1 if len(sys.argv) < 4 else sys.argv[3]

    logpath = os.getcwd() + '/logs'
    if not os.path.isdir(logpath):
        os.mkdir(logpath)
    submitpath = os.getcwd() + '/submissions'
    if not os.path.isdir(submitpath):
        os.mkdir(submitpath)
    workpath = submitpath + '/submit_' + Process
    if os.path.isdir(workpath):
        os.system(f'rm -rf {workpath}')
    os.mkdir(workpath)
    user = getpass.getuser()

    prep_submit(infile=inf, workpath=workpath, year=year)
    prep_exec(infile=inf, workpath=workpath, year=year)
    condor_job = prep_condor(process=process, workpath=workpath, logpath=logpath, user=user, njobs=njobs)
    os.system(f'condor_submit {condor_job}')
