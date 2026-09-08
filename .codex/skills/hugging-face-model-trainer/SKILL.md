---
name: hugging-face-model-trainer
description: Use when the user explicitly wants TRL training, fine-tuning, or conversion on Hugging Face Jobs infrastructure. Submit a paid job only when the user asks to start or submit it; planning, cost estimation, examples, and code-only requests remain non-launching. Do not invoke for training on local machines, SSH servers, or unrelated cloud providers.
license: Complete terms in LICENSE.txt
---

# TRL Training on Hugging Face Jobs

## Overview

Train language models using TRL (Transformer Reinforcement Learning) on fully managed Hugging Face infrastructure. No local GPU setup is required. Configure the authorized durable output destination before launching; the included examples demonstrate Hub persistence.

**TRL provides multiple training methods:**
- **SFT** (Supervised Fine-Tuning) - Standard instruction tuning
- **DPO** (Direct Preference Optimization) - Alignment from preference data
- **GRPO** (Group Relative Policy Optimization) - Online RL training
- **Reward Modeling** - Train reward models for RLHF

**For detailed TRL method documentation:**
```python
hf_doc_search("your query", product="trl")
hf_doc_fetch("https://huggingface.co/docs/trl/sft_trainer")  # SFT
hf_doc_fetch("https://huggingface.co/docs/trl/dpo_trainer")  # DPO
# etc.
```

**See also:** `references/training_methods.md` for method overviews and selection guidance

## When to Use This Skill

Use these capabilities only for work assigned to Hugging Face Jobs. They do not redirect local, SSH, or another provider's workloads to HF. Within that scope, users may want to:
- Fine-tune language models on cloud GPUs without local infrastructure
- Train with TRL methods (SFT, DPO, GRPO, etc.)
- Run training jobs on Hugging Face Jobs infrastructure
- Convert trained models to GGUF for local deployment (Ollama, LM Studio, llama.cpp)
- Ensure trained models are permanently saved to the Hub
- Use modern workflows with optimized defaults

### When to Use Unsloth

Consider **Unsloth** (`references/unsloth.md`) when current model support and measured memory or throughput benefit fit the requested run. Preserve the selected trainer and scientific contract unless changing them is within scope. Candidate benefits to verify include:
- **Limited GPU memory** - Unsloth uses ~60% less VRAM
- **Speed matters** - Unsloth is ~2x faster
- Training **large models (>13B)** - memory efficiency is critical
- Training **Vision-Language Models (VLMs)** - Unsloth has `FastVisionModel` support

See `references/unsloth.md` for complete Unsloth documentation and `scripts/unsloth_sft_example.py` for a production-ready training script.

## Key Directives

When assisting with training jobs:

1. **Use an appropriate interface for an authorized launch** - Prefer the callable HF Jobs MCP tool for an authorized launch; use the existing HF CLI or SDK when MCP is unavailable or the established workflow requires it. MCP script input is inline code or a reachable URL; the CLI can upload a local script. Retain a local script when requested, needed for reproducibility, or required by the existing launch contract. For planning, cost estimation, examples, or code-only requests, prepare the requested material without submitting a job.

2. **Choose monitoring proportionally** - Include Trackio when the user wants a dashboard or the established workflow uses it. Platform logs are sufficient for a minimal smoke job when adding Trackio would be unnecessary overhead.

3. **Provide job details after submission** - After submitting, provide job ID, monitoring URL, estimated time, and note that the user can request status checks later.

4. **Use example scripts as templates** - Reference `scripts/train_sft_example.py`, `scripts/train_dpo_example.py`, etc. as starting points.

## Local Script Dependencies

To run scripts locally (like `estimate_cost.py`), install dependencies:
```bash
pip install -r requirements.txt
```

## Prerequisites Checklist

Before starting any training job, verify:

### ✅ **Account & Authentication**
- Hugging Face Account with [Pro](https://hf.co/pro), [Team](https://hf.co/enterprise), or [Enterprise](https://hf.co/enterprise) plan (Jobs require paid plan)
- Authenticated login: Check with `hf_whoami()`
- Configure an authorized durable destination for required training outputs before launch. If that destination is the Hub, require write access and pass `secrets={"HF_TOKEN": "$HF_TOKEN"}` in the job config. Public downloads do not require a token.

### ✅ **Dataset Requirements**
- Dataset must exist on Hub or be loadable via `datasets.load_dataset()`
- Format must match training method (SFT: "messages"/text/prompt-completion; DPO: chosen/rejected; GRPO: prompt-only)
- **ALWAYS validate unknown datasets** before GPU training to prevent format failures (see Dataset Validation section below)
- Size appropriate for hardware (Demo: 50-100 examples on t4-small; Production: 1K-10K+ on a10g-large/a100-large)

### ⚠️ **Critical Settings**
- **Timeout must exceed expected training time** - Default 30min is TOO SHORT for most training. Minimum recommended: 1-2 hours. Job fails and loses all progress if timeout is exceeded.
- **Required outputs must persist** - Use the established authorized destination. For Hub persistence, configure `push_to_hub=True`, `hub_model_id="username/model-name"`, and job secrets. Retained platform logs may suffice for a disposable smoke check.

## Asynchronous Job Guidelines

**⚠️ IMPORTANT: Training jobs run asynchronously and can take hours**

### Action Required

**When the user explicitly requests a launch:**
1. **Create the training script**, adding Trackio when monitoring requirements justify it (use `scripts/train_sft_example.py` as a template when applicable)
2. **Submit** with the available interface described above; retain the script when requested or required for reproducibility
3. **Report submission** with job ID, monitoring URL, and estimated time
4. **Follow the requested endpoint** - Use the monitoring guidance below for submission-only versus completion requests.

### Ground Rules
- **Jobs run in background** - Submission returns immediately; training continues independently
- **Initial logs delayed** - Can take 30-60 seconds for logs to appear
- **Monitor within scope** - Match the requested endpoint: for submission-only work, verify acceptance and return job details; for requested completion, monitoring, or artifacts, continue bounded checks or an available authorized monitoring mechanism. Avoid frequent unchanged polling.

### After Submission

**Provide to user:**
- ✅ Job ID and monitoring URL
- ✅ Expected completion time
- ✅ Trackio dashboard URL when configured
- ✅ Note that user can request status checks later

**Example Response:**
```
✅ Job submitted successfully!

Job ID: abc123xyz
Monitor: https://huggingface.co/jobs/username/abc123xyz

Expected time: ~2 hours
Estimated cost: ~$10

The job is running in the background. Ask me to check status/logs when ready!
```

## Quick Start: Three Approaches

**💡 Tip for Demos:** For quick demos on smaller GPUs (t4-small), omit `eval_dataset` and `eval_strategy` to save ~40% memory. You'll still see training loss and learning progress.

### Sequence Length Configuration

**TRL config classes use `max_length` (not `max_seq_length`)** to control tokenized sequence length:

```python
# ✅ CORRECT - If you need to set sequence length
SFTConfig(max_length=512)   # Truncate sequences to 512 tokens
DPOConfig(max_length=2048)  # Longer context (2048 tokens)

# ❌ WRONG - This parameter doesn't exist
SFTConfig(max_seq_length=512)  # TypeError!
```

**Default behavior:** `max_length=1024` (truncates from right). This works well for most training.

**When to override:**
- **Longer context**: Set higher (e.g., `max_length=2048`)
- **Memory constraints**: Set lower (e.g., `max_length=512`)
- **Vision models**: Set `max_length=None` (prevents cutting image tokens)

**Usually you don't need to set this parameter at all** - the examples below use the sensible default.

### Approach 1: UV Scripts (Recommended—Default Choice)

UV scripts use PEP 723 inline dependencies for clean, self-contained training. **This is the primary approach in Codex when Hugging Face Jobs tools are available.**

```python
hf_jobs("uv", {
    "script": """
# /// script
# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "trackio"]
# ///

from datasets import load_dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
import trackio

dataset = load_dataset("trl-lib/Capybara", split="train")

# Create train/eval split for monitoring
dataset_split = dataset.train_test_split(test_size=0.1, seed=42)

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset_split["train"],
    eval_dataset=dataset_split["test"],
    peft_config=LoraConfig(r=16, lora_alpha=32),
    args=SFTConfig(
        output_dir="my-model",
        push_to_hub=True,
        hub_model_id="username/my-model",
        num_train_epochs=3,
        eval_strategy="steps",
        eval_steps=50,
        report_to="trackio",
        project="meaningful_prject_name", # project name for the training name (trackio)
        run_name="meaningful_run_name",   # descriptive name for the specific training run (trackio)
    )
)

trainer.train()
trainer.push_to_hub()
""",
    "flavor": "a10g-large",
    "timeout": "2h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

**Benefits:** Direct MCP tool usage, clean code, dependencies declared inline (PEP 723), no file saving required, full control
**When to use:** Default choice for an explicit Hugging Face Jobs training request that needs custom logic or `hf_jobs()`

#### Working with Scripts

⚠️ **Important:** The MCP `script` parameter accepts inline code or a reachable URL; local file paths are not valid MCP input. The HF CLI can upload local scripts.

**Why local paths don't work:**
Jobs run in isolated Docker containers without access to your local filesystem. Scripts must be:
- Inline code (recommended for custom training)
- Publicly accessible URLs
- Private repo URLs (with HF_TOKEN)

**Common mistakes:**
```python
# ❌ These will all fail
hf_jobs("uv", {"script": "train.py"})
hf_jobs("uv", {"script": "./scripts/train.py"})
hf_jobs("uv", {"script": "/path/to/train.py"})
```

**Correct approaches:**
```python
# ✅ Inline code (recommended)
hf_jobs("uv", {"script": "# /// script\n# dependencies = [...]\n# ///\n\n<your code>"})

# ✅ From Hugging Face Hub
hf_jobs("uv", {"script": "https://huggingface.co/user/repo/resolve/main/train.py"})

# ✅ From GitHub
hf_jobs("uv", {"script": "https://raw.githubusercontent.com/user/repo/main/train.py"})

# ✅ From Gist
hf_jobs("uv", {"script": "https://gist.githubusercontent.com/user/id/raw/train.py"})
```

**To use local scripts:** Read the file and pass its contents to MCP, or use the HF CLI, which uploads a local script. A separate repository upload is optional and should occur only when publishing the script is in scope.

### Approach 2: TRL Maintained Scripts (Official Examples)

TRL provides battle-tested scripts for all methods. Can be run from URLs:

```python
hf_jobs("uv", {
    "script": "https://github.com/huggingface/trl/blob/main/trl/scripts/sft.py",
    "script_args": [
        "--model_name_or_path", "Qwen/Qwen2.5-0.5B",
        "--dataset_name", "trl-lib/Capybara",
        "--output_dir", "my-model",
        "--push_to_hub",
        "--hub_model_id", "username/my-model"
    ],
    "flavor": "a10g-large",
    "timeout": "2h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

**Benefits:** No code to write, maintained by TRL team, production-tested
**When to use:** Standard TRL training, quick experiments, don't need custom code
**Available:** Scripts are available from https://github.com/huggingface/trl/tree/main/examples/scripts

### Finding More UV Scripts on Hub

The `uv-scripts` organization provides ready-to-use UV scripts stored as datasets on Hugging Face Hub:

```python
# Discover available UV script collections
dataset_search({"author": "uv-scripts", "sort": "downloads", "limit": 20})

# Explore a specific collection
hub_repo_details(["uv-scripts/classification"], repo_type="dataset", include_readme=True)
```

**Popular collections:** ocr, classification, synthetic-data, vllm, dataset-creation

### Approach 3: HF Jobs CLI (Direct Terminal Commands)

When the `hf_jobs()` MCP tool is unavailable, use the `hf jobs` CLI directly.

**⚠️ CRITICAL: CLI Syntax Rules**

```bash
# ✅ CORRECT syntax - flags BEFORE script URL
hf jobs uv run --flavor a10g-large --timeout 2h --secrets HF_TOKEN "https://example.com/train.py"

# ❌ WRONG - "run uv" instead of "uv run"
hf jobs run uv "https://example.com/train.py" --flavor a10g-large

# ❌ WRONG - flags AFTER script URL (will be ignored!)
hf jobs uv run "https://example.com/train.py" --flavor a10g-large

# ❌ WRONG - "--secret" instead of "--secrets" (plural)
hf jobs uv run --secret HF_TOKEN "https://example.com/train.py"
```

**Key syntax rules:**
1. Command order is `hf jobs uv run` (NOT `hf jobs run uv`)
2. All flags (`--flavor`, `--timeout`, `--secrets`) must come BEFORE the script URL
3. Use `--secrets` (plural), not `--secret`
4. Script URL must be the last positional argument

**Complete CLI example:**
```bash
hf jobs uv run \
  --flavor a10g-large \
  --timeout 2h \
  --secrets HF_TOKEN \
  "https://huggingface.co/user/repo/resolve/main/train.py"
```

**Check job status via CLI:**
```bash
hf jobs ps                        # List all jobs
hf jobs logs <job-id>             # View logs
hf jobs inspect <job-id>          # Job details
hf jobs cancel <job-id>           # Cancel a job
```

### Approach 4: TRL Jobs Package (Simplified Training)

The `trl-jobs` package provides optimized defaults and one-liner training.

```bash
# Install
pip install trl-jobs

# Train with SFT (simplest possible)
trl-jobs sft \
  --model_name Qwen/Qwen2.5-0.5B \
  --dataset_name trl-lib/Capybara
```

**Benefits:** Pre-configured settings, automatic Trackio integration, automatic Hub push, one-line commands
**When to use:** The user is working directly in a terminal without Codex-integrated Hugging Face Jobs tools, or needs quick local experimentation
**Repository:** https://github.com/huggingface/trl-jobs

⚠️ **In Codex, prefer the `hf_jobs()` MCP tool (Approach 1) when it is available.**

## Hardware Selection

| Model Size | Recommended Hardware | Cost (approx/hr) | Use Case |
|------------|---------------------|------------------|----------|
| <1B params | `t4-small` | ~$0.75 | Demos, quick tests only without eval steps |
| 1-3B params | `t4-medium`, `l4x1` | ~$1.50-2.50 | Development |
| 3-7B params | `a10g-small`, `a10g-large` | ~$3.50-5.00 | Production training |
| 7-13B params | `a10g-large`, `a100-large` | ~$5-10 | Large models (use LoRA) |
| 13B+ params | `a100-large`, `a10g-largex2` | ~$10-20 | Very large (use LoRA) |

**GPU Flavors:** cpu-basic/upgrade/performance/xl, t4-small/medium, l4x1/x4, a10g-small/large/largex2/largex4, a100-large, h100/h100x8

**Guidelines:**
- Use **LoRA/PEFT** for models >7B to reduce memory
- Multi-GPU automatically handled by TRL/Accelerate
- Start with smaller hardware for testing

**See:** `references/hardware_guide.md` for detailed specifications

## Critical: Saving Results to Hub

**Ephemeral storage: persist required training outputs.**

Use the established authorized durable destination. The Hub configuration below applies when Hub storage is selected; another authorized durable store is valid. Unsaved job files are lost when the job ends. Retained platform logs may suffice for a disposable smoke check.

### Configuration When Saving to Hub

**In training script/config:**
```python
SFTConfig(
    push_to_hub=True,
    hub_model_id="username/model-name",  # MUST specify
    hub_strategy="every_save",  # Optional: push checkpoints
)
```

**In job submission:**
```python
{
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}  # Enables authentication
}
```

### Verification Checklist

When Hub is the persistence destination, before submitting:
- [ ] `push_to_hub=True` set in config
- [ ] `hub_model_id` includes username/repo-name
- [ ] `secrets` parameter includes HF_TOKEN
- [ ] User has write access to target repo

**See:** `references/hub_saving.md` for detailed troubleshooting

## Timeout Management

**⚠️ DEFAULT: 30 MINUTES—TOO SHORT FOR TRAINING**

### Setting Timeouts

```python
{
    "timeout": "2h"   # 2 hours (formats: "90m", "2h", "1.5h", or seconds as integer)
}
```

### Timeout Guidelines

| Scenario | Recommended | Notes |
|----------|-------------|-------|
| Quick demo (50-100 examples) | 10-30 min | Verify setup |
| Development training | 1-2 hours | Small datasets |
| Production (3-7B model) | 4-6 hours | Full datasets |
| Large model with LoRA | 3-6 hours | Depends on dataset |

**Always add 20-30% buffer** for model/dataset loading, checkpoint saving, Hub push operations, and network delays.

**On timeout:** The job stops and unsaved progress is lost. Resume from a compatible persisted checkpoint when available; otherwise restart within the authorized contract.

## Cost Estimation

**Offer to estimate cost when planning jobs with known parameters.** Use `scripts/estimate_cost.py`:

```bash
uv run scripts/estimate_cost.py \
  --model meta-llama/Llama-2-7b-hf \
  --dataset trl-lib/Capybara \
  --hardware a10g-large \
  --dataset-size 16000 \
  --epochs 3
```

Output includes estimated time, cost, recommended timeout (with buffer), and optimization suggestions.

**When to offer:** User planning a job, asks about cost/time, choosing hardware, job will run >1 hour or cost >$5

## Example Training Scripts

**Production-ready templates with all best practices:**

Load only the template matching the requested training method:

- **`scripts/train_sft_example.py`** - Complete SFT training with Trackio, LoRA, checkpoints
- **`scripts/train_dpo_example.py`** - DPO training for preference learning
- **`scripts/train_grpo_example.py`** - GRPO training for online RL

These scripts demonstrate proper Hub saving, Trackio integration, checkpoint management, and optimized parameters. Pass their content inline to `hf_jobs()` or use as templates for custom scripts.

## Monitoring and Tracking

**Trackio** provides real-time metrics visualization. See `references/trackio_guide.md` for complete setup guide.

**Key points:**
- Add `trackio` to dependencies
- Configure trainer with `report_to="trackio" and run_name="meaningful_name"`

### Trackio Configuration Defaults

**Use sensible defaults unless user specifies otherwise.** When generating training scripts with Trackio:

**Default Configuration:**
- **Space ID**: `{username}/trackio` (use "trackio" as default space name)
- **Run naming**: Unless otherwise specified, name the run in a way the user will recognize (e.g., descriptive of the task, model, or purpose)
- **Config**: Keep minimal - only include hyperparameters and model/dataset info
- **Project Name**: Use a Project Name to associate runs with a particular Project 

**User overrides:** If user requests specific trackio configuration (custom space, run naming, grouping, or additional config), apply their preferences instead of defaults.


This is useful for managing multiple jobs with the same configuration or keeping training scripts portable.

See `references/trackio_guide.md` for complete documentation including grouping runs for experiments.

### Check Job Status

```python
# List all jobs
hf_jobs("ps")

# Inspect specific job
hf_jobs("inspect", {"job_id": "your-job-id"})

# View logs
hf_jobs("logs", {"job_id": "your-job-id"})
```

**Monitoring:** Match the requested endpoint: for submission-only work, verify acceptance and return job details; for requested completion, monitoring, or artifacts, continue bounded checks or an available authorized monitoring mechanism. Avoid frequent unchanged polling.

## Dataset Validation

**Validate dataset format BEFORE launching GPU training to prevent the #1 cause of training failures: format mismatches.**

### Why Validate

- 50%+ of training failures are due to dataset format issues
- DPO especially strict: requires exact column names (`prompt`, `chosen`, `rejected`)
- Failed GPU jobs waste $1-10 and 30-60 minutes
- Validation on CPU costs ~$0.01 and takes <1 minute

### When to Validate

**ALWAYS validate for:**
- Unknown or custom datasets
- DPO training (CRITICAL - 90% of datasets need mapping)
- Any dataset not explicitly TRL-compatible

**Skip validation for known TRL datasets:**
- `trl-lib/ultrachat_200k`, `trl-lib/Capybara`, `HuggingFaceH4/ultrachat_200k`, etc.

### Usage

```python
hf_jobs("uv", {
    "script": "https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py",
    "script_args": ["--dataset", "username/dataset-name", "--split", "train"]
})
```

The script is fast, and will usually complete synchronously.

### Reading Results

The output shows compatibility for each training method:

- **`✓ READY`** - Dataset is compatible, use directly
- **`✗ NEEDS MAPPING`** - Compatible but needs preprocessing (mapping code provided)
- **`✗ INCOMPATIBLE`** - Cannot be used for this method

When mapping is needed, the output includes a **"MAPPING CODE"** section with copy-paste ready Python code.

### Example Workflow

```python
# 1. Inspect dataset (costs ~$0.01, <1 min on CPU)
hf_jobs("uv", {
    "script": "https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py",
    "script_args": ["--dataset", "argilla/distilabel-math-preference-dpo", "--split", "train"]
})

# 2. Check output markers:
#    ✓ READY → proceed with training
#    ✗ NEEDS MAPPING → apply mapping code below
#    ✗ INCOMPATIBLE → choose different method/dataset

# 3. If mapping needed, apply before training:
def format_for_dpo(example):
    return {
        'prompt': example['instruction'],
        'chosen': example['chosen_response'],
        'rejected': example['rejected_response'],
    }
dataset = dataset.map(format_for_dpo, remove_columns=dataset.column_names)

# 4. Launch training job with confidence
```

### Common Scenario: DPO Format Mismatch

Most DPO datasets use non-standard column names. Example:

```
Dataset has: instruction, chosen_response, rejected_response
DPO expects: prompt, chosen, rejected
```

The validator detects this and provides exact mapping code to fix it.

## Converting Models to GGUF

After training, convert models to **GGUF format** for use with llama.cpp, Ollama, LM Studio, and other local inference tools.

**What is GGUF:**
- Optimized for CPU/GPU inference with llama.cpp
- Supports quantization (4-bit, 5-bit, 8-bit) to reduce model size
- Compatible with Ollama, LM Studio, Jan, GPT4All, llama.cpp
- Typically 2-8GB for 7B models (vs 14GB unquantized)

**When to convert:**
- Running models locally with Ollama or LM Studio
- Reducing model size with quantization
- Deploying to edge devices
- Sharing models for local-first use

**See:** `references/gguf_conversion.md` for complete conversion guide, including production-ready conversion script, quantization options, hardware requirements, usage examples, and troubleshooting.

**Quick conversion:**
```python
hf_jobs("uv", {
    "script": "<see references/gguf_conversion.md for complete script>",
    "flavor": "a10g-large",
    "timeout": "45m",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"},
    "env": {
        "ADAPTER_MODEL": "username/my-finetuned-model",
        "BASE_MODEL": "Qwen/Qwen2.5-0.5B",
        "OUTPUT_REPO": "username/my-model-gguf"
    }
})
```

## Common Training Patterns

See `references/training_patterns.md` for detailed examples including:
- Quick demo (5-10 minutes)
- Production with checkpoints
- Multi-GPU training
- DPO training (preference learning)
- GRPO training (online RL)

## Common Failure Modes

### Out of Memory (OOM)

**Fix (try in order):**
1. Reduce batch size: `per_device_train_batch_size=1`, increase `gradient_accumulation_steps=8`. Effective batch size is `per_device_train_batch_size` x `gradient_accumulation_steps`. For best performance keep effective batch size close to 128. 
2. Enable: `gradient_checkpointing=True`
3. Upgrade hardware: t4-small → l4x1, a10g-small → a10g-large etc. 

### Dataset Misformatted

**Fix:**
1. Validate first with dataset inspector:
   ```bash
   uv run https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py \
     --dataset name --split train
   ```
2. Check output for compatibility markers (✓ READY, ✗ NEEDS MAPPING, ✗ INCOMPATIBLE)
3. Apply mapping code from inspector output if needed

### Job Timeout

**Fix:**
1. Check logs for actual runtime: `hf_jobs("logs", {"job_id": "..."})`
2. Increase timeout with buffer: `"timeout": "3h"` (add 30% to estimated time)
3. Or reduce training: lower `num_train_epochs`, use smaller dataset, enable `max_steps`
4. Save checkpoints: `save_strategy="steps"`, `save_steps=500`, `hub_strategy="every_save"`

**Note:** Default 30min is insufficient for real training. Minimum 1-2 hours.

### Hub Push Failures

**Fix:**
1. Add to job: `secrets={"HF_TOKEN": "$HF_TOKEN"}`
2. Add to config: `push_to_hub=True`, `hub_model_id="username/model-name"`
3. Verify auth: `mcp__huggingface__hf_whoami()`
4. Check token has write permissions and repo exists (or set `hub_private_repo=True`)

### Missing Dependencies

**Fix:**
Add to PEP 723 header:
```python
# /// script
# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "trackio", "missing-package"]
# ///
```

## Troubleshooting

**Common issues:**
- Job times out → Increase timeout, reduce epochs/dataset, use smaller model/LoRA
- Model not saved to Hub → Check push_to_hub=True, hub_model_id, secrets=HF_TOKEN
- Out of Memory (OOM) → Reduce batch size, increase gradient accumulation, enable LoRA, use larger GPU
- Dataset format error → Validate with dataset inspector (see Dataset Validation section)
- Import/module errors → Add PEP 723 header with dependencies, verify format
- Authentication errors → Check `mcp__huggingface__hf_whoami()`, token permissions, secrets parameter

**See:** `references/troubleshooting.md` for complete troubleshooting guide

## Resources

### References (In This Skill)
- `references/training_methods.md` - Overview of SFT, DPO, GRPO, KTO, PPO, Reward Modeling
- `references/training_patterns.md` - Common training patterns and examples
- `references/unsloth.md` - Unsloth for fast VLM training (~2x speed, 60% less VRAM)
- `references/gguf_conversion.md` - Complete GGUF conversion guide
- `references/trackio_guide.md` - Trackio monitoring setup
- `references/hardware_guide.md` - Hardware specs and selection
- `references/hub_saving.md` - Hub authentication troubleshooting
- `references/troubleshooting.md` - Common issues and solutions

### Scripts (In This Skill)
- `scripts/train_sft_example.py` - Production SFT template
- `scripts/train_dpo_example.py` - Production DPO template
- `scripts/train_grpo_example.py` - Production GRPO template
- `scripts/unsloth_sft_example.py` - Unsloth text LLM training template (faster, less VRAM)
- `scripts/estimate_cost.py` - Estimate time and cost (offer when appropriate)
- `scripts/convert_to_gguf.py` - Complete GGUF conversion script

### External Scripts
- [Dataset Inspector](https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py) - Validate dataset format before training (use via `uv run` or `hf_jobs`)

### External Links
- [TRL Documentation](https://huggingface.co/docs/trl)
- [TRL Jobs Training Guide](https://huggingface.co/docs/trl/en/jobs_training)
- [TRL Jobs Package](https://github.com/huggingface/trl-jobs)
- [HF Jobs Documentation](https://huggingface.co/docs/huggingface_hub/guides/jobs)
- [TRL Example Scripts](https://github.com/huggingface/trl/tree/main/examples/scripts)
- [UV Scripts Guide](https://docs.astral.sh/uv/guides/scripts/)
- [UV Scripts Organization](https://huggingface.co/uv-scripts)

## Key Takeaways

1. **Submit through the appropriate interface** - Follow Key Directives for MCP/CLI selection and reproducible scripts.
2. **Jobs are asynchronous** - Follow the requested endpoint and the monitoring guidance above.
3. **Always set timeout** - Default 30 min is insufficient; minimum 1-2 hours recommended
4. **Persist required outputs** - Use an authorized durable destination; enable Hub push when Hub storage is selected.
5. **Use proportional monitoring** - Include Trackio when a dashboard or the existing workflow calls for it; otherwise rely on job logs
6. **Offer cost estimation** - When parameters are known, use `scripts/estimate_cost.py`
7. **Use UV scripts (Approach 1)** - Default to `hf_jobs("uv", {...})` with inline scripts; use TRL-maintained scripts for standard training; avoid bash `trl-jobs` commands when Codex can call `hf_jobs()` directly
8. **Use hf_doc_fetch/hf_doc_search** for latest TRL documentation
9. **Validate dataset format** before training with dataset inspector (see Dataset Validation section)
10. **Choose appropriate hardware** for model size; use LoRA for models >7B
