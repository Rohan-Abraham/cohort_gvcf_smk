#!/bin/bash
#SBATCH --cpus-per-task=1
#SBATCH --output=log/sbatch/smk-%j.out
#SBATCH --time=50-00:00:00
#SBATCH --mail-user=rabraham@bcgsc.ca
#SBATCH --qos=general
#SBATCH --exclude=s[101-114]

cd /home/rabraham/icgc_smk && \
venv/bin/snakemake --profile configs/smk_profiles/cookie_numbers/ all_targets --cores 24
