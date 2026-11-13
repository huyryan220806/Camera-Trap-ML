# R6 cross-entropy audit

Selected epoch: 13; lowest validation CE epoch: 13.

Train online CE: 0.430585 -> 0.222018. Validation CE: 0.483298 -> 0.422491.

Validation improves then fluctuates near a plateau. There is no observed loss divergence. A decreasing online train loss with plateauing validation may suggest increasing train fit; the gap alone does not prove overfitting because measurement conditions differ.

The original train curve is an average across optimizer updates with augmentation. Validation uses one end-of-epoch model in eval mode without augmentation. Both losses use mean-parent-mean-crop cross entropy; accuracy/F1 use mean crop probabilities per image. Validation explicitly calls model.eval() and torch.inference_mode(). Training enables only the last two blocks, final norm and head; other modules remain eval. Best checkpoint is selected by image macro-F1 with earliest tie; patience is 5.

No train-eval accuracy/F1 history exists. Only supplementary eval of the selected epoch can be added. No implementation defect was found in these reviewed paths; supplementary same-mode GPU evaluation has completed; independent TV2 review is pending. The task document references dino_w6_r6.py; the actual bound implementation is dino_w6.py.

Decision: KEEP_R6 for the 14/11 report, as proposed by TV2; independent review of supplementary evaluation remains pending. No new candidate training has been performed.

## Supplementary checkpoint evaluation

Epoch 13, eval mode, no augmentation, full train and unchanged validation. Train: 4246 images / 4729 crops; CE 0.2293024063, accuracy 0.9390014131, macro-F1 0.9394727952. Validation: 600 images / 680 crops; CE 0.4211072028, accuracy 0.865, macro-F1 0.8641867348. Both losses use mean-parent-mean-crop CE.

The same-mode gap is 0.1918047965 CE and 0.0740014131 accuracy. This is consistent with a generalization gap and warrants investigation; it does not establish the cause or prove a particular weight decay will improve validation. Exact validation comparison with accepted R6: PASS, zero logit delta and zero prediction changes.

Supplementary evaluation used 302.224 seconds in a separate post-W6 ledger. No training or Official Test inference was performed. Keep R6 pending TV2 review.
