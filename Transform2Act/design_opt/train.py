import argparse
import os
import sys
sys.path.append(os.getcwd())

from khrylib.utils import *
from design_opt.utils.config import Config
from design_opt.agents.transform2act_agent import Transform2ActAgent


parser = argparse.ArgumentParser()
parser.add_argument('--cfg', default=None)
parser.add_argument('--ctrl_only', action='store_true', default=False)
parser.add_argument('--render', action='store_true', default=False)
parser.add_argument('--tmp', action='store_true', default=False)
parser.add_argument('--num_threads', type=int, default=20)
parser.add_argument('--gpu_index', type=int, default=0)
parser.add_argument('--epoch', default='0')
parser.add_argument('--show_noise', action='store_true', default=False)
parser.add_argument('--xml_path', default=None)
parser.add_argument('--max_epoch_num', type=int, default=1000)
args = parser.parse_args()
if args.render:
    args.num_threads = 1
cfg = Config(args.cfg, args.tmp, ctrl_only=args.ctrl_only, xml_path=args.xml_path, max_epoch_num=args.max_epoch_num)

dtype = torch.float64
torch.set_default_dtype(dtype)
device = torch.device('cuda', index=args.gpu_index) if torch.cuda.is_available() else torch.device('cpu')
if torch.cuda.is_available():
    torch.cuda.set_device(args.gpu_index)
np.random.seed(cfg.seed)
torch.manual_seed(cfg.seed)

start_epoch = int(args.epoch) if args.epoch.isnumeric() else args.epoch

"""create agent"""
agent = Transform2ActAgent(cfg=cfg, dtype=dtype, device=device, seed=cfg.seed, num_threads=args.num_threads, training=True, checkpoint=start_epoch)


def main_loop():
    best_eval_result = -float('inf')

    start_epoch_int = start_epoch
    if start_epoch == 'best' or start_epoch is None:
        start_epoch_int = 0

    print(f"start_epoch: {start_epoch}")
    if args.render:
        agent.pre_epoch_update(start_epoch_int)
        agent.sample(1e8, mean_action=not args.show_noise, render=True)
        return 0.0
    else:
        for epoch in range(start_epoch_int, start_epoch_int + cfg.max_epoch_num):
            eval_result = agent.optimize(epoch)
            if eval_result is not None and eval_result > best_eval_result:
                best_eval_result = eval_result
            agent.save_checkpoint(epoch)

            """clean up gpu memory"""
            torch.cuda.empty_cache()

        agent.logger.info('training done!')
        print
    return best_eval_result

best_result = main_loop()
print(f"BEST_EVAL_RESULT:{best_result}")

