# python train.py --config-name=train_prior.yaml \
#     task=metaworld_ml45_prise \
#     training.use_amp=false \
#     train_dataloader.num_workers=6 \
#     algo.skill_block_size=16 \
#     algo.downsample_factor=2


downsample_factors=(2 4)
seeds=(4 5)

for downsample_factor in ${downsample_factors[@]}; do
    for seed in ${seeds[@]}; do
        sbatch slurm/run_rtx6000.sbatch python train.py --config-name=train_fewshot.yaml \
            task=metaworld_ml45_prise_fewshot \
            exp_name=quest_cs_1024.1 \
            variant_name=block_16_ds_${downsample_factor} \
            training.use_tqdm=false \
            training.save_all_checkpoints=true \
            training.use_amp=false \
            train_dataloader.persistent_workers=true \
            train_dataloader.num_workers=6 \
            make_unique_experiment_dir=false \
            algo.skill_block_size=16 \
            algo.downsample_factor=$downsample_factor \
            seed=$seed \
            checkpoint_path=/storage/home/hcoda1/1/awilcox31/p-agarg35-0/albert/quest/experiments/metaworld/ML45_PRISE/quest/quest_cs_1024/block_16_ds_${downsample_factor}/${seed}/stage_1/
    done
done







