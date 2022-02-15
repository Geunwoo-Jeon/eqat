import argparse
import logging
import logging.config
import os
import time

import munch
import yaml


def merge_nested_dict(d, other):
    new = dict(d)
    for k, v in other.items():
        if d.get(k, None) is not None and type(v) is dict:
            new[k] = merge_nested_dict(d[k], v)
        else:
            new[k] = v
    return new


def get_config(config_file):
    with open(config_file) as yaml_file:
        cfg = yaml.safe_load(yaml_file)
    return munch.munchify(cfg)


def init_logger(experiment_name, output_dir, cfg_file=None):
    time_str = time.strftime("%Y%m%d-%H%M%S")
    exp_full_name = time_str if experiment_name is None else experiment_name + '_' + time_str
    log_dir = output_dir / exp_full_name
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / (exp_full_name + '.log')
    logging.config.fileConfig(cfg_file, defaults={'logfilename': log_file})
    logger = logging.getLogger()
    logger.info('Log file for this run: ' + str(log_file))
    return log_dir
