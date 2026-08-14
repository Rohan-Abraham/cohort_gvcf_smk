# icgc_smk

Snakemake pipeline for ICGC-ARGO CRAM inputs.

## What it does

- Takes CRAM files directly as input.
- Runs GATK HaplotypeCaller per chromosome.
- Merges split GVCFs into one per-sample GVCF.
- Adds `--annotation-group AS_StandardAnnotation` for allele-specific annotations.

## Layout

- `snakefiles/common.snake` — sample-sheet helpers.
- `snakefiles/variant.snake` — CRAM-to-GVCF rules.
- `snakefiles/default.snake` — default targets.
- `configs/config.yaml` — reference, paths, containers, resources.

## Sample sheet

`configs/samples.csv` is a single-column CSV of CRAM paths.
The sample name is derived from the CRAM basename.

## Run

```bash
snakemake --profile configs/smk_profiles/cookie_numbers/ all_targets --cores 24
```
