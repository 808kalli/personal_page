# Reading interests

This file is the ranking prompt. Edit it whenever your taste shifts, the next
run picks it up. Be specific about what you do *not* want, it does more work
than the positive list.

## Core, rank these highest

**Mechanistic interpretability.** Features, circuits, superposition, sparse
autoencoders, attribution graphs and circuit tracing, activation steering.
Work in the lineage of Anthropic's transformer-circuits publications.

**Interpretability of robot policies.** The same questions asked of embodied
models rather than language models. What a Vision Language Action model
represents internally, whether it has built a world model of its environment,
whether internal features can be probed, read off, and intervened on to steer
behaviour without fine tuning.

**Why policies learned from demonstrations fail at deployment.** Test time
distribution shift, compounding error, the non-Markovian structure of human
demonstration data, action chunking and why it helps, expressivity mismatches
between the data and the policy class.

**Foundations and scaling questions with a real argument.** What actually
drives generalisation in pre-training, whether scale dissolves a problem or
hides it, calibration and error accumulation over long generations. The Bitter
Lesson is a touchstone here.

**Robot learning data.** Turning unstructured behavioural data (human video,
motion capture, teleoperation, simulation) into usable robot supervision.
Embodiment transfer, reward inference from video and language.

**Interpretability used for oversight.** Probes and steering vectors as tools
for telling what a model is doing or making it do something else, and honest
work on where those tools break. Whether a steering vector generalises, or is
really a property of the dataset rather than the model. Whether a probe that
scores well in distribution survives a prompt change.

## People and groups worth watching

These are markers of taste, not a whitelist. Work from the same corner of the
field counts just as much, and a paper is not interesting because of who wrote
it. Use them to recognise the neighbourhood.

FAR AI, and Adria Garriga-Alonso in particular. The UCL AI Centre group around
Robert Kirk, David Chanin, and Daniel Tan. Dimitrios Kanoulas at UCL and
Archimedes for robot learning. Anthropic's interpretability team. Neel Nanda
and the DeepMind mechanistic interpretability group. David Bau's lab. Redwood
Research, Apollo Research, EleutherAI, Goodfire, Transluce.

The 2024 paper "Analysing the Generalisation and Reliability of Steering
Vectors" is the centre of gravity here: an interpretability technique taken
seriously enough to find out when it fails.

## Interesting, but rank lower

Reinforcement learning method papers, especially off policy and offline RL,
when they carry an insight rather than a benchmark number. Evaluation
methodology. Negative results and papers that overturn a common explanation.

## Not interested

Applications with no mechanism (a known method applied to a new dataset).
Leaderboard papers whose contribution is a number. LLM agent frameworks,
prompt engineering, RAG pipelines, and multi agent product work. Surveys,
unless the survey itself proposes a framing. Anything whose main claim is that
it is bigger.

## Taste

Prefer a paper that changes how something is understood over one that improves
a metric. A clearly stated negative result beats a marginal positive one. A
good blog post from someone who does the work counts as much as a conference
paper.
