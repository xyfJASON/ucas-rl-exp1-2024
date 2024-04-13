import os
import yaml
import argparse
import datetime

import numpy as np

from learners.q_learning import QLearning
from envs.pendulum import PendulumEnv, StateQuantizer, ActionQuantizer


def get_parser():
    parser = argparse.ArgumentParser()
    # system
    parser.add_argument('--logdir', type=str, help='log directory')
    parser.add_argument('--no-test-gif', action='store_true', help='do not save test gif')
    # hyper-parameters
    parser.add_argument('--alpha', type=float, default=0.1, help='learning rate')
    parser.add_argument('--gamma', type=float, default=0.98, help='discount factor')
    parser.add_argument('--epsilon', type=float, default=0.1, help='epsilon-greedy policy')
    parser.add_argument('--episodes', type=int, default=100, help='number of episodes')
    parser.add_argument('--episode_length', type=int, default=10000, help='length of each episode')
    parser.add_argument('--num_disc_alpha', type=int, default=20, help='discretization of alpha')
    parser.add_argument('--num_disc_alpha_dot', type=int, default=20, help='discretization of alpha_dot')
    parser.add_argument('--num_u', type=int, default=3, help='discretization of u')
    # special discretization method for pendulum problem
    parser.add_argument('--power_disc_alpha', type=int, default=1, help='power of discretization of alpha')
    parser.add_argument('--power_disc_alpha_dot', type=int, default=1, help='power of discretization of alpha_dot')
    return parser


def main():
    # Arguments
    args = get_parser().parse_args()
    if args.logdir is None:
        args.logdir = f"./logs/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    os.makedirs(args.logdir, exist_ok=True)
    with open(f'{args.logdir}/args.yaml', 'w') as f:
        args_dict = args.__dict__.copy()
        args_dict.pop('logdir')
        yaml.dump(args_dict, f, default_flow_style=False)

    # Initialize
    env = PendulumEnv()

    def func(array, power):
        result = array ** power
        if power % 2 == 0:
            result *= np.sign(array)
        return result

    uni = np.arange(-1, 1, 2 / args.num_disc_alpha)
    alpha_table = func(uni, args.power_disc_alpha) * np.pi

    uni = np.linspace(-1, 1, args.num_disc_alpha_dot)
    alpha_dot_table = func(uni, args.power_disc_alpha_dot) * 15 * np.pi

    learner = QLearning(
        env=env,
        state_quantizer=StateQuantizer(
            num_disc_alpha=args.num_disc_alpha,
            num_disc_alpha_dot=args.num_disc_alpha_dot,
            alpha_table=alpha_table,
            alpha_dot_table=alpha_dot_table,
        ),
        action_quantizer=ActionQuantizer(num_u=args.num_u),
    )

    # Train
    learner.train(
        episodes=args.episodes,
        episode_length=args.episode_length,
        epsilon=args.epsilon,
        learning_rate=args.alpha,
        discount_factor=args.gamma,
    )

    # Save Q-table
    np.save(os.path.join(args.logdir, 'q_table.npy'), learner.Q)

    # Test
    states, actions, rewards = learner.test(episode_length=1000)
    np.save(os.path.join(args.logdir, 'test_rewards.npy'), rewards)
    env.plot_curve(states, actions, rewards, os.path.join(args.logdir, 'test.png'))
    if not args.no_test_gif:
        env.animate(states, actions, os.path.join(args.logdir, 'test.gif'))


if __name__ == '__main__':
    main()
