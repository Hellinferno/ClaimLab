# Making ClaimLab's LLM tutor direct, detailed and pedagogically effective, and how AI tutors are evaluated

Scope note: researched 2026-10-31. Classic learning-science sources are 2003-2017. Most LLM-tutoring evidence is 2023-2025, plus a few 2026 benchmark papers that I read only at abstract level. Evidence quality is labelled inline as **[meta-analysis]**, **[RCT/field experiment]**, **[benchmark/peer-reviewed NLP]**, **[preprint]** or **[vendor claim/press]**.

---

## Q1. Which learning-science principles should shape the explanations and checks, and how do they map onto paged steps, the whiteboard and check questions?

### Takeaway
The strongest evidence supports three things: (1) worked examples for novices, faded as competence grows (expertise reversal); (2) retrieval practice with *elaborated* feedback, meaning an explanation of why rather than "correct/incorrect"; and (3) Mayer's extraneous-load principles (coherence, signaling, contiguity, segmenting). ClaimLab's paged steps already implement segmenting, and its whiteboard is a dual-coding channel. The weakest link is the check/feedback loop. Elaborated, misconception-targeted feedback beats knowledge-of-result by roughly 10x in effect size (0.49 vs 0.05).

### Cited Findings
**Worked examples, fading and expertise reversal**
- The worked-example effect is a cognitive-load-theory prediction: studying worked solutions beats unguided problem solving for novices. The benefit shrinks or reverses as prior knowledge grows (the expertise reversal effect). Studies of expertise reversal find worked examples most effective when fading is tailored to the individual learner — [Wikipedia: Worked-example effect](https://en.wikipedia.org/wiki/Worked-example_effect); [Wikipedia: Expertise reversal effect](https://en.wikipedia.org/wiki/Expertise_reversal_effect)
- Proposed fading sequence: complete examples, then increasingly incomplete examples, then unsolved problems. In electrical-circuit studies, fading reliably helped near transfer but not far transfer — [Atkinson/Renkl papers (ASU)](https://asu.academia.edu/RobertAtkinson); [ASU faculty PDF](https://faculty.engineering.asu.edu/mre/wp-content/uploads/sites/31/2020/02/1124_final.pdf)
- Fading pace interacts with prior knowledge. High-prior-knowledge learners did worse under a slow fading schedule, and low-prior-knowledge learners did better under it — [Learner Achievement under Different Paces of Transitioning to Independent Problem Solving](https://karlsmithmn.org/?p=1488)
- Boundary condition: in a less-structured domain (law), worked examples were efficient for both novices and advanced students — [Wikipedia: Worked-example effect](https://en.wikipedia.org/wiki/Worked-example_effect). This matters because research-paper reasoning is semi-structured.

**Retrieval practice and elaborative interrogation (Dunlosky et al. 2013, PSPI review, older but still the standard reference)**
- Of 10 techniques, only practice testing and distributed practice were rated **high utility**. Interleaved practice, elaborative interrogation and self-explanation were rated **moderate**. Practice testing's benefits generalize across ages, abilities and criterion tasks — [Duke faculty database entry](https://fds.duke.edu/db/aas/pn/faculty/emarsh/publications/252743); [Notre Dame Kaneb summary](https://sites.nd.edu/kaneb/?p=1307)
- Elaborative interrogation (generating an explanation of *why* a fact is true) and self-explanation were rated moderate because the evidence base was thin, especially in real educational contexts, not because they were shown to be ineffective — [Texas LD Center summary](https://texasldcenter.org/?p=346); [Kaufman summary](https://scottbarrykaufman.com/study-alert-improving-students-learning-with-effective-learning-techniques-from-cognitive-and-educational-psychology)

**Feedback after wrong answers [meta-analysis]**
- Van der Kleij, Feskens & Eggen (2015, *Review of Educational Research*): 40 studies, 70 effect sizes on item-based computer feedback. **Elaborated feedback (an explanation) ES = 0.49, knowledge of correct response (KCR) = 0.32, knowledge of result/correctness only (KR) = 0.05.** EF was especially superior for higher-order outcomes, and delayed feedback weakened effects — [ACU Research Bank](https://acuresearchbank.acu.edu.au/item/86y84/effects-of-feedback-in-a-computer-based-learning-environment-on-students-learning-outcomes-a-meta-analysis)
- Mertens, Finn & Lindner (2022) network meta-analysis: elaborated feedback is most likely the most effective variant for both lower-order (recall/recognition) and higher-order (transfer) outcomes — [IPN Leibniz](https://www.leibniz-ipn.de/en/research/publications/effects-of-computer-based-feedback-on-lower-and-higher-order-learning-outcomes)

**Multimedia / dual coding (Mayer)**
- Mayer (2017, *J. Computer Assisted Learning*) reports, for reducing extraneous processing: coherence d = 0.70, signaling d = 0.46, redundancy d = 0.87, spatial contiguity d = 0.79. For managing essential processing: segmenting d = 0.70, pre-training d = 0.46, modality d = 0.72. Several principles are stronger for low- than high-knowledge learners — [Zendy record of Mayer 2017](https://zendy.io/title/10.1111/jcal.12197)
- The Cambridge Handbook (2014) gives somewhat different medians: coherence 23/23 tests, median d = 0.86; signaling 24/28, d = 0.41; redundancy 16/16, d = 0.86; temporal contiguity 9/9, d = 1.22. **The two sources conflict on exact values**, so treat them as "moderate-to-large", not precise figures — [Cambridge Handbook chapter](https://resolve-he.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/CD5B7AE1279A9AB81F8EEBB53DBEC86E); [Dartmouth summary of 12 principles](https://services.dartmouth.edu/TDClient/1806/Portal/KB/PrintArticle?ID=171655)

**Active engagement (ICAP)**
- Chi & Wylie (2014) ICAP predicts learning rises from Passive to Active to Constructive to Interactive engagement, defined by overt behaviour. Support comes from studies of note-taking, concept mapping and self-explaining — [Chi & Wylie 2014 PDF](https://chilab.asu.edu/sites/default/files/lcl/chiwylie2014icap_2.pdf)
- This is contested. One experiment found passive learners performed best, and argued that boundary conditions (task complexity, learner preparedness) matter — [TOJET article](https://www.tojet.net/articles/v23i2/2322.pdf)

**Productive failure (problem-solving before instruction)**
- Sinha & Kapur (2021, *RER*) meta-analysed 53 studies and 166 comparisons of PS-I vs I-PS. After a publication-bias adjustment, summaries report an estimated true effect of g = 0.87 favouring PS-I, with larger effects under high-fidelity designs. An earlier 12-article review found g = 0.43 — [X-MOL record](https://www.x-mol.com/paper/1406031499744456704); [phys.org](https://phys.org/news/2021-09-productively-wiser.html). **Flag:** I did not verify the unadjusted estimate. A secondary write-up notes two randomized experiments with the opposite result — [techlearning](https://techlearning.com/news/study-productive-failure-a-success-in-education). The benefits are for conceptual knowledge and transfer, and depend on carefully designed activation problems.

### Inferences
Mapping to ClaimLab, each with a testable form:
- **Paged steps = segmenting principle.** Keep learner-paced "next", 2-5 sentences per step. Brevity does not cause abstraction; the absence of a worked example does. Rule: **at least one step per turn must be a worked example using the paper's own numbers/variables** (for example, plug Table 2 values into Eq. 3). *Test:* code check that some step contains at least 2 numeric tokens that appear in the selected pages' text.
- **Pre-training principle.** When the answer depends on more than 2 unfamiliar named components, define them (name + one-line role) in step 1 or 2, before the mechanism. *Test:* every capitalized/technical term used in later steps is defined earlier or tagged `background`.
- **Coherence.** No decorative board objects. Every board object must be referenced by its step text, and every step must have at most one "new idea". *Test:* every board object ID is referenced in its step's text; LLM-judge "no irrelevant information" (a LearnLM rubric item, see Q4).
- **Signaling + spatial contiguity.** Arrow labels sit on the arrow; equation annotations sit adjacent to the term. The step text should name the box/arrow it is talking about ("the arrow labelled 'reweights'").
- **Temporal contiguity.** Reveal a step's drawings at the same moment as its text, not all upfront.
- **Redundancy.** The board holds keywords, equations, verbatim quotes and plots, not the step's sentences repeated. *Test:* n-gram overlap between step text and board text stays below a threshold, excluding quotes.
- **Retrieval practice (high utility).** Keep the end-of-turn check. Add a **delayed re-check**: when a learner returns to a paper or concept, re-ask a new variant of an earlier check (distributed practice is also rated high utility).
- **Elaborative interrogation.** Use "why does the paper's result follow from X?" as the free-text check type, and use it sparingly, since it is the latency-heavy format.
- **Elaborated feedback.** A bare "Incorrect, try again" (KR, ES of about 0.05) is nearly useless. The remediation turn must say *what* is wrong, *why*, and *what to do next* (see Q5 for the misconception map).
- **Expertise reversal → fading.** Tie the fading level to ClaimLab's existing evidence categories. At `introduced`/`needs_check`, give a full worked example. At `supported_with_help`, give a partially worked example and ask the learner to complete one step. At `supported_independently`, give a short answer plus the source pointer, with no worked example (it becomes redundant and can hurt). *Test:* for scripted learners at each mastery level, count worked-example steps; they should decrease monotonically.

### Gaps
- I did not retrieve meta-analytic effect sizes for retrieval practice (for example Rowland 2014, Adesope et al. 2017). Only the Dunlosky qualitative ratings are sourced here.
- Almost all of this evidence comes from K-12/undergraduate STEM or short multimedia lessons. I found no studies on adult researchers learning from primary research papers.
- Mayer's modality principle concerns spoken narration and does not transfer directly to ClaimLab's text-only steps.

---

## Q2. Answer-first or Socratic/withholding for adult self-learners reading papers? When should the tutor answer directly and when should it scaffold?

### Takeaway
The evidence does not support blanket withholding for an information-seeking question. The documented harm from "answer-giving" AI comes from the AI *doing the practice* for the learner (Bastani et al.). Worked-solution help itself produces learning gains (Pardos & Bhandari), and novices learn more from worked examples than from unguided search (cognitive load theory). Best fit for ClaimLab: **answer the paper question directly with a worked example, then withhold only inside the check/remediation loop** (hint first, reveal with explanation after repeated misses), and fade support as mastery evidence accumulates.

### Cited Findings
- **Bastani et al. (PNAS 2025) [field experiment, about 1,000 Turkish high-school math students]:** "GPT Base" (a ChatGPT-like interface) improved practice performance. When access was later removed, those students did worse than students who never had access (**17% reduction in grades**). "GPT Tutor", with prompts designed to safeguard learning, largely mitigated the harm — [Wharton Knowledge](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education); [IDEAS/RePEc](https://ideas.repec.org/a/nas/journl/v122y2025pe2422633122.html). Limits: one school, one subject, four 90-minute sessions — [critique (opinion piece)](https://liveinthefuture.org/stories/ai-makes-students-worse)
- **Kestin et al. (Scientific Reports 2025) [crossover RCT, 194 Harvard physics undergrads]:** the AI tutor (GPT-4, "PS2 Pal") beat in-class active learning, with median post-test 4.5 vs 3.5 and "more than twice" the learning gain. Median time was about 49 min vs 75 min, and engagement 4.1 vs 3.6 out of 5 — [Hechinger Report](https://hechingerreport.org/?p=103689); [AIED Research summary](https://aiedresearch.substack.com/p/ai-tutoring-outperforms-active-learning). Its prompt was only about two paragraphs and included "Only give away ONE STEP AT A TIME, DO NOT give away the full solution in a single message", "Keep responses BRIEF (a few sentences or less) but helpful", "Assume no prior knowledge", and encourage the student to "give it a try first" — [AIED Research summary](https://aiedresearch.substack.com/p/ai-tutoring-outperforms-active-learning). Caveats: single course, short term, provocative title — [etcjournal review](https://etcjournal.com/2025/11/10/review-of-kestin-et-al-s-june-2025-harvard-study-on-ai-tutoring/)
- **Pardos & Bhandari (PLoS ONE 2024) [RCT, N = 274]:** ChatGPT-generated worked-solution help was the only condition with statistically significant learning gains over a no-help control. It did not differ significantly from human-tutor-authored help in gains or time-on-task — [PMC full text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11125466/). Their earlier 2023 preprint (N = 77) had found human hints better — [arXiv 2302.06871](https://arxiv.org/pdf/2302.06871). The two results conflict, and the 2024 version is more rigorous.
- **Google LearnLM arena (2025):** "what students find immediately helpful often diverges from what is pedagogically sound." Its rubric includes "Guides to answer" (don't give answers away too quickly), and experts penalised models that bypassed the learning process — [arXiv 2505.24477](https://arxiv.org/html/2505.24477v1)
- **LearnLM-Tutor (2024) participatory workshops with learners/educators:** "Do not give away solutions prematurely. Encourage learners to come up with solutions." — [arXiv 2407.12687](https://arxiv.org/html/2407.12687v4)
- **Google/Eedi exploratory RCT (Dec 2025) [preprint, N = 165, UK Year 9-10]:** LearnLM, supervised by a human tutor who approved 76.4% of drafted messages with zero or minimal edits, performed at least as well as human tutors. LearnLM students were 5.5 pp more likely to solve novel problems on later topics (66.2% vs 60.7%) — [arXiv 2512.23633](https://arxiv.org/abs/2512.23633v1). This is an exploratory, small trial, and the authors flag cross-condition contamination.
- Expertise reversal: guidance that helps novices becomes redundant for knowledgeable learners — [Wikipedia: Expertise reversal effect](https://en.wikipedia.org/wiki/Expertise_reversal_effect)
- Productive failure favours problem-first designs for conceptual knowledge and transfer, but only with deliberately designed activation problems (see Q1) — [phys.org](https://phys.org/news/2021-09-productively-wiser.html)

### Inferences
- In Bastani and Kestin, the "don't give answers" rule applied to **practice problems the learner was supposed to solve**. A ClaimLab learner asking "what does the paper claim about X and why?" has an information need, which is closer to studying a worked example. Withholding the answer there adds extraneous load and drives the "not to the point" complaint. **Recommendation: answer-first (BLUF) for explanation turns; Socratic/withholding for check and remediation turns.**
- Decision rule the agent can apply (code-selectable mode, not left to the model):
  1. *Question is "what/which/where does the paper say"* → answer directly in step 1 with a source quote.
  2. *Question is "why/how does it follow / derive / would it still hold if"* → step 1 states the answer, steps 2-4 give a worked example in the paper's numbers, and the check asks the learner to apply it to a changed case (a near-transfer variant).
  3. *Learner already at `supported_with_help` on this concept* → faded example: leave one step blank and ask the learner to fill it.
  4. *Optional "predict first" (productive-failure-lite)*: for experiment-driven turns, ask the learner to predict the plot's shape before the sandbox result is drawn. This costs one cheap MCQ and no LLM grading.
- Remediation ladder after a wrong check answer (draws on Kestin's "one step at a time", MRBench's "don't reveal", and Van der Kleij's EF > KCR > KR):
  1. 1st miss: name the specific error and give a targeted hint, without revealing the answer, then pose a **new variant**.
  2. 2nd miss: reveal the answer *with* a worked explanation (elaborated feedback), then pose another new variant later.
  3. Never repeat the same item.
- *Test:* on scripted wrong-answer scenarios, measure "answer revealed on 1st miss" (target below 10%) and "elaborated explanation present on 2nd miss" (target above 95%).

### Gaps
- No study I found tests answer-first vs Socratic tutoring specifically for adults reading research papers. All the RCTs are K-12 or undergraduate STEM problem-solving.
- I could not verify whether Kestin's tutor prompt contained instructor-written step-by-step solutions. The Nature page redirected to a login, and the summaries do not say.

---

## Q3. How do LearnLM, Khanmigo, Duolingo Max, OpenAI study mode and Anthropic's learning mode structure tutoring, and what principles or rubrics do they publish?

### Takeaway
Every major vendor mode is mostly **prompt/system-instruction level** and converges on the same five principles: manage cognitive load, active learning, metacognition, curiosity/motivation, and adaptivity. Vendors openly admit run-to-run inconsistency (OpenAI) and instruction-dropping in long prompts (Khan Academy). Only Google has published detailed rubrics and learning-outcome trials. ClaimLab can beat prompt-only designs by enforcing structure in code.

### Cited Findings
**Google LearnLM (most transparent; tech reports 2024-2025, RCT preprint Dec 2025)**
- LearnLM-Tutor's high-level pedagogy rubric prioritises five principles: encourage active learning, manage cognitive load, deepen metacognition, motivate and stimulate curiosity, and adapt to learners' goals and needs. Its automatic-eval dimensions are: stay on topic, don't reveal the answer, guide towards the answer, promote active engagement, identify and address misconceptions, respond appropriately to affect cues, positive tone, adapt to learner's level. Tutoring is "grounded in lesson materials that are shared between the tutor and the learner" (educational YouTube videos) — [arXiv 2407.12687](https://arxiv.org/html/2407.12687v4)
- LearnLM-Tutor turn-level factuality: about 93% of fact-containing turns were rated "Fully verified" vs about 96% for base Gemini 1.0 (not significant). The only significant learner-reported gain was confidence in applying the material later, with small n (27-33) — [arXiv 2407.12687](https://arxiv.org/html/2407.12687v4)
- "LearnLM: Improving Gemini for Learning" frames the approach as **pedagogical instruction following**: system-level instructions describe the desired teaching behaviour, and the model is trained to follow them — [arXiv 2412.16429](https://arxiv.org/html/2412.16429v3)
- **Arena rubric (25 items, 5 principles)**, the most directly reusable artifact:
  - *Manages cognitive load:* appropriate response length, manageable chunks, straightforward response, no irrelevant information, analogies, information presentation, information order, no repetition, no contradiction.
  - *Inspires active learning:* opportunities for engagement, asks questions, guides to answer, active engagement.
  - *Deepens metacognition:* guide mistake discovery, constructive feedback, acknowledge correctness, communicates plan.
  - *Stimulates curiosity:* stimulates interest, adapts to affect, encouraging feedback.
  - *Adapts to learner:* leveling, unstuck, adapts to needs, proactive, guides appropriately.
  - Source: [arXiv 2505.24477, Appendix A](https://arxiv.org/html/2505.24477v1)

**OpenAI ChatGPT study mode (launched 29 July 2025) [vendor claim/press]**
- Built on custom system instructions written with teachers, scientists and pedagogy experts. It targets active participation, managing cognitive load, metacognition, curiosity and feedback, using Socratic questioning, hints and self-reflection prompts, and adapts to skill level using memory. OpenAI acknowledged that the system-instruction approach "may result in inconsistent behavior and mistakes across conversations" and said it plans to train the behaviour into its main models. No outcome results were published at launch (research with Stanford SCALE was planned) — [OpenAI announcement](https://openai.com/index/chatgpt-study-mode/) (returned 403 to my fetcher, so details are via the search summary); [The Decoder](https://the-decoder.com/openai-launches-study-mode-for-chatgpt-while-education-users-are-told-to-wait-and-learn-later/); [CO/AI](https://getcoai.com/news/chatgpts-new-study-mode-transforms-ai-from-answer-machine-to-tutor)

**Anthropic Claude for Education "Learning mode" (April 2025) [vendor claim/press]**
- Socratic prompts such as "How would you approach this problem?" and "What evidence supports your conclusion?". It highlights fundamental principles behind problems and provides templates (research-paper outlines, study guides) — [Engadget](https://engadget.com/ai/claudes-new-learning-mode-will-prompt-students-to-answer-questions-on-their-own-172057828.html); [VentureBeat](https://venturebeat.com/ai/anthropic-flips-the-script-on-ai-in-education-claude-learning-mode-makes-students-do-the-thinking); [Maginative](https://www.maginative.com/article/anthropic-launches-claude-for-education-with-learning-mode-to-foster-critical-thinking-in-universities/)
- Reported as on by default for Claude for Education users as of Feb 2026 — [Educators Technology](https://www.educatorstechnology.com/2026/02/claude-for-education.html). I found little published outcome evidence — [InfoQ](https://www.infoq.com/news/2025/04/claude-for-education)

**Khan Academy Khanmigo (GPT-4; posts are 2023-24, older) [vendor]**
- 7-step prompt process: envision the ideal tutor interaction, consult learning science (meet students where they are, prompt self-explanation), integrate the content library, craft tone and question types with guardrails, test with diverse personas, safety, iterate on user feedback. **Users complained Khanmigo repeated itself, so prompts were rewritten to avoid repeated questions and use more concise language.** Pilot users found emojis offensive on serious topics — [Khan Academy blog](https://blog.khanacademy.org/khan-academys-7-step-approach-to-prompt-engineering-for-khanmigo)
- Khan Academy reported that "when prompts get to be too long, the model starts randomly ignoring different parts of the instructions" (via Khan's Portuguese blog/interview summaries; secondary) — [Khan Academy PT blog](https://blog.khanacademy.org/pt-br/?p=19535); [Teaching Channel podcast with K. DiCerbo](https://www.teachingchannel.com/k12-hub/podcast/teaching-channel-talks-episode-95-how-khan-academy-is-taking-ai-to-the-next-level-in-education-with-dr-kristen-dicerbo/)

**Duolingo Max (March 2023; launch-era, older) [vendor]**
- "Explain My Answer" gives a GPT-4 explanation of why an answer was right or wrong, with follow-up on request. "Roleplay" is a scenario chat that ends with feedback on accuracy and complexity. Duolingo said it "constantly review[s] AI-generated explanations ... to ensure that the answers are factually correct and have the right tone". OpenAI's case study notes one wrong term could teach a concept incorrectly — [Duolingo blog](https://blog.duolingo.com/duolingo-max); [OpenAI customer story](https://openai.com/customer-stories/duolingo); [TechRadar](https://www.techradar.com/news/duolingos-new-gpt-4-ai-will-happily-explain-why-your-spanish-is-wrong)

### Inferences
- **Khanmigo's repetition problem is exactly ClaimLab's repeated-check-question problem.** Khan fixed it in the prompt. ClaimLab should fix it in code (variant IDs plus a dedupe check; see Q5), because OpenAI admits prompt-only behaviour is inconsistent.
- Duolingo's "Explain My Answer" is a direct template for ClaimLab's wrong-answer turn: explain why *this* answer is wrong, then offer more on request.
- Adopt Google's 25-item rubric (lightly adapted) as ClaimLab's judge rubric. It is the only published, expert-validated pedagogy rubric among these vendors, and items like "straightforward response", "information order", "no repetition" and "no irrelevant information" directly operationalize the user's "not to the point" complaint.
- The vendors' shared Socratic-by-default stance is tuned for homework help by students, where cheating is the risk. ClaimLab's user is a self-directed adult; see Q2 for why answer-first fits better.

### Gaps
- I found no published learning-outcome evaluation for OpenAI study mode, Claude learning mode, Khanmigo or Duolingo Max (vendor claims only). Google/Eedi is the exception.
- The full text of OpenAI's study-mode page was not retrievable (403). I also did not check Anthropic's own announcement page for exact wording.

---

## Q4. Which benchmarks and evaluations exist for LLM tutoring quality, what do they score, and how could a small team build a lightweight harness for ClaimLab?

### Takeaway
The field scores tutor turns on roughly 8 dimensions: mistake identification, mistake location, not revealing the answer, guidance, actionability, coherence, tone, human-likeness (MRBench). Google's 25-item pedagogy rubric covers whole conversations. A consistent finding: **solving ability does not imply teaching ability**, and **small/open LLM judges correlate poorly (even negatively) with human raters on pedagogical dimensions**. A small team should combine deterministic code checks, a per-dimension LLM judge calibrated on about 50-100 human-labelled turns, scripted simulated learners, and repeated sampling to measure variance.

### Cited Findings
- **MRBench / "Unifying AI Tutor Evaluation" (Maurya et al., NAACL 2025) [peer-reviewed]:** 192 conversations and 1,596 responses from 7 LLM tutors plus novice and expert humans, built on MathDial and Bridge — [arXiv 2412.09416](https://arxiv.org/html/2412.09416v2); [MBZUAI](https://mbzuai.ac.ae/news/tutors-of-tomorrow-a-new-benchmark-for-evaluating-llms/). Dimensions, with the desired label in brackets:
  - mistake identification [Yes]
  - mistake location [Yes]
  - revealing of the answer [No]
  - providing guidance (correct, relevant hint, explanation or example) [Yes]
  - actionability (clear what the student should do next) [Yes]
  - coherence with prior turns [Yes]
  - tutor tone [Encouraging]
  - human-likeness [Yes]
  - Labels are Yes / To some extent / No.
  - Results: GPT-4 revealed the answer about 47% of the time, Sonnet avoided revealing it 94.79% of the time, and expert humans had the best actionability (76.04%). Most LLMs had a neutral rather than encouraging tone. **Prometheus2 and Llama-3.1-8B judges showed mostly negative correlations with human annotations.** Human inter-annotator agreement: Cohen's kappa = 0.71 — [arXiv 2412.09416](https://arxiv.org/html/2412.09416v2)
- **BEA 2025 shared task** adopted four dimensions (mistake identification, mistake location, guidance, actionability) and released MRBench V3 (300 dev / 191 test dialogues) — [MRBench search summary / ACL BEA 2025](https://preview.aclanthology.org/acl25-workshop-ingestion/2025.bea-1.84.pdf)
- **MathTutorBench (Macina et al., EMNLP 2025 oral) [peer-reviewed]:** three task groups. Math expertise and student understanding (verify, locate and correct student solutions) use standard metrics. Teacher response generation (scaffolding) is scored by a **reward model trained to prefer effective tutor utterances**. Finding: "subject expertise ... does not immediately translate to good teaching". There is a trade-off between expertise and pedagogy, and most models are weak at mistake detection and pedagogical responses. Code, data and leaderboard are open (github eth-lre/mathtutorbench) — [arXiv 2502.18940](https://arxiv.org/abs/2502.18940)
- **Bridge (Wang et al., NAACL 2024) [peer-reviewed]:** 700 real tutoring conversations annotated with expert decisions in three steps: (A) infer the student's error, (B) choose a remediation strategy, (C) state the strategy's intention. GPT-4 responses conditioned on expert decisions were **76% more preferred and 80% more useful**. Random decisions degraded quality (−67% per arXiv v3; the Hugging Face README says −97%, **so the sources conflict**). License CC BY-NC 4.0 — [arXiv 2310.10648](https://arxiv.org/html/2310.10648v3); [HF dataset](https://huggingface.co/datasets/rose-e-wang/bridge/blob/main/README.md)
- **TutorEval (Chevalier et al., ICML 2024) [peer-reviewed]:** 800+ expert-written questions about **long STEM textbook chapters** (math, physics, CS, environmental and life sciences). It is the closest public analogue to "tutor over a provided document". The companion TutorChat dataset has 80K synthetic textbook dialogues, and code is at princeton-nlp/LM-Science-Tutor — [PMLR](https://proceedings.mlr.press/v235/chevalier24a.html)
- **Stepwise verification (Daheim et al., EMNLP 2024):** 1,002 stepwise math reasoning chains with teacher-annotated first error step. LLMs solve problems well but "struggle to precisely detect student's errors" — [arXiv 2407.09136](https://arxiv.org/abs/2407.09136)
- **LearnLM arena (2025):** 189 educators produced 2,666 blind multi-turn interactions (1,333 match-ups) across **49 scenarios**. 206 experts gave 4,306 assessments, about 3.2 per match-up. Gemini 2.5 Pro was preferred in 73.2% of match-ups and had the highest rubric adherence (82-84% per principle). Limitations: snapshot interactions, **no measured learning outcomes**, expensive expert evaluation — [arXiv 2505.24477](https://arxiv.org/html/2505.24477v1)
- **LearnLM-Tutor automatic evals** use an LLM critic with **a separate prompt per pedagogical dimension** — [arXiv 2407.12687](https://arxiv.org/html/2407.12687v4)
- **2026 benchmarks [preprints, abstract-level only, not verified]:**
  - KMP-Bench (K-8 math, holistic + granular pedagogy, 150K-dialogue KMP-Pile) — [arXiv 2603.02775](https://arxiv.org/abs/2603.02775)
  - SafeTutors (joint safety + pedagogy; argues most tutor evals still inherit QA metrics) — [arXiv 2603.17373](https://arxiv.org/html/2603.17373)
  - EduAgentBench (tutor *agents*: learner-state diagnosis, adaptation over time) — [arXiv 2605.14322](https://arxiv.org/pdf/2605.14322v2)
  - EduEVAL-DB (pedagogical-risk rubric; fine-tuned Llama 3.1 8B evaluator) — [arXiv 2602.15531](https://arxiv.org/pdf/2602.15531)
  - ConvoLearn (dialogic tutoring fine-tuning data) — [arXiv 2601.08950](https://arxiv.org/html/2601.08950v4)

### Inferences
**A lightweight ClaimLab eval harness, buildable in about 1-2 days:**
1. **Scenario bank (20-30, modelled on the LearnLM arena's 49).** Each scenario is a tuple: paper PDF, page range, learner question, persona/mastery state, and scripted learner answers. Scripted answers include the correct answer, a common misconception (written by hand from the paper), an off-topic answer, and "I don't know". Cover question types: definition, result lookup, why/derivation, experiment.
2. **Layer 1: deterministic checks (cheap, run on every CI commit with recorded or replayed outputs, and live nightly):**
   - schema validity
   - 3-5 steps, 2-5 sentences each
   - step 1 is not a question
   - `source`-tagged steps contain a quote that matches the selected pages verbatim (fuzzy ratio ≥ 0.95)
   - each turn has at least 1 step whose numbers or terms appear in the source text (the concreteness proxy)
   - every board object is referenced in its step text
   - the check has a private key
   - after a wrong answer, the next check's `variant_id` differs and its normalized text and option-set similarity to all prior variants is below a threshold
3. **Layer 2: per-dimension LLM judge.** One prompt per dimension, LearnLM-Tutor style, with Yes / To some extent / No labels, MRBench style. Dimensions:
   - (a) *Directness*: does step 1 answer the question asked?
   - (b) *Concreteness*: uses the paper's names, numbers and definitions, including a worked example
   - (c) *Groundedness*: claims tagged `source` are supported by the quote
   - (d) Google rubric items: straightforward, information order, no irrelevant information, no repetition, no contradiction
   - (e) for remediation turns, MRBench's mistake identification, mistake location, guidance, actionability, answer-not-revealed-on-1st-miss
   - (f) *Check quality*: answerable from the steps, not answerable by copying a sentence, targets the turn's key idea
4. **Calibrate the judge before trusting it.** MRBench found small judges negatively correlated with humans. Have 2 team members label about 60 turns, compute Cohen's kappa (MRBench's human-human agreement was 0.71, a reasonable ceiling to compare against), and keep only dimensions where judge-human agreement is acceptable. Use a stronger judge than the tutor model where possible.
5. **Variance measurement.** Run each scenario k = 5 times at production temperature. Report the per-dimension pass rate and its spread. Regressions are judged on the pass-rate distribution, not single samples. This directly targets "output varies turn to turn".
6. **Pairwise A/B for prompt changes (arena-style).** For each scenario, show old vs new outputs blind to a judge (and to a human for a subset). Report the win rate.
7. **Latency budget.** Record p50/p95 per turn phase: generation, check grading by type. Free text should be the only path that needs a second model call.
8. **Optional learning proxy.** A small within-subject pilot (5-10 people) with pre/post questions on a paper section. The arena paper explicitly lacks outcome measures, so even a tiny pilot is more than most vendor modes report.

### Gaps
- MRBench tested only Prometheus2 and Llama-3.1-8B as judges. I did not find a published reliability number for frontier-model judges on these dimensions; LearnLM's critic-reliability section was in a part of the paper I could not read.
- All the public benchmarks are math or STEM-textbook based. None targets research-paper comprehension, so ClaimLab will need its own scenario bank.
- I did not verify TutorEval's grading protocol (whether an LLM grades against expert key points).

---

## Q5. Which prompt and agent patterns make LLM tutors direct and deep without hallucinating: schemas, self-checks, rubric-guided generation, grounding/citation, check-variant generation, diagnosing misconceptions?

### Takeaway
The best-evidenced patterns separate *deciding* and *verifying* from *writing*. Bridge's decide-then-respond step improved GPT-4 responses 76-80%. Daheim's verify-then-generate reduced hallucinated feedback. Pardos's self-consistency cut bad hints from 32% to near 0% in algebra. Combine these with short prompts (long ones get partially ignored) and code-enforced rules (prompt-only behaviour is inconsistent). For ClaimLab that means: generate the answer key, misconception map and multiple check variants *in the planning pass*; diagnose MCQ/numeric errors in code; and use the LLM only where judgment is genuinely needed.

### Cited Findings
- **Decision-before-response (Bridge):** a structured "infer the error, pick a strategy, state the intention" step before generation made GPT-4 responses 76% more preferred and 80% more useful than unstructured generation — [arXiv 2310.10648](https://arxiv.org/html/2310.10648v3)
- **Verify-then-generate (Daheim et al., EMNLP 2024):** a separate verifier (classification, textual error description, or step alignment against a reference solution) runs before the response generator. Alignment and error-description verifiers make replies "highly targeted ... more often correct with less hallucinations", per automatic and teacher evaluations. Code at eth-lre — [arXiv 2407.09136](https://arxiv.org/abs/2407.09136); [ACL Anthology](https://preview.aclanthology.org/setup/2024.emnlp-main.478)
- **Self-consistency for answer keys and hints (Pardos & Bhandari 2024):** 32% of ChatGPT help failed quality checks. Applying self-consistency (sample several and take the agreed answer) reduced failures to nearly 0% for algebra and 13% for statistics — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11125466/)
- **Hidden reference-solution pattern:** some tutor prompts have the model first produce a full step-by-step solution in a hidden self-note used as the "gold standard for assessment". **Low-quality source** (a shared generic Gemini Gem prompt, not a study), but the pattern matches Daheim's reference-alignment verifier — [shared prompt doc](https://docs.google.com/document/d/1p2aeeVmstAASRUsgH52NLDmhghrhhsab2pvmyevnuYI/export?format=pdf)
- **Prompt length and consistency:**
  - Khan Academy found long prompts lead the model to "randomly ignor[e] different parts of the instructions" — [Khan Academy PT blog](https://blog.khanacademy.org/pt-br/?p=19535)
  - OpenAI says its system-instruction-based study mode "may result in inconsistent behavior and mistakes across conversations" — [The Decoder](https://the-decoder.com/openai-launches-study-mode-for-chatgpt-while-education-users-are-told-to-wait-and-learn-later/)
  - University of Toronto guidance recommends repeating the most important rules throughout the system prompt — [U of T CTSI guide (Dec 2025)](https://teaching.utoronto.ca/wp-content/uploads/AI-virtual-tutor-developing-effective-system-prompt-CTSI-Dec2025.pdf)
  - Kestin's effective tutor used a two-paragraph prompt with capitalised hard rules — [AIED Research](https://aiedresearch.substack.com/p/ai-tutoring-outperforms-active-learning)
- **Anti-repetition:** Khanmigo users complained of repetition, and prompts were rewritten to avoid repeated questions — [Khan Academy blog](https://blog.khanacademy.org/khan-academys-7-step-approach-to-prompt-engineering-for-khanmigo)
- **Grounding:** LearnLM-Tutor grounds interactions in lesson materials shared by tutor and learner, and rates groundedness — [arXiv 2407.12687](https://arxiv.org/html/2407.12687v4). Duolingo uses human review of explanations for factual correctness — [Duolingo blog](https://blog.duolingo.com/duolingo-max)
- **Mistake detection is the weak link:** MathTutorBench and Daheim both find models solve well but detect student errors poorly — [arXiv 2502.18940](https://arxiv.org/abs/2502.18940); [arXiv 2407.09136](https://arxiv.org/abs/2407.09136)
- **Pedagogical instruction following:** Google's approach is to describe the desired pedagogy in system instructions and train the model to follow them — [arXiv 2412.16429](https://arxiv.org/html/2412.16429v3). ClaimLab cannot fine-tune muse-spark-1.3, so it should rely on structure and validation instead.

### Inferences
Concrete, testable recommendations for ClaimLab, mapped to the observed issues:

**A. Directness and depth ("too abstract")**
1. **Two-pass turn: private plan, then render.** The plan pass outputs a schema the learner never sees:
   - `direct_answer` (1-2 sentences, must cite page/figure)
   - `key_entities` (paper's terms, symbols and numbers, each with a page reference)
   - `worked_example` (concrete values from the paper and the computation)
   - `likely_misconceptions[]`
   - `check_variants[≥3]`, each with an answer key and a distractor→misconception map
   The render pass turns the plan into 3-5 steps. Code validates that step 1 paraphrases `direct_answer` (judge or embedding similarity) and that `key_entities` appear in the steps. This is Bridge's decide-then-respond applied to explanations.
2. **Required schema fields with code validators (not prompt-only):**
   - `step[0].role = "answer"`
   - at least one step has `role = "worked_example"` with numeric tokens found in the selected pages or in a sandbox run
   - every `source`-tagged step carries a quote that string-matches the PDF text
   - every `assumption`/`interpretation` step states what it rests on
   On validation failure, do one repair retry with the specific failed rule in the message, then fall back. Log failures as eval data rather than hiding them.
3. **Keep the system prompt short.** Put hard rules in a numbered list of 8 or fewer items and repeat the top 2 (answer first; use the paper's numbers) at the end of the prompt. Khanmigo and U of T found long prompts get partially ignored.
4. **Use the Google rubric items as generation guidance.** Include 4-5 of them verbatim in the prompt ("straightforward response", "information order", "no repetition", "no irrelevant information"), and score them with the judge. This is rubric-guided generation that matches the eval.

**B. Repeated check question after a wrong answer**
5. **Variant pool generated upfront in the plan pass** (no extra latency at remediation time). Each variant gets a `variant_id`, the same concept, and different surface features (different numbers, a different figure or condition, a reordered or reworded stem). Code enforces non-repetition: never re-serve a `variant_id`, and reject a variant if its normalized stem plus option set exceeds a similarity threshold to any served variant. This also gives the mastery model the "two distinct variants" it requires. *Test:* 0 repeated or near-duplicate variants across scripted 3-miss sequences.
6. **Self-consistency on answer keys.** Generate or compute each key twice (or compute it in the Python sandbox for numeric checks) and drop variants whose keys disagree. Pardos saw 32% → about 0% (algebra) / 13% (stats) failures with self-consistency.

**C. Diagnosing misconceptions from wrong answers**
7. **MCQ: misconception-tagged distractors.** Each distractor carries `misconception_id` and a one-line `why_wrong`. A wrong choice gives the diagnosis deterministically in code, with zero latency and zero variance. The remediation text is then generated, or pre-generated in the plan, from that misconception (elaborated feedback, ES 0.49 vs 0.05 for "incorrect").
8. **Numeric: code-side error classifiers** before any LLM call: off by a factor of 10ⁿ (units), sign flip, used the wrong table row or column (compare against other values on the selected pages), and the reciprocal. Pass the classifier label to the remediation prompt, as in Daheim's verify-then-generate.
9. **Remediation turn template (MRBench dimensions):**
   - (i) name the error: identification + location
   - (ii) one targeted hint or counter-example drawn from the paper: guidance
   - (iii) an explicit next action ("try this new version: ..."): actionability
   - (iv) don't reveal on the 1st miss; reveal with a worked explanation on the 2nd
   - (v) encouraging but brief tone (most LLMs score "neutral" on tone in MRBench)

**D. Free-text latency**
10. Default to MCQ/numeric checks. Use free text only for "why" (elaborative interrogation), at most once per concept per session. Grade free text against the plan's **key points list**, a rubric-of-key-points that a smaller/faster model or a single judge call can apply. Show provisional feedback immediately (the model answer plus "compare yours"; self-explanation against a reference is still constructive in ICAP terms) and attach the graded mastery evidence asynchronously. *Test:* p95 latency for MCQ/numeric grading under 300 ms (code-only); free-text grading off the critical path.

**E. Turn-to-turn variance**
11. Lower the temperature for the plan pass, keep a higher temperature only for phrasing, use schema validation with targeted repair, and measure variance with the k = 5 eval runs from Q4. Move every pedagogical decision that can be made in code into code: mode selection (answer-first vs faded), variant selection, misconception diagnosis for MCQ/numeric, reveal-on-2nd-miss. This follows ClaimLab's existing principle that "the agent selects supported tools; reviewed code performs calculations".

### Gaps
- None of the pattern papers (Bridge, Daheim, Pardos) tested research-paper comprehension. Their gains come from math remediation and may not transfer one-for-one.
- I found no published evaluation of "misconception-tagged distractor" pipelines with LLM-generated distractors in a tutoring context. The recommendation rests on the feedback meta-analyses plus Bridge/Daheim, not on a direct study.
- I found no evidence on how muse-spark-1.3 specifically behaves under these patterns. ClaimLab needs to measure this itself with the Q4 harness.
