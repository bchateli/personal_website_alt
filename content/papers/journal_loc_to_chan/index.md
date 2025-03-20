---
title: "Model-based learning for multi-antenna multi-frequency location-to-channel mapping" 
date: 2024-06-17
lastmod: 2024-06-17
# tags: ["philology","oleic science","history of oil","Mediterranean world"]
author: ["Baptiste CHATELIER","Vincent CORLAY", "Matthieu CRUSSIERE", "Luc LE MAGOAROU"]
# description: "This paper reviews the impact of phase noise on the array factor. Published in IEEE WCNC 2023" 
summary: "This paper studies the location-to-channel mapping learning in a multi-antenna multi-frequency setting. Preprint." 
cover:
    image: "real_reconstruct_with_freq.png"
    alt: "Reconstructions"
    relative: false
editPost:
    URL: "https://arxiv.org/pdf/2407.07719"
    Text: "Published in IEEE Journal of Selected Topics in Signal Processing"

---

---

##### Download

+ [Paper](https://arxiv.org/pdf/2407.07719)

---

##### Abstract

Years of study of the propagation channel showed a close relation between a location and the associated communication channel response. The use of a neural network to learn the location-to-channel mapping can therefore be envisioned. The Implicit Neural Representation (INR) literature showed that classical neural architecture are biased towards learning low-frequency content, making the location-to-channel mapping learning a non-trivial problem. Indeed, it is well known that this mapping is a function rapidly varying with the location, on the order of the wavelength. This paper leverages the model-based machine learning paradigm to derive a problem-specific neural architecture from a propagation channel model. The resulting architecture efficiently overcomes the spectral-bias issue. It only learns low-frequency sparse correction terms activating a dictionary of high-frequency components. The proposed architecture is evaluated against classical INR architectures on realistic synthetic data, showing much better accuracy. Its mapping learning performance is explained based on the approximated channel model, highlighting the explainability of the model-based machine learning paradigm.

---

##### Figure 5: Real part of reconstructed channel over a $2.5$m by $2.5$m zone.

![](real_reconstruct_with_freq.png)

---

##### Citation

```BibTeX
@misc{chatelier2024modelbasedlearningmultiantennamultifrequency,
      title={Model-based learning for multi-antenna multi-frequency location-to-channel mapping}, 
      author={Baptiste Chatelier and Vincent Corlay and Matthieu Crussière and Luc Le Magoarou},
      year={2024},
      eprint={2407.07719},
      archivePrefix={arXiv},
      primaryClass={cs.IT},
      url={https://arxiv.org/abs/2407.07719}, 
}
```

---