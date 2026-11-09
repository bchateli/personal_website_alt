+++
title = "Model-based learning for DoA estimation and array calibration via continuous sparse recovery"
authors = ["Baptiste Chatelier", "José Miguel Mateos-Ramos", "Vincent Corlay", "Matthieu Crussière",
"Christian Häger", "Henk Wymeersch", "Nir Shlezinger", "Luc Le Magoarou"]
date = 2026-11-06
year = 2026
type = "preprint"  # journal | conference | preprint
venue = "arXiv preprint"
venue_short = "arXiv"
summary = "This paper introduces a model-based learning method for joint DoA estimation and array calibration under severe gain-phase and antenna location impairments, handling coherent signals and requiring no labeled data."
image = "cover.png"

[links]  # paper, publisher, slides, code, video
paper = "https://arxiv.org/pdf/2611.09263"
+++

Direction of arrival (DoA) estimation, a classical signal processing problem, has experienced renewed interest with the advent of integrated sensing and communication (ISAC). While decades of research have yielded highly accurate DoA estimators, hardware impairments have frequently been neglected, despite degrading both DoA estimation accuracy and downstream communication performance in ISAC systems. This work introduces a joint array calibration and DoA estimation method based on the simultaneous orthogonal matching pursuit (SOMP) algorithm, following the model-based machine learning paradigm. The proposed method enables the calibration of antenna arrays subject to severe gain-phase and antenna location impairments through projected gradient descent (PGD), with either supervised or unsupervised objectives. Additionally, DoA estimation is enhanced by extending SOMP to continuous dictionaries via PGD refinement steps. Simulation results demonstrate that the proposed method enables efficient hardware impairment compensation, even without labeled samples, while outperforming conventional sparse recovery and subspace-based DoA estimation baselines.

```bibtex
@misc{chatelier2026modelbasedlearningdoaestimation,
      title={Model-based learning for DoA estimation and array calibration via continuous sparse recovery}, 
      author={Baptiste Chatelier and José Miguel Mateos-Ramos and Vincent Corlay and Matthieu Crussière and Christian Häger and Henk Wymeersch and Nir Shlezinger and Luc Le Magoarou},
      year={2026},
      eprint={2611.09263},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2611.09263}, 
}
```
