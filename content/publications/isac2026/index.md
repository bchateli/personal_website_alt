+++
title = "Online Array Calibration via Bayesian Tracking"
authors = ["Sivan Grotas Mussan", "José Miguel Mateos-Ramos", "Baptiste Chatelier", "Luc Le Magoarou", "Christian Häger", "Henk Wymeersch", "Nir Shlezinger"]
date = 2026-09-14
year = 2026
type = "conference"  # journal | conference | preprint
venue = "IEEE Conference on Integrated Sensing and Communications"
venue_short = "ISAC 2026"
summary = "This paper presents a Bayesian tracking approach in a DoA estimation problem with hardware impairments."

[links]  # paper, publisher, slides, code, video
+++

DoA estimation is a key array-processing task, with existing methods typically relying on accurate knowledge of the array response. Calibration mismatches  can thus severely degrade DoA recovery, and existing calibration techniques struggle with rapid calibration drifts when only few snapshots are available and no labeled data is provided. We propose a rapid unsupervised online calibration framework that casts drifting array calibration as a state-estimation problem. The proposed method jointly tracks the source directions and calibration parameters over time, exploiting temporal structure rather than recalibrating each time block independently. We develop two state-space formulations: one using the empirical covariance matrix as the observation, and another based on  subspace orthogonality, avoiding  knowledge of the source and noise statistics. Both formulations are solved using few-step iterated extended Kalman filtering, yielding low-complexity recursive calibration from unlabeled measurements. Numerical results show that the proposed dynamic-system-based approach enables accurate DoA estimation under fast calibration variations and limited snapshots.
