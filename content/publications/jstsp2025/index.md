+++
title = "Model-based learning for multi-antenna multi-frequency location-to-channel mapping"
authors = ["Baptiste Chatelier", "Vincent Corlay", "Matthieu Crussière", "Luc Le Magoarou"]
date = 2024-06-17
year = 2025
type = "journal"  # journal | conference | preprint
venue = "IEEE Journal of Selected Topics in Signal Processing"
venue_short = "JSTSP"
summary = "This paper studies the location-to-channel mapping learning in a multi-antenna multi-frequency setting."
image = "cover.jpg"

[links]  # paper, publisher, slides, code, video
paper = "https://arxiv.org/pdf/2407.07719"
publisher = "https://ieeexplore.ieee.org/document/10924768"
+++

Years of study of the propagation channel showed a close relation between a location and the associated communication channel response. The use of a neural network to learn the location-to-channel mapping can therefore be envisioned. The Implicit Neural Representation (INR) literature showed that classical neural architecture are biased towards learning low-frequency content, making the location-to-channel mapping learning a non-trivial problem. Indeed, it is well known that this mapping is a function rapidly varying with the location, on the order of the wavelength. This paper leverages the model-based machine learning paradigm to derive a problem-specific neural architecture from a propagation channel model. The resulting architecture efficiently overcomes the spectral-bias issue. It only learns low-frequency sparse correction terms activating a dictionary of high-frequency components. The proposed architecture is evaluated against classical INR architectures on realistic synthetic data, showing much better accuracy. Its mapping learning performance is explained based on the approximated channel model, highlighting the explainability of the model-based machine learning paradigm.

```bibtex
@ARTICLE{10924768,
  author={Chatelier, Baptiste and Corlay, Vincent and Crussière, Matthieu and Le Magoarou, Luc},
  journal={IEEE Journal of Selected Topics in Signal Processing}, 
  title={Model-Based Learning for Multi-Antenna Multi-Frequency Location-to-Channel Mapping}, 
  year={2025},
  volume={},
  number={},
  pages={1-16},
  keywords={Computer architecture;Neural networks;Machine learning;Signal processing;Channel estimation;Training;Channel models;Adaptation models;Complexity theory;Channel impulse response;Model-based machine learning;implicit neural representations;spectral bias;sparse representation;MIMO},
  doi={10.1109/JSTSP.2025.3549952}
}
```
