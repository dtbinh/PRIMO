
sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d64 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=64 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d64/block_10/0/stage_1 \
    seed=0

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d256 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=256 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d256/block_10/0/stage_1 \
    seed=0

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d64 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=64 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d64/block_10/0/stage_1 \
    seed=1

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d256 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=256 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d256/block_10/0/stage_1 \
    seed=1

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d64 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=64 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d64/block_10/0/stage_1 \
    seed=2

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d256 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=256 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d256/block_10/0/stage_1 \
    seed=2

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d64 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=64 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d64/block_10/0/stage_1 \
    seed=3

sbatch slurm/run_rtx6000.sbatch python evaluate.py \
    task=metaworld_ml45_prise \
    algo=bc_transformer \
    exp_name=eval_bc_d256 \
    variant_name=block_10 \
    training.use_tqdm=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=256 \
    checkpoint_path=/storage/home/hcoda1/0/amete7/p-agarg35-0/PRIMO/experiments/metaworld/ML45_PRISE/bc_transformer_policy/bc_d256/block_10/0/stage_1 \
    seed=3
