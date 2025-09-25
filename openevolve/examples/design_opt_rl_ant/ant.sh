#!/bin/bash

# Robot Structure Design Optimization Script
# This script runs the OpenEvolve optimization for robot XML designs
# Supports checkpoint resumption functionality

# Set working directory to openevolve root
cd "$(dirname "$0")/../../.."

# Check if Transform2Act is available
if [ ! -d "./Transform2Act" ]; then
    echo "Error: Transform2Act directory not found at ../../Transform2Act"
    echo "Please ensure Transform2Act is properly installed and accessible."
    exit 1
fi

# Default values
CHECKPOINT_PATH=""
ITERATIONS=""
TARGET_SCORE=""
LOG_LEVEL="INFO"
OUTPUT_DIR="./openevolve/examples/design_opt_rl_ant/init_xml/ant_new1"   
EXTRACT_TOP=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --checkpoint|-c)
            CHECKPOINT_PATH="$2"
            shift 2
            ;;
        --iterations|-i)
            ITERATIONS="$2"
            shift 2
            ;;
        --target-score|-t)
            TARGET_SCORE="$2"
            shift 2
            ;;
        --log-level|-l)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --extract-top|-e)
            EXTRACT_TOP="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --checkpoint PATH     Resume from checkpoint directory"
            echo "  -i, --iterations NUM      Maximum number of iterations"
            echo "  -t, --target-score NUM    Target score to reach"
            echo "  -l, --log-level LEVEL     Logging level (DEBUG, INFO, WARNING, ERROR)"
            echo "  -o, --output DIR          Output directory"
            echo "  -e, --extract-top NUM     Extract top N non-seed programs from latest checkpoint"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0  # Run fresh optimization"
            echo "  $0 --checkpoint $OUTPUT_DIR/checkpoints/checkpoint_5"
            echo "  $0 --checkpoint checkpoint_5 --iterations 10 --target-score 0.9"
            echo "  $0 --extract-top 3  # Extract top 3 non-seed programs from latest checkpoint"
            echo ""
            echo "Available checkpoints:"
            if [ -d "$OUTPUT_DIR/checkpoints" ]; then
                ls -1 "$OUTPUT_DIR/checkpoints/" | grep "checkpoint_" | sort -V
            else
                echo "  No checkpoints found"
            fi
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set environment variables
export OPENEVOLVE_ROBOT_XML="./openevolve/examples/design_opt_rl_ant/init_xml/best.xml"

# Build command arguments
CMD_ARGS=(
    "./openevolve/examples/design_opt_rl_ant/init_xml/best.xml"
    "./openevolve/examples/design_opt_rl_ant/evaluator.py"
    "--config" "./openevolve/examples/design_opt_rl_ant/config.yaml"
    "--log-level" "$LOG_LEVEL"
    "--output" "$OUTPUT_DIR"
)

# Add checkpoint if specified
if [ -n "$CHECKPOINT_PATH" ]; then
    # Handle relative checkpoint paths
    if [[ "$CHECKPOINT_PATH" =~ ^checkpoint_[0-9]+$ ]]; then
        CHECKPOINT_PATH="$OUTPUT_DIR/checkpoints/$CHECKPOINT_PATH"
    fi
    
    # Verify checkpoint exists
    if [ ! -d "$CHECKPOINT_PATH" ]; then
        echo "Error: Checkpoint directory '$CHECKPOINT_PATH' not found"
        echo "Available checkpoints:"
        if [ -d "$OUTPUT_DIR/checkpoints" ]; then
            ls -1 "$OUTPUT_DIR/checkpoints/" | grep "checkpoint_" | sort -V
        else
            echo "  No checkpoints found"
        fi
        exit 1
    fi
    
    CMD_ARGS+=("--checkpoint" "$CHECKPOINT_PATH")
    echo "Resuming from checkpoint: $CHECKPOINT_PATH"
    
    # Display checkpoint information
    if [ -f "$CHECKPOINT_PATH/metadata.json" ]; then
        echo "Checkpoint information:"
        echo "  Last iteration: $(jq -r '.last_iteration' "$CHECKPOINT_PATH/metadata.json" 2>/dev/null || echo "Unknown")"
        echo "  Best program ID: $(jq -r '.best_program_id' "$CHECKPOINT_PATH/metadata.json" 2>/dev/null || echo "Unknown")"
        echo "  Programs in database: $(jq -r '.archive | length' "$CHECKPOINT_PATH/metadata.json" 2>/dev/null || echo "Unknown")"
    fi
else
    echo "Starting fresh optimization..."
fi

# Add iterations if specified
if [ -n "$ITERATIONS" ]; then
    CMD_ARGS+=("--iterations" "$ITERATIONS")
fi

# Add target score if specified
if [ -n "$TARGET_SCORE" ]; then
    CMD_ARGS+=("--target-score" "$TARGET_SCORE")
fi

echo "Initial design: $OPENEVOLVE_ROBOT_XML"
echo "Output directory: $OUTPUT_DIR"
echo "Command: python ./openevolve/openevolve-run.py ${CMD_ARGS[*]}"
echo ""

# Run the optimization only if not extracting top programs
if [ -z "$EXTRACT_TOP" ]; then
    # Run the optimization
    python ./openevolve/openevolve-run.py "${CMD_ARGS[@]}"
fi

# Handle extract-top option
if [ -n "$EXTRACT_TOP" ]; then
    echo ""
    echo "Extracting top $EXTRACT_TOP non-seed programs..."
    
    # Find latest checkpoint
    if [ -d "$OUTPUT_DIR/checkpoints" ]; then
        LATEST_CHECKPOINT=$(ls -1 "$OUTPUT_DIR/checkpoints" | grep "checkpoint_" | sort -V | tail -1)
        if [ -n "$LATEST_CHECKPOINT" ]; then
            CHECKPOINT_PATH="$OUTPUT_DIR/checkpoints/$LATEST_CHECKPOINT"
            echo "Using checkpoint: $CHECKPOINT_PATH"
            
            # Run extraction script
            python ./openevolve/examples/design_opt_rl_ant/extract_top_programs.py \
                "$CHECKPOINT_PATH" \
                --config "./openevolve/examples/design_opt_rl_ant/config.yaml" \
                --output "$OUTPUT_DIR/top_programs" \
                --count "$EXTRACT_TOP" \
                --file-extension ".xml"
            
            echo ""
            echo "Top $EXTRACT_TOP programs extracted to: $OUTPUT_DIR/top_programs"
        else
            echo "Error: No checkpoints found in $OUTPUT_DIR/checkpoints"
            exit 1
        fi
    else
        echo "Error: No checkpoints directory found at $OUTPUT_DIR/checkpoints"
        exit 1
    fi
else
    echo ""
    echo "Optimization complete!"
    echo "Results saved to: $OUTPUT_DIR"
    echo ""
    echo "Latest checkpoint:"
    if [ -d "$OUTPUT_DIR/checkpoints" ]; then
        LATEST_CHECKPOINT=$(ls -1 "$OUTPUT_DIR/checkpoints" | grep "checkpoint_" | sort -V | tail -1)
        if [ -n "$LATEST_CHECKPOINT" ]; then
            echo "  $OUTPUT_DIR/checkpoints/$LATEST_CHECKPOINT"
            echo "  To resume from this checkpoint, use:"
            echo "    $0 --checkpoint $LATEST_CHECKPOINT"
            echo ""
            echo "  To extract top programs, use:"
            echo "    $0 --extract-top 3"
        fi
    fi
fi