#! /bin/bash

## This script is used to produce AOD files from a gridpack for
## 2018 data. The CMSSW version is 10_2_3 and all four lifetimes are
## produced: {1, 10, 100, 1000} mm per seed.
##
## The lifetime replacement no longer occurs at the LHE level (i.e.
## manually replacing the lifetime in LHE events) but rather at the
## Pythia hadronizer level. For private production, there are four 
## different hadronizers, one for each ctau, which gets called by this
## script as appropriate. For official central production, can have the
## calling script `sed` into the one hadronizer file to change the 
## lifetime accordingly.
##
## The number of events produced per sample is 250 instead of 1000
## because otherwise condor jobs run out of memory (due to the four
## lifetimes now).
##
## To produce 2017 AOD files use runOffGridpack2017.sh
##
## Currently MINIAOD production is commented out to save time.

## Usage: ./runOffGridpack.sh GRIDPACK.tar.xz

echo "Starting runOffGridpack2018Pileup.sh"

export BASEDIR=`pwd`
GP_f=$1
GRIDPACKDIR=${BASEDIR}/gridpacks
LHEDIR=${BASEDIR} #/mylhes
SAMPLEDIR=${BASEDIR}/samples
[ -d ${LHEDIR} ] || mkdir ${LHEDIR}

namebase=${GP_f/.tar.xz/}
nevent=1000

export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

export SCRAM_ARCH=slc6_amd64_gcc700
if ! [ -r CMSSW_10_2_3/src ] ; then
    scram p CMSSW CMSSW_10_2_3
fi
cd CMSSW_10_2_3/src
eval `scram runtime -sh`
scram b -j 4
tar xaf ${GRIDPACKDIR}/${GP_f}
sed -i 's/exit 0//g' runcmsgrid.sh
ls -lrth

RANDOMSEED=`od -vAn -N4 -tu4 < /dev/urandom`
#Sometimes the RANDOMSEED is too long for madgraph
RANDOMSEED=`echo $RANDOMSEED | rev | cut -c 3- | rev`

echo "0.) Generating LHE"
sh runcmsgrid.sh ${nevent} ${RANDOMSEED} 4
namebase=${namebase}_$RANDOMSEED
SAMPLEDIR=`echo $namebase | cut -d'_' -f 1-3`
mkdir -p ${LHEDIR}/$SAMPLEDIR
cp cmsgrid_final.lhe ${LHEDIR}/${SAMPLEDIR}/${namebase}.lhe
echo "${LHEDIR}/${namebase}.lhe" 
rm -rf *
cd ${BASEDIR}

echo "ALL Done"
