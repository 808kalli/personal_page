# Research interests - Neural Networks in Battery Management Systems

This file documents my research focus. Updated regularly as interests evolve.
Be specific about what I *do not* want - it clarifies the search space.

## Core, rank these highest

**Neural Networks for SOX Estimation (SOC/SOH/SOF).** State-of-charge, state-of-health, 
and state-of-function estimation using neural networks. Focus on accurate prediction 
models that capture battery dynamics, aging patterns, and performance degradation. 
Particular interest in generalizable models that work across different battery chemistries 
and operating conditions.

**Model Distillation for Embedded Battery Management.** Knowledge distillation techniques 
to compress large neural network models into smaller, deployable architectures suitable 
for real-time inference on resource-constrained BMS hardware. Efficient architectures 
(MobileNets, SqueezeNets, TinyML variants) that maintain accuracy while reducing 
computational and memory footprint.

**Battery Derating Methods Linked to SOX Prediction.** Integration of neural network 
predictions into derating algorithms. How SOH and SOC estimates drive dynamic power/current 
limiting, thermal management, and cycle-life optimization. The feedback loop between 
accurate estimation and safe operational envelope definition.

**Neural Networks Integrated into Battery Management Systems.** Real BMS architectures 
that incorporate NNs for improved decision-making. Online learning, adaptive algorithms, 
and robust inference under extreme conditions (low temperature, degradation, limited 
computational resources).

**Lithium-Ion Battery NN Research.** Established chemistry with extensive research. Focus 
on papers proposing new mechanisms for SOX estimation, novel feature engineering approaches, 
or architectural innovations rather than incremental improvements on benchmarks.

**Solid-State and Emerging Battery Chemistries with NNs.** Transfer learning and domain 
adaptation for SOX estimation. How models trained on Li-ion translate to solid-state 
batteries, sodium-ion, and other emerging chemistries. Challenges of limited data for 
new battery types and generalization strategies.

**Sodium-Ion Batteries and SOX Estimation.** Emerging chemistry with different 
electrochemical signatures. NN models for Na-ion SOC/SOH, comparative analysis with 
Li-ion approaches, and the implications for BMS design.

**Small, Efficient NN Architectures for Battery Estimation.** TinyML, quantization, 
pruning, and architecture search specifically for SOX tasks. Edge ML on microcontrollers. 
The trade-off between model complexity, accuracy, latency, and power consumption.

## Important sub-topics

**Feature Engineering for Battery NNs.** Novel input representations that capture battery 
physics (voltage curves, current profiles, temperature effects, aging signatures). 
Mechanistic features versus learned representations. Time-series preprocessing and 
normalization strategies.

**Transfer Learning and Domain Adaptation.** Leveraging pre-trained models across battery 
types, chemistries, manufacturers. Addressing data scarcity for new applications.

**Uncertainty Quantification in Battery NNs.** Confidence bounds, Bayesian approaches, 
ensemble methods. Critical for safety-critical battery applications. Distinguishing aleatoric 
and epistemic uncertainty.

**Real-time Inference on Embedded Hardware.** ONNX, TensorFlow Lite, specialized accelerators 
for automotive/industrial BMS. Latency constraints and on-device optimization.

**Battery Physics-Informed Neural Networks (PINNs).** Incorporating electrochemical 
models into NN training. Hybrid approaches combining domain knowledge with data-driven learning.

## People and groups worth watching

Researchers and groups advancing NN-based battery management:

**Academic Leaders:** Gregory Plett (Colorado School of Mines) - battery state estimation 
foundations. Hosam Fathy (University of Michigan) - advanced vehicle management systems. 
Rajiv Malhotra - SOH estimation and machine learning. Yi Cui group (Stanford) - battery 
chemistry and characterization.

**Research Programs:** MIT Energy Initiative battery research. Argonne National Laboratory 
(ReaxFF, battery modeling). NREL Battery Research. UC San Diego Power Lab.

**Industry/Applied Focus:** Tesla Autopilot/Energy - real-world BMS at scale. 
Catl, LG Chem, Samsung SDI research on predictive battery management.

**Key References:** Papers on electrochemical impedance spectroscopy (EIS) with ML. 
Gaussian process approaches to SOH. Recurrent neural networks for temporal battery 
dynamics. Papers addressing real-world deployment challenges, not just simulation results.

## Interesting, but rank lower

**General machine learning improvements applied to batteries.** New optimization methods, 
attention mechanisms, or architectures, unless specifically designed with battery 
constraints in mind. Incremental benchmark improvements without mechanistic insight.

**Battery cycling data and dataset papers.** Unless they provide novel insights into 
NN model behavior or enable important comparisons across chemistries.

**Manufacturing and quality control with ML.** Important but outside core focus unless 
directly related to field performance prediction.

**Thermal management using NNs.** Relevant but secondary to SOX estimation.

## Not interested

**Pure chemistry papers without ML/NN component.** Unless they provide fundamental 
insights into aging mechanisms that inform model design.

**Marketing or product announcements.** BMS product specs without technical depth.

**Leaderboard racing.** Papers claiming SOTA without justifying why accuracy matters 
for real deployment. Benchmark inflation without practical constraints.

**Generic NN papers applied to batteries as one case study.** Unless the battery problem 
reveals something fundamental about the NN method.

**Surveys without novel framing.** Unless they synthesize the state of NN-based battery 
management in a way that changes understanding.

## Taste and methodology preferences

**Mechanism over metrics.** A paper explaining *why* an NN works for SOX estimation, 
or when it fails, beats one claiming +0.5% accuracy improvement.

**Real constraints acknowledged.** Papers that discuss actual hardware limitations, 
thermal conditions (-20°C to +60°C operation), aging over 1000+ cycles, and deployment 
challenges beat those with idealized lab conditions.

**Generalizable approaches.** Methods that transfer across battery types, manufacturers, 
or thermal conditions. Robustness and reliability paramount - a BMS failure is costly.

**Reproducibility and clarity.** Code available. Clear description of battery test conditions, 
preprocessing, train/val/test splits. How the model fails matters as much as where it succeeds.

**Negative results valued.** "This distillation approach failed on real hardware" or 
"This model doesn't generalize to aged cells" is more useful than incremental success claims.

**Physics-informed thinking.** Understanding electrochemistry and BMS constraints improves 
model design. Not required to read papers, but respected when present.

## Suggestions for improvement

I'm open to your insights! Potential areas to explore:

- **Federated learning for BMS:** Distributed training across fleet data without sending 
  raw cell data to cloud. Privacy-preserving model updates.
  
- **Causal inference in degradation:** Beyond correlative prediction - understanding which 
  factors *cause* SOH changes. Important for intervention and control strategies.
  
- **Active learning for battery systems:** Adaptive testing strategies that minimize cycle 
  count needed to train accurate SOX models. Data-efficient learning crucial given battery 
  costs.
  
- **Explainability for safety:** Which NN outputs are trustworthy? Interpretability methods 
  specific to battery domains where knowing *why* the model predicted low SOH enables better 
  maintenance decisions.
  
- **Graph neural networks for battery packs:** Multi-cell systems where individual cell 
  state couples through shared thermal/electrical networks. GNNs for pack-level estimation.

---

*Last updated: September 2026*
*Focus: Neural networks for embedded, real-time battery state estimation and management*
