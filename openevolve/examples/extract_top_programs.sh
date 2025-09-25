#!/bin/bash

# Define arrays for models and environments
models=("gemini" "dpsk" "dpskchat" "geminipro" "geminiflash" "qwen_noelite" "qwen_nograd")
environments=("ant" "gap" "hopper" "swimmer")

# Nested loop to execute extract_top_programs.py for each model and environment
for model in "${models[@]}"; do
    for env in "${environments[@]}"; do
        python ./openevolve/examples/extract_top_programs.py -i 100 -n 6 -M "$model" -e "$env"
    done
done