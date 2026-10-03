# cohort_gvcf_smk

Snakemake workflow for producing cohort-compatible, per-sample gVCFs. The
default path calls variants from an existing compatible CRAM or BAM. Optional
alignment modes support projects whose source alignments are not compatible
with the cohort reference and alignment method.

Each sample produces one indexed gVCF. This workflow does not combine samples
or perform joint genotyping.

## Processing modes

| `input_mode` | Input | Processing |
| --- | --- | --- |
| `call_only` | Compatible CRAM or BAM | HaplotypeCaller and gVCF merge only (default) |
| `realign_bam` | BAM aligned to another reference or with another aligner | Recover paired reads, BWA-MEM alignment, duplicate marking, tag restoration, BQSR, and variant calling |
| `align_fastq` | Paired FASTQs | BWA-MEM alignment, duplicate marking, tag restoration, BQSR, and variant calling |

The alignment path uses BWA-MEM 0.7.17-r1188 against
`GRCh38_full_analysis_set_plus_decoy_hla.fa`. Variant calling uses GATK 4.2.5.0
HaplotypeCaller in DRAGEN mode with `AS_StandardAnnotation`, matching the
ICGC-ARGO gVCF calling configuration.

## Compatibility contract

The BWA and BAM-realignment modes deliberately reuse the analytically relevant
HostSeq processing contract after alignment:

- the same GRCh38 full analysis set plus decoy/HLA reference and dbSNP142
  known-sites resource;
- byte-identical interval contents;
- GATK 4.2.5.0 MarkDuplicates, `SetNmMdAndUqTags`, BQSR, and HaplotypeCaller;
- the HostSeq HaplotypeCaller filtering, pair-HMM, DRAGEN-mode, and gVCF
  options; and
- bcftools 1.14 concatenation and tabix indexing.

`AS_StandardAnnotation` is intentionally added for ICGC-ARGO and future cohort
compatibility. HostSeq's diagnostic HaplotypeCaller BAM is not generated because
it does not affect the gVCF. JVM sizing, thread counts, disk intermediates, and
compression mechanics may differ without changing this analytical contract.

For aligned inputs, retained QC mirrors HostSeq: duplicate metrics, samtools
stats, flagstat, idxstat, coverage, and sambamba-bamStats. The alignment header
is also retained. Alignment BAMs remain temporary.

Alignment BAMs, their indexes, recovered FASTQs, BQSR tables, and per-interval
gVCFs are temporary Snakemake outputs. The final gVCF and index, alignment QC,
duplicate metrics, rule logs, and benchmarks are retained. The input BAM is
never modified.

## Setup

```bash
cd cohort_gvcf_smk
python -m venv venv
source venv/bin/activate
pip install -r REQUIREMENTS.txt
```

The workflow runs tools through the containers configured in the selected YAML
file. It therefore requires Singularity and access to the referenced project
filesystems. Alignment modes also require the internal
`sambamba-bamStats_v0.4.0` executable configured under `tools` because no
container is available for that HostSeq QC program.

## Sample sheets

`call_only` accepts the historical one-column ICGC-ARGO sheet:

```csv
cram_path
/path/to/sample.cram
```

For new call-only datasets, use explicit sample names and indexes:

```csv
sample,alignment,index
SAMPLE_1,/path/to/SAMPLE_1.cram,/path/to/SAMPLE_1.cram.crai
```

`realign_bam` requires:

```csv
sample,bam,bai,read_group_id,library,platform_unit
SAMPLE_1,/path/to/SAMPLE_1.bam,/path/to/SAMPLE_1.bam.bai,SAMPLE_1.RG1,SAMPLE_1.LIB1,SAMPLE_1.PU1
```

`align_fastq` requires:

```csv
sample,r1,r2,read_group_id,library,platform_unit
SAMPLE_1,/path/to/SAMPLE_1.R1.fastq.gz,/path/to/SAMPLE_1.R2.fastq.gz,SAMPLE_1.RG1,SAMPLE_1.LIB1,SAMPLE_1.PU1
```

Sample names and read-group fields may contain letters, numbers, periods,
underscores, and hyphens.

Operational cohort manifests are local artifacts and are intentionally ignored
by Git. Create `configs/samples.csv` locally before using the default
`configs/config.yaml`, or point `samples` in a copied configuration file to a
different local manifest. The tracked benchmark and MoHCCN sample sheets are
small fixtures and examples.

## Run

Always inspect a dry run before submitting work:

```bash
venv/bin/python -m snakemake \
  --configfile configs/config.yaml \
  --dry-run --printshellcmds all_targets --cores 1
```

Submit the default call-only workflow:

```bash
sbatch sbatch.sh configs/config.yaml
```

Run the BWA-MEM benchmark-sample workflow for HG001 and SYNDIP:

```bash
venv/bin/python -m snakemake \
  --configfile configs/config.benchmark_bwa.yaml \
  --dry-run --printshellcmds all_targets --cores 1
sbatch sbatch.sh configs/config.benchmark_bwa.yaml
```

On `hostseq01`, where the Slurm client may not be available, run the same
profile locally in a persistent shell. Set the core and memory ceilings for the
host rather than copying these values to a smaller machine:

```bash
venv/bin/python -m snakemake \
  --configfile configs/config.benchmark_bwa.yaml \
  --use-singularity --singularity-args '-B /projects' \
  --cores 96 --resources mem_mb=1000000 time_limit=20000 \
  --rerun-incomplete --keep-going --printshellcmds --latency-wait 60 \
  all_targets
```

This profile writes two independent indexed outputs:

```text
/projects/HostSeq/HostSeq_ext/data/outputs/benchmark_samples/bwa-mem-0.7.17-r1188/HG001/gatk-v4.2.5.0/HG001.g.vcf.gz
/projects/HostSeq/HostSeq_ext/data/outputs/benchmark_samples/bwa-mem-0.7.17-r1188/SYNDIP/gatk-v4.2.5.0/SYNDIP.g.vcf.gz
```

For MoHCCN, copy `configs/config.mohccn.example.yaml` and
`configs/samples.mohccn.example.csv`, replace the placeholder input paths and
sample metadata, and retain `input_mode: realign_bam`. The BAM-to-FASTQ stage
discards secondary, supplementary, unpaired, and singleton reads from the BWA
input; review the retained alignment QC before using the gVCF downstream.

## Configuration

- `configs/config.yaml`: default ICGC-ARGO call-only profile; preserves the
  existing output layout.
- `configs/config.benchmark_bwa.yaml`: HG001 and SYNDIP BWA-MEM benchmark run.
- `configs/config.mohccn.example.yaml`: template for BAM realignment projects.
- `configs/smk_profiles/cookie_numbers/`: Slurm submission profile.
- `snakefiles/align.snake`: optional read recovery, alignment, duplicate
  marking, BQSR, and alignment QC.
- `snakefiles/variant.snake`: interval-sharded HaplotypeCaller and final gVCF
  concatenation.
