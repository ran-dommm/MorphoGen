# Robot Structure Design Optimization with OpenEvolve + Transform2Act

This example demonstrates how to optimize robot morphology using OpenEvolve with Transform2Act's RL training system. The system directly optimizes MuJoCo XML robot descriptions to maximize locomotion performance.

## Overview

- **Input**: MuJoCo XML robot description
- **Optimization**: Robot structure (body positions, joint configurations, actuator settings)
- **Evaluation**: RL training using Transform2Act + locomotion performance measurement
- **Output**: Optimized robot designs with improved locomotion capabilities

## Key Features

1. **Direct XML Optimization**: LLM directly modifies the complete XML structure
2. **RL-based Evaluation**: Each design is trained using Transform2Act's RL algorithms
3. **Multi-objective Optimization**: Balances locomotion performance, structural complexity, and actuator efficiency
4. **Cascaded Evaluation**: Two-stage evaluation (quick validation → full training)

## Files

- `initial_ant.xml`: Starting robot design (4-legged ant-like robot)
- `evaluator.py`: Evaluation system using Transform2Act training
- `config.yaml`: OpenEvolve configuration for XML optimization
- `README.md`: This documentation

## Requirements

1. **Transform2Act Environment**: This example requires the Transform2Act codebase to be available at `../../Transform2Act/`
2. **MuJoCo**: MuJoCo physics simulator
3. **PyTorch**: For RL training
4. **Additional dependencies**: See Transform2Act requirements

## Usage

```bash
# From the openevolve root directory
python openevolve-run.py examples/design_opt_rl/initial_ant.xml examples/design_opt_rl/evaluator.py --config examples/design_opt_rl/config.yaml
```

## How It Works

### 1. XML Structure Optimization

The LLM receives the complete MuJoCo XML and can modify:
- **Body structure**: Positions, orientations, hierarchies
- **Joint configurations**: Types, ranges, axes
- **Geometry**: Sizes, shapes, positions of limbs
- **Actuators**: Motor specifications and gear ratios

### 2. Evaluation Process

Each generated XML design goes through:

**Stage 1 (Quick Validation)**:
- XML syntax and structure validation
- Basic structural metrics calculation
- Short RL training (5 epochs) for feasibility check

**Stage 2 (Full Evaluation)**:
- Extended RL training (20 epochs) using Transform2Act
- Locomotion performance measurement
- Multi-objective scoring

### 3. Scoring System

The combined score considers:
- **Locomotion Performance (70%)**: Forward movement speed/distance
- **Structural Complexity (20%)**: Number of bodies/joints (normalized)
- **Actuator Efficiency (10%)**: Coverage of joints by motors

## Design Principles

### Structural Requirements
- Root body at appropriate height for stability
- Proper joint-actuator correspondence
- Valid XML syntax and MuJoCo compatibility
- Reasonable physical parameters

### Optimization Strategies
- **Limb Design**: Optimize lengths and orientations for locomotion
- **Joint Configuration**: Adjust ranges and axes for better movement
- **Actuator Tuning**: Set appropriate gear ratios
- **Complexity Management**: Balance capability with controllability

## Example Evolution

Starting from a simple 4-legged ant design, the system might evolve:
1. **Limb length optimization** for better stride
2. **Joint range adjustments** for more flexible movement
3. **Additional body segments** for more complex gaits
4. **Actuator rebalancing** for better control

## Configuration Options

### Key Parameters
- `max_iterations: 10`: Number of evolution iterations
- `diff_based_evolution: false`: Use full XML rewrite mode
- `language: "xml"`: Set language type for proper parsing
- `cascade_thresholds: [0.3]`: Minimum score to proceed to stage 2

### Database Settings
- `feature_dimensions: ["complexity_score", "actuator_efficiency"]`: MAP-Elites dimensions
- `population_size: 15`: Number of designs maintained
- `num_islands: 2`: Parallel evolution islands

### Evaluation Settings
- `timeout: 900`: 15-minute timeout per evaluation
- `parallel_evaluations: 1`: Single evaluation due to training overhead

## Tips for Success

1. **Start Simple**: Begin with basic designs and let evolution add complexity
2. **Monitor Training**: Check Transform2Act training logs for convergence
3. **Adjust Timeouts**: Increase if training needs more time
4. **Feature Engineering**: Modify feature dimensions for different optimization goals

## Troubleshooting

### Common Issues
- **XML Parsing Errors**: Check generated XML syntax
- **MuJoCo Simulation Failures**: Verify physical parameter validity
- **Training Timeouts**: Increase evaluation timeout or reduce training epochs
- **Transform2Act Path Issues**: Ensure correct relative path to Transform2Act

### Debug Tips
- Check `openevolve_output/logs/` for detailed execution logs
- Monitor temporary XML files during evaluation
- Verify Transform2Act installation and dependencies

## Extension Ideas

1. **Multi-Environment Evaluation**: Test designs on different terrains
2. **Task-Specific Optimization**: Optimize for specific locomotion tasks
3. **Energy Efficiency**: Add energy consumption metrics
4. **Robustness Testing**: Evaluate under various conditions
5. **Interactive Design**: Allow manual design constraints or preferences
