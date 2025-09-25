#!/usr/bin/env python3
"""
Extract top programs from OpenEvolve checkpoint, excluding elite seeds
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add openevolve to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openevolve.database import ProgramDatabase, Program
from openevolve.config import load_config


def load_checkpoint_database(checkpoint_path: str, config_path: str) -> ProgramDatabase:
    """Load database from checkpoint"""
    config = load_config(config_path)
    database = ProgramDatabase(config.database)
    database.load(checkpoint_path)
    return database


def get_top_non_seed_programs(
    database: ProgramDatabase, 
    n: int = 3, 
    metric: Optional[str] = None
) -> List[Program]:
    """
    Get top N programs excluding elite seeds
    
    Args:
        database: ProgramDatabase instance
        n: Number of programs to return
        metric: Metric to use for ranking (uses combined_score or average if None)
    
    Returns:
        List of top programs excluding seeds
    """
    # Get all programs
    all_programs = list(database.programs.values())
    
    # Filter out seed programs
    non_seed_programs = [
        p for p in all_programs 
        if not (p.metadata.get("seed", False))
    ]
    
    if not non_seed_programs:
        print("Warning: No non-seed programs found in database")
        return []
    
    # Sort by metric
    if metric:
        # Sort by specific metric
        sorted_programs = sorted(
            [p for p in non_seed_programs if metric in p.metrics],
            key=lambda p: p.metrics[metric],
            reverse=True,
        )
    else:
        # Sort by combined_score if available, otherwise by average of all numeric metrics
        from openevolve.utils.metrics_utils import get_fitness_score
        sorted_programs = sorted(
            non_seed_programs,
            key=lambda p: get_fitness_score(p.metrics, database.config.feature_dimensions),
            reverse=True,
        )
    
    return sorted_programs[:n]


def save_programs(programs: List[Program], output_dir: str, file_extension: str = ".xml") -> None:
    """Save programs to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, program in enumerate(programs, 1):
        # Save program code
        filename = f"top_{i}_program{file_extension}"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(program.code)
        
        # Save program metadata
        metadata_filename = f"top_{i}_program_info.json"
        metadata_filepath = os.path.join(output_dir, metadata_filename)
        
        metadata = {
            "id": program.id,
            "generation": program.generation,
            "iteration_found": program.iteration_found,
            "timestamp": program.timestamp,
            "parent_id": program.parent_id,
            "metrics": program.metrics,
            "language": program.language,
            "metadata": program.metadata,
            "rank": i
        }
        
        with open(metadata_filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved top {i} program to {filepath}")
        print(f"  Metrics: {program.metrics}")
        print(f"  Found at iteration: {program.iteration_found}")
        print(f"  Program ID: {program.id}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Extract top programs from OpenEvolve checkpoint")
    parser.add_argument("--env", "-e", help="Environment", 
                        type=str, default="ant")
    parser.add_argument("--iteration", "-i", help="Iteration", 
                        type=int, default=100)
    parser.add_argument("--count", "-n", help="Number of top programs to extract", 
                       type=int, default=3)
    parser.add_argument("--metric", "-m", help="Metric to use for ranking", 
                       default=None)
    parser.add_argument("--file-extension", help="File extension for saved programs", 
                       default=".xml")
    
    args = parser.parse_args()

    checkpoint_path = os.path.join(f"./openevolve/examples/design_opt_rl_{args.env}/init_xml/{args.env}_new1/checkpoints", f"checkpoint_{args.iteration}")
    output_path = os.path.join(f"./openevolve/examples/design_opt_rl_{args.env}/result/{args.env}/top_programs")
    config_path = os.path.join(f"./openevolve/examples/design_opt_rl_{args.env}", 'config.yaml')
    
    # Validate checkpoint path
    if not os.path.exists(checkpoint_path):
        print(f"Error: Checkpoint directory '{checkpoint_path}' not found")
        return 1
    
    # Validate config path
    if not os.path.exists(config_path):
        print(f"Error: Config file '{config_path}' not found")
        return 1
    
    try:
        # Load database from checkpoint
        print(f"Loading checkpoint from {checkpoint_path}")
        database = load_checkpoint_database(checkpoint_path, config_path)
        
        print(f"Database loaded successfully")
        print(f"Total programs: {len(database.programs)}")
        
        # Count seed programs
        seed_count = sum(1 for p in database.programs.values() if p.metadata.get("seed", False))
        print(f"Seed programs: {seed_count}")
        print(f"Non-seed programs: {len(database.programs) - seed_count}")
        print()
        
        # Get top non-seed programs
        top_programs = get_top_non_seed_programs(database, args.count, args.metric)
        
        if not top_programs:
            print("No non-seed programs found to extract")
            return 0
        
        print(f"Extracting top {len(top_programs)} non-seed programs:")
        print()
        
        # Save programs
        save_programs(top_programs, output_path, args.file_extension)
        
        print(f"Successfully extracted {len(top_programs)} programs to {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

