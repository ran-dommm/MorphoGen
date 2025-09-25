"""
Evaluator for robot structure design optimization using Transform2Act.
"""

import os
import subprocess
import re
import tempfile
import traceback
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any
import yaml
import random
import openai
import logging

logger = logging.getLogger(__name__)

cfg = 'ant'
epoch = 100
gpu_index = 5
num_threads = 40

def validate_xml_structure(xml_content: str) -> Dict[str, Any]:
    """
    Validate XML structure and extract basic metrics.
    
    Args:
        xml_content: XML string content
        
    Returns:
        Dictionary with validation results and basic metrics
    """
    try:
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Check if it's a valid MuJoCo model
        if root.tag != 'mujoco':
            return {"valid": False, "error": "Root element must be 'mujoco'"}
        
        # Extract basic structure information
        bodies = root.findall('.//body')
        joints = root.findall('.//joint[@type="hinge"]')  # Only count hinge joints
        actuators = root.findall('.//motor')
        
        num_bodies = len(bodies)
        num_joints = len(joints)
        num_actuators = len(actuators)
        
        # Basic validation checks
        if num_bodies == 0:
            return {"valid": False, "error": "No bodies found in XML"}
        
        if num_joints == 0:
            return {"valid": False, "error": "No hinge joints found in XML"}
        
        # Check if actuators match joints (approximately)
        joint_names = {joint.get('name') for joint in joints if joint.get('name')}
        actuator_joints = {motor.get('joint') for motor in actuators if motor.get('joint')}
        
        # Count matching actuators
        matching_actuators = len(joint_names.intersection(actuator_joints))
        actuator_coverage = matching_actuators / len(joint_names) if joint_names else 0
        
        return {
            "valid": True,
            "num_bodies": num_bodies,
            "num_joints": num_joints,
            "num_actuators": num_actuators,
            "actuator_coverage": actuator_coverage,
            "complexity_score": min(num_bodies / 10.0, 1.0),  # Normalize complexity
            "actuator_efficiency": actuator_coverage
        }
        
    except ET.ParseError as e:
        print(xml_content)
        return {"valid": False, "error": f"XML parsing error: {str(e)}"}
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {str(e)}"}


def train_and_evaluate_design(xml_content: str, max_epochs: int = 20) -> float:
    """
    Train and evaluate a robot design using Transform2Act.
    
    Args:
        xml_content: MuJoCo XML content as string
        max_epochs: Maximum training epochs
        
    Returns:
        Best reward achieved during training
    """
    # Create temporary XML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
        temp_file.write(xml_content)
        xml_path = temp_file.name
    
    try:
        # Path to Transform2Act
        transform2act_dir = os.path.abspath('./Transform2Act')
        train_script = os.path.join(transform2act_dir, 'design_opt/train.py')
        
        if not os.path.exists(train_script):
            print(f"Transform2Act training script not found: {train_script}")
            return 0.0
        
        # Prepare training command
        cmd = [
            'python', train_script,
            '--cfg', cfg,
            '--ctrl_only',
            '--xml_path', os.path.abspath(xml_path),
            '--max_epoch_num', str(max_epochs),
            '--epoch', str(epoch),
            '--num_threads', str(num_threads),
            '--gpu_index', str(gpu_index),
        ]
        
        print(f"Running training with command: {' '.join(cmd)}")
        
        # Run training
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=transform2act_dir,
            timeout=1800,  # 30 minute timeout
            env=os.environ.copy(),
        )
        
        if result.returncode != 0:
            logger.error("Training process failed.")
            logger.error("STDOUT:", result.stdout)
            logger.error("STDERR:", result.stderr)
            return 0.0
        
        # Parse output to extract best reward
        output = result.stdout
        best_reward = -1e9
        # print(f"Training output: {output}")

        # Look for the definitive best reward from the end of the script
        match = re.search(r'BEST_EVAL_RESULT:([-\d.]+)', output)
        if match:
            try:
                best_reward = float(match.group(1))
                # logger.info(f"Training completed. Best reward from BEST_EVAL_RESULT: {best_reward}")
                return best_reward
            except ValueError:
                logger.error("Could not parse BEST_EVAL_RESULT.")

        # Fallback to parsing log lines if the final result isn't found
        for line in output.split('\n'):
            # Pattern: exec_R_eps followed by reward value
            if 'exec_R_eps' in line:
                match = re.search(r'exec_R_eps\s+([-\d.]+)', line)
                if match:
                    try:
                        reward = float(match.group(1))
                        if reward > best_reward:
                            best_reward = reward
                    except ValueError:
                        continue
            
            # Alternative pattern: look for reward in different formats
            elif 'reward' in line.lower() and 'mean' in line.lower():
                numbers = re.findall(r'[-+]?\d*\.?\d+', line)
                for num_str in numbers:
                    try:
                        reward = float(num_str)
                        if -1000 < reward < 1000:  # Reasonable reward range
                            best_reward = max(best_reward, reward)
                    except ValueError:
                        continue
        
        logger.info(f"Training completed. Best reward: {best_reward}")
        return best_reward if best_reward != -1e9 else 0.0
        
    except subprocess.TimeoutExpired:
        print("Training timed out")
        return 0.0
    except Exception as e:
        print(f"Training failed with error: {str(e)}")
        traceback.print_exc()
        return 0.0
    finally:
        # Clean up temporary file
        try:
            os.unlink(xml_path)
        except:
            pass

def evaluate_design(xml_content: str) -> Dict[str, Any]:
    """
    Evaluate a robot design using Transform2Act.
    
    Args:
        xml_content: MuJoCo XML content as string
        
    Returns:
        E+valuation metrics
    """
    # Create temporary XML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
        temp_file.write(xml_content)
        xml_path = temp_file.name
    
    try:
        # Path to Transform2Act
        transform2act_dir = os.path.abspath('./Transform2Act')
        eval_script = os.path.join(transform2act_dir, 'design_opt/eval.py')
        
        if not os.path.exists(eval_script):
            print(f"Transform2Act evaluation script not found: {eval_script}")
            return 0.0
        
        # Prepare training command
        cmd = [
            'python', eval_script,
            '--cfg', cfg,
            '--xml_path', os.path.abspath(xml_path),
            '--epoch', str(epoch),
            '--no_render',
            '--ctrl_only',
        ]
        
        print(f"Running evaluation with command: {' '.join(cmd)}")
        
        # Run training
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=transform2act_dir,
            timeout=1800,  # 30 minute timeout
            env=os.environ.copy(),
        )
        
        if result.returncode != 0:
            print("Evaluation process failed.")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return 0.0
        
        # Parse output to extract best reward
        output = result.stdout
        # print(f"Evaluation output: {output}")
        best_reward = -1e9

        # Look for the definitive best reward from the end of the script: EVALUATION RESULT: 100.0
        match = re.search(r'EVALUATION RESULT:\s*([-\d.]+)', output)
        if match:
            try:
                best_reward = float(match.group(1))
                print(f"Evaluation completed. Best reward from EVALUATION RESULT: {best_reward}")
                return best_reward
            except ValueError:
                print("Could not parse EVALUATION RESULT.")

        # Fallback to parsing log lines if the final result isn't found
        for line in output.split('\n'):
            # Pattern: exec_R_eps followed by reward value
            if 'exec_R_eps' in line:
                match = re.search(r'exec_R_eps\s+([-\d.]+)', line)
                if match:
                    try:
                        reward = float(match.group(1))
                        if reward > best_reward:
                            best_reward = reward
                    except ValueError:
                        continue
            
            # Alternative pattern: look for reward in different formats
            elif 'reward' in line.lower() and 'mean' in line.lower():
                numbers = re.findall(r'[-+]?\d*\.?\d+', line)
                for num_str in numbers:
                    try:
                        reward = float(num_str)
                        if -1000 < reward < 1000:  # Reasonable reward range
                            best_reward = max(best_reward, reward)
                    except ValueError:
                        continue
        
        logger.info(f"Evaluation completed. Best reward: {best_reward}")

        return best_reward if best_reward != -1e9 else 0.0
        
    except subprocess.TimeoutExpired:
        logger.error("Evaluation timed out")
        return 0.0
    except Exception as e:
        logger.error(f"Evaluation failed with error: {str(e)}")
        traceback.print_exc()
        return 0.0
    finally:
        # Clean up temporary file
        try:
            os.unlink(xml_path)
        except:
            pass



def evaluate(xml_path: str) -> Dict[str, Any]:
    """
    Main evaluation function for XML robot designs.
    
    Args:
        xml_path: Path to XML file containing robot design
        
    Returns:
        Dictionary of evaluation metrics
    """
    try:
        # Read XML content
        with open(xml_path, 'r') as f:
            xml_content = f.read().strip()
        
        # Validate XML structure first
        validation_result = validate_xml_structure(xml_content)
        
        if not validation_result["valid"]:
            return {
                "combined_score": 0.0,
                "locomotion_reward": 0.0,
                "complexity_score": 0.0,
                "actuator_efficiency": 0.0,
                "error": validation_result["error"]
            }
        
        # Extract structural metrics
        complexity_score = validation_result["complexity_score"]
        actuator_efficiency = validation_result["actuator_efficiency"]
        
        # Train and evaluate locomotion performance
        print("Starting locomotion training and evaluation...")
        locomotion_reward = train_and_evaluate_design(xml_content, max_epochs=1)
        
        normalized_locomotion = locomotion_reward / 2000
        
        # Calculate combined score
        combined_score = max(0, min(normalized_locomotion, 1.0))
        
        results = {
            "combined_score": combined_score,
            "locomotion_reward": locomotion_reward,
            "normalized_locomotion": normalized_locomotion,
            "complexity_score": complexity_score,
            "actuator_efficiency": actuator_efficiency,
            "num_bodies": validation_result["num_bodies"],
            "num_joints": validation_result["num_joints"],
            "num_actuators": validation_result["num_actuators"]
        }
        
        return results
        
    except Exception as e:
        print(f"Evaluation failed: {str(e)}")
        traceback.print_exc()
        return {
            "combined_score": 0.0,
            "locomotion_reward": 0.0,
            "complexity_score": 0.0,
            "actuator_efficiency": 0.0,
            "error": str(e)
        }


def evaluate_stage1(xml_path: str) -> Dict[str, Any]:
    """
    Stage 1 evaluation: Quick validation and basic training.
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        Dictionary with basic metrics
    """
    print("Starting stage 1 evaluation...")
    try:
        # Read XML content
        with open(xml_path, 'r') as f:
            xml_content = f.read().strip()
        
        # Validate XML structure
        validation_result = validate_xml_structure(xml_content)
        
        if not validation_result["valid"]:
            print(f"Stage 1 evaluation failed: {validation_result['error']}")
            return {
                "combined_score": 0.0,
                "structural_validity": 0.0,
                "complexity_score": 0.0,
                "actuator_efficiency": 0.0,
                "error": validation_result["error"]
            }
        
        # Quick training with fewer epochs
        locomotion_reward = evaluate_design(xml_content)
        normalized_locomotion = locomotion_reward / 2000
        
        # Simple combined score for stage 1
        # combined_score = (
        #     0.9 * normalized_locomotion +
        #     0.05 * validation_result["complexity_score"] + 
        #     0.05 * validation_result["actuator_efficiency"]
        # )
        combined_score = max(0, min(normalized_locomotion, 1.0))
        
        return {
            "combined_score": combined_score,
            "structural_validity": 1.0,
            "complexity_score": validation_result["complexity_score"],
            "actuator_efficiency": validation_result["actuator_efficiency"],
            "locomotion_reward": locomotion_reward
        }
        
    except Exception as e:
        print(f"Stage 1 evaluation failed: {str(e)}")
        return {
            "combined_score": 0.0,
            "structural_validity": 0.0,
            "complexity_score": 0.0,
            "error": str(e)
        }


def evaluate_stage2(xml_path: str) -> Dict[str, Any]:
    """
    Stage 2 evaluation: Full evaluation with complete training.
    
    Args:
        xml_path: Path to XML file
        
    Returns:
        Dictionary with complete metrics
    """
    print("Starting stage 2 evaluation...")
    return evaluate(xml_path)