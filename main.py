import sys, os
import multiprocessing as mp
import logging
import subprocess
logger = mp.log_to_stderr(logging.DEBUG)

def run_process(ind):
    output = "/scratch/souvik/" + str(ind) 
    subprocess.call(['python', 'w_indexer.py',str(xmls[ind]), output])

xmls = []
index = []
for file_name in os.listdir(sys.argv[1]):
    if ".xml" in file_name:
        xml_file = os.path.join(sys.argv[1], file_name)
        xmls.append(xml_file)


pool = mp.Pool(processes=len(xmls))
pool.map(run_process,[30])
pool.close()
