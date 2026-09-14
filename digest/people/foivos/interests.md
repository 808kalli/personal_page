# Research interests - Embedded Neural Networks for Battery Management Systems

PhD Focus: Development and validation of neural network models on microcontrollers with datasets aligned to real-world field conditions.

*Updated: September 2026*

---

## Core Research Direction

My PhD focuses on bridging the gap between laboratory testing and real-world deployment of battery management systems. The core challenge: laboratory datasets and synthetic cycles do not represent actual field conditions where battery management matters most. I develop and validate neural network models directly on resource-constrained microcontrollers, using datasets captured from real operating environments.

**Key thesis pillars:**
1. **Embedded Model Validation** - Testing and benchmarking neural networks ON microcontrollers (STM32, ARM Cortex, embedded platforms) rather than simulating performance
2. **Field-Aligned Datasets** - Datasets capturing real-world driving patterns, temperature variability, aging signatures, and duty cycles that differ fundamentally from standardized test profiles
3. **Hardware-Software Codesign** - Optimizing models for specific microcontroller architectures, memory constraints, computational budgets
4. **Deployment Reality** - Addressing the gap between published accuracy metrics and real-world BMS performance

---

## Core Research Areas (Highest Priority)

### Embedded TinyML for Battery State Estimation

**Neural networks validated on microcontroller hardware.** Not accuracy in simulation - actual deployment on STM32, ARM Cortex-M, automotive microcontrollers. Real-time SOC/SOH inference under computational and memory constraints. Quantization, pruning, and architecture optimization specifically for embedded targets. Testing inference latency, memory footprint, power consumption on actual hardware.

Key questions: Which model architectures actually fit on 256KB RAM? How does post-training quantization affect battery estimation accuracy in real cells? What is the latency/accuracy trade-off on specific MCU families?

### Real-World Battery Datasets vs. Laboratory Cycles

**Field-captured data that reflects actual usage patterns.** The disconnect between WLTP cycles, UDDS profiles, constant-current charging, and what vehicles/devices actually experience in the field. Real temperature variability (-20°C to 60°C swings), inconsistent charging patterns, realistic duty cycles, aged battery behavior.

Critical observation: Models trained on synthetic cycles fail catastrophically when deployed to real driving data. Need datasets that capture:
- Natural temperature cycling and thermal transients
- Realistic charge/discharge patterns (not standardized profiles)
- Multiple manufacturers and battery types in field conditions
- Aging signatures over 100+ charge cycles in real vehicles
- Edge cases: rapid DC charging, cold-weather performance, thermal runaway precursors

### Hardware-Aware Model Design

**Co-optimization of neural networks with embedded hardware constraints.** Not "train a model, then shrink it." Instead: design architectures knowing the target microcontroller from the start. Fixed-point arithmetic, binary/ternary networks where applicable, memory-efficient RNNs (GRU vs LSTM), depthwise separable convolutions.

Trade-offs matter: A model using 10% more memory might enable 2x faster inference, changing real-time feasibility. Embedded systems force hard decisions that research papers often avoid.

### Validation Methodology for Embedded Deployment

**From laboratory testing to field validation.** Validation protocols that move beyond benchmark metrics:
- Cross-validation across different battery chemistries and manufacturers
- Temperature stress testing on actual hardware over wide operating ranges
- Long-duration cycling studies (1000+ cycles) to assess aging model robustness
- Failure analysis: When and why does the embedded model break?
- Generalization studies: Does a model trained on Fleet A work on Fleet B?

Real question: What validation proves an embedded battery estimation model is safe for production deployment?

---

## Important Supporting Areas

### Data Collection and Preprocessing for Field Conditions

Practical challenges in capturing and processing real-world battery data:
- Telemetry systems that don't interfere with actual BMS operation
- Feature extraction from noisy sensor data (vehicle CAN bus, temperature sensors)
- Handling missing/corrupted data from field devices
- Normalization and alignment across heterogeneous hardware platforms

### Transfer Learning and Domain Adaptation

Models trained on one vehicle/battery type applied to another with minimal fine-tuning. Critical for cost-effective deployment: collect expensive labeled data once, transfer to many targets. Addressing battery chemistry differences (Li-ion → Na-ion), manufacturer variations, thermal environment shifts.

### Uncertainty Quantification for Safety-Critical Applications

Battery management cannot afford confident wrong predictions. Methods for:
- Confidence bounds on SOX estimates (Bayesian approaches, ensembles)
- Detecting out-of-distribution inputs (novel aging signatures, extreme conditions)
- Safe fallback strategies when model confidence drops
- Distinguishing model uncertainty from actual battery unpredictability

### Feature Engineering from Electrochemical Signatures

Extracting meaningful features for neural networks:
- Voltage curve features and their evolution with aging
- Current transient responses as diagnostic signatures
- Electrochemical impedance spectroscopy (EIS) integration
- Temperature-dependent feature normalization
- Time-series preprocessing: filtering, windowing, aggregation

### Microcontroller Architecture and Optimization

Hardware understanding essential for efficient deployment:
- ARM Cortex-M4/M7 SIMD capabilities for inference
- Memory hierarchy and DMA for data movement efficiency
- Floating-point vs fixed-point trade-offs
- Hardware accelerators (DSP, crypto units used for ML)
- Power profiling: Which operations consume most energy?

---

## Research Landscape & Key Publications

**People and groups doing embedded battery ML correctly:**

**Academic Leaders:**
- Spyridon Giazitzis - TinyML for battery state estimation, embedded microcontroller deployment
- Gregory Plett (Colorado School of Mines) - Battery state estimation foundations, adaptive algorithms
- Hosam Fathy (University of Michigan) - Real-world vehicle systems, practical BMS deployment

**Research Groups:**
- MIT Energy Initiative - Battery research with data-driven components
- Argonne National Laboratory - Battery testing, real-world cycling data
- UC San Diego Power Lab - Field data collection and validation
- Politecnico di Milano - Embedded systems and battery management
- University of Ferrara / UNIMORE - Real-world battery datasets and validation

**Key Publication Areas:**
- TinyML models for SOH estimation based on Electrochemical Impedance Spectroscopy
- Real-time SOC estimation with embedded neural networks on resource-constrained hardware
- Battery field data studies highlighting disconnect from laboratory cycles
- Embedded deployment and system-level validation frameworks
- Real-world datasets with driving cycles, temperature variation, aging

---

## Not Interested In

**Laboratory-only research.** Papers presenting models tested only in simulation or with synthetic data, claiming real-world applicability without field validation.

**Benchmark inflation without deployment reality.** +0.5% accuracy improvement on standardized cycles, tested on high-end GPUs, no discussion of embedded constraints.

**Theoretical NN papers applied to batteries as an afterthought.** Generic ML papers using battery datasets as one case study.

**Black-box applications with no mechanism.** Applying a standard architecture to battery data without understanding why it works or when it fails.

**Product announcements.** BMS product specs without technical depth or reproducible research.

---

## Research Values & Methodology

### Prefer:
- **Real over perfect.** A model that works 85% of the time on real field data beats one claiming 99% on synthetic cycles.
- **Failure analysis matters.** Papers acknowledging when and why models break are more valuable than those reporting only success metrics.
- **Hardware constraints explicit.** Stating inference latency, memory usage, power consumption on specific MCU platforms.
- **Reproducibility first.** Published code, datasets, clear preprocessing steps, exact hardware specifications.
- **Generalization proven.** Models tested across multiple battery manufacturers, chemistries, and field conditions - not one carefully selected dataset.

### Methodological quality signals:
- Real-world validation data collected independently from training data
- Long-duration cycling studies (1000+ cycles minimum)
- Cross-validation across different operating conditions and thermal environments
- Failure case analysis and model robustness discussion
- Clear statement of model limitations and applicability boundaries

---

## Open Research Questions (PhD Opportunities)

**Field datasets and benchmarking:**
- What open-source datasets best represent real-world battery operation? How do they differ from standard cycles?
- How can we collect representative field data at scale without overwhelming vehicles with telemetry?
- What constitutes a fair benchmark for embedded battery ML across different hardware platforms?

**Embedded optimization:**
- Which network architectures are fundamentally better for microcontroller deployment? (CNN vs RNN vs Transformer-lite)
- Can we design architecture search spaces that respect embedded constraints from the start?
- How much accuracy loss is acceptable when moving from float32 to int8 quantization for battery estimation?

**Real-world robustness:**
- How much training data from the field is needed to match the generalization of laboratory-trained models?
- Can we identify "distribution shift" when deployed models encounter new battery types or operating conditions?
- What validation proves an embedded model is safe for autonomous vehicle or grid-scale deployment?

**Hardware-software codesign:**
- Can fixed-point arithmetic be used for battery estimation without unacceptable accuracy loss?
- Which microcontroller peripherals (ADC characteristics, timing precision) most affect estimation performance?
- How do thermal variations in the MCU itself affect model inference in cold-weather vehicle operation?

---

## Suggested Research Directions (Feedback Welcome)

**Areas I'm exploring or should explore:**

1. **Open-source embedded battery datasets** - Creating curated, annotated field datasets from diverse vehicles and chemistries, freely available for reproducible research

2. **Embedded model validation framework** - Standardized testing protocols that move beyond accuracy metrics to deployment readiness (latency, robustness, thermal stability, generalization)

3. **Hardware-aware neural architecture search** - AutoML specifically for embedded targets, generating architectures optimized for specific microcontroller families while maintaining accuracy

4. **Transfer learning for battery chemistries** - Models trained on mainstream Li-ion that effectively adapt to emerging chemistries (Na-ion, solid-state) with minimal field data

5. **Physics-informed TinyML** - Incorporating electrochemical first principles into small neural networks, improving generalization across operating conditions

6. **Uncertainty quantification for embedded systems** - Lightweight confidence estimation (ensembles, dropout variants) that actually runs on microcontrollers, flagging uncertain predictions

7. **Multi-modal datasets** - Combining different sensor modalities (voltage, current, temperature, impedance) captured in the same real-world vehicles to improve model robustness

8. **Degradation mode classification** - Small networks identifying failure modes (calendar aging vs cycling wear, manufacturing defects) from embedded sensor data

---

## Connection to Broader Challenges

Embedded battery estimation connects to larger systems problems:
- **EV range anxiety** - Accurate SOC on 10-year-old packs, not just new cars
- **Grid storage reliability** - Predicting behavior of aged batteries in stationary storage
- **Circular economy** - Characterizing second-life batteries for automotive, stationary, or consumer applications
- **Safety** - Preventing thermal runaway through early detection of degradation signatures
- **Cost** - Reducing expensive sensors and computation by doing more with less data and less hardware

The dissertation will be evaluated by: (1) rigorous validation on real field data, (2) actual deployment on embedded hardware, (3) reproducible methods other researchers can build on, and (4) advancing practical battery management - not just metrics.

---

*Seeking papers, datasets, and collaborators in this space. Particularly interested in work validating on microcontroller hardware and datasets captured from real-world operating conditions.*
