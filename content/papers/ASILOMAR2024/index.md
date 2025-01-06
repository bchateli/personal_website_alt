---
title: "CSI Compresion using Channel Charting" 
date: 2024-10-30
lastmod: 2024-12-20
# tags: ["philology","oleic science","history of oil","Mediterranean world"]
author: ["Baptiste CHATELIER","Vincent CORLAY","Matthieu CRUSSIERE","Luc LE MAGOAROU"]
# description: "This paper reviews the impact of phase noise on the array factor. Published in IEEE WCNC 2023" 
summary: "This paper presents how channel charting can be used to perform CSI compression in FDD MIMO systems. Published in IEEE ASILOMAR 2024." 
cover:
    image: "encoder_decoder_framework.png"
    alt: "Proposed CSI compression method"
    relative: false
editPost:
    URL: "https://arxiv.org/pdf/2501.01431"
    Text: "IEEE ASILOMAR"

---

---

##### Download

+ [Paper](https://arxiv.org/pdf/2501.01431)
+ [Slides](slides.pdf)

---

##### Abstract

Reaping the benefits of multi-antenna communication systems in frequency division duplex (FDD) requires channel state information (CSI) reporting from mobile users to the base station (BS). Over the last decades, the amount of CSI to be collected has become very challenging owing to the dramatic increase of the number of antennas at BSs. To mitigate the overhead associated with CSI reporting, compressed CSI techniques have been proposed with the idea of recovering the original CSI at the BS from its compressed version sent by the mobile users. Channel charting is an unsupervised dimensionality reduction method that consists in building a radio-environment map from CSIs. Such a method can be considered in the context of the CSI compression problem, since a chart location is, by definition, a low-dimensional representation of the CSI. In this paper, the performance of channel charting for a task-based CSI compression application is studied. A comparison of the proposed method against baselines on realistic synthetic data is proposed, showing promising results.

---

##### Figure 1: Overview of the proposed CSI compresssion scheme

![](encoder_decoder_framework.png)

---

##### Citation

```BibTeX
@misc{chatelier2024csicompressionusingchannel,
      title={CSI Compression using Channel Charting}, 
      author={Baptiste Chatelier and Vincent Corlay and Matthieu Crussière and Luc Le Magoarou},
      year={2024},
      eprint={2501.01431},
      archivePrefix={arXiv},
      primaryClass={cs.IT},
      url={https://arxiv.org/abs/2501.01431}, 
}

```

---