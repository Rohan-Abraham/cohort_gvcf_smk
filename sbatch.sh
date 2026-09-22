#!/bin/bash
#SBATCH --cpus-per-task=1
#SBATCH --output=log/sbatch/smk-%j.out
#SBATCH --time=50-00:00:00
#SBATCH --mail-user=rabraham@bcgsc.ca
#SBATCH --qos=prod
#SBATCH --exclude=s[101-114]

set -euo pipefail

cd /home/rabraham/cohort_gvcf_smk
venv/bin/python -m snakemake \
  --configfile "${1:-configs/config.yaml}" \
  --profile configs/smk_profiles/cookie_numbers/ \
  all_targets --cores 48
