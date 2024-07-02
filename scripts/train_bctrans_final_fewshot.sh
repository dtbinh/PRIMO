
# sbatch slurm/run_rtx6000.sbatch python train.py --config-name=train_fewshot.yaml \
#     task=metaworld_ml45_prise_fewshot \
#     algo=bc_transformer \
#     exp_name=bc_d64_bs64 \
#     variant_name=block_10 \
#     training.use_tqdm=false \
#     training.use_amp=true \
#     training.save_all_checkpoints=true \
#     train_dataloader.persistent_workers=true \
#     train_dataloader.num_workers=6 \
#     train_dataloader.batch_size=64 \
#     make_unique_experiment_dir=false \
#     algo.skill_block_size=1 \
#     algo.frame_stack=10 \
#     algo.embed_dim=64 \
#     training.n_epochs=100 \
#     training.save_interval=10 \
#     training.auto_continue=true \
#     seed=0

sbatch slurm/run_rtx6000.sbatch python train.py --config-name=train_fewshot.yaml \
    task=metaworld_ml45_prise_fewshot \
    algo=bc_transformer \
    exp_name=bc_d64 \
    variant_name=block_10 \
    training.use_tqdm=false \
    training.use_amp=true \
    training.save_all_checkpoints=true \
    train_dataloader.persistent_workers=true \
    train_dataloader.num_workers=6 \
    make_unique_experiment_dir=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=64 \
    training.n_epochs=100 \
    training.save_interval=10 \
    training.auto_continue=true \
    seed=0

sbatch slurm/run_rtx6000.sbatch python train.py --config-name=train_fewshot.yaml \
    task=metaworld_ml45_prise_fewshot \
    algo=bc_transformer \
    exp_name=bc_d256 \
    variant_name=block_10 \
    training.use_tqdm=false \
    training.use_amp=true \
    training.save_all_checkpoints=true \
    train_dataloader.persistent_workers=true \
    train_dataloader.num_workers=6 \
    make_unique_experiment_dir=false \
    algo.skill_block_size=1 \
    algo.frame_stack=10 \
    algo.embed_dim=256 \
    training.n_epochs=100 \
    training.save_interval=10 \
    training.auto_continue=true \
    seed=0


# # for debugging
# python train.py --config-name=train_fewshot.yaml \
#     task=metaworld_ml45_prise_fewshot \
#     algo=bc_transformer \
#     exp_name=bc_debug \
#     variant_name=block_10 \
#     training.use_tqdm=true \
#     training.use_amp=true \
#     training.save_all_checkpoints=false \
#     train_dataloader.persistent_workers=true \
#     train_dataloader.num_workers=6 \
#     make_unique_experiment_dir=true \
#     algo.skill_block_size=1 \
#     algo.frame_stack=10 \
#     training.n_epochs=200 \
#     logging.mode=disabled \
#     training.do_profile=True \
#     task.env_runner.debug=true \
#     seed=0