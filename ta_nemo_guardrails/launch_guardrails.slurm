#!/bin/bash

#SBATCH --job-name=guardrails
#SBATCH --output=slurm-%x-%j.out
#SBATCH --mem=100gb
#SBATCH --time=10:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus=a100

cd ~/f24-nvidia/ta_nemo_guardrails

# Set environmental variable to allow CORS
export NEMO_GUARDRAILS_SERVER_ENABLE_CORS=TRUE


# Run the nemoguardrails server with the specified config
apptainer build nemo_gr_2.sif ngr.def
