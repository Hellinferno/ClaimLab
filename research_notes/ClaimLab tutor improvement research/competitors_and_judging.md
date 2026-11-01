# ClaimLab: competitive landscape of AI paper-understanding tools, and analysis of the Meta Global AI Developer Hackathon judging (as of 31 October 2026)

Scope note: research ran on 31 October 2026. Every product capability is dated to its announcement or source; product features change often and may have moved since. Pricing comes mostly from third-party aggregators, which disagree, and is flagged as unverified. TinyFish tools were not available in this session, so standard web search/fetch was used.

---

## Q1. Which products and research prototypes help people read or learn from papers in 2025-2026, and how does ClaimLab compare?

### Takeaway
The market for "summarise / chat with / cite a paper" is crowded and commoditised. The big general assistants converged in July-August 2025 on Socratic tutoring modes (ChatGPT study mode, Gemini Guided Learning, Claude learning mode), and in 2025-2026 on generated visuals (NotebookLM Video Overviews, mind maps and infographics; Gemini interactive images; Claude inline interactive charts with sliders since March 2026). No consumer reading tool found in this research writes and runs an experiment that reproduces a paper's mechanism with learner-adjustable knobs, verifies quotes against the PDF, and grades checks against a private key under a two-variant mastery rule. Code-based paper reproduction does exist, but in researcher-facing agents (PaperBench, Paper2Code, Paper2Agent, the 2026 "Paper-replication" skill) that take hours per paper and do no teaching. ClaimLab's defensible position sits between the tutors and the reproduction agents.

### Cited Findings

#### General-purpose assistants with learning, research, or visual modes
- **NotebookLM Video Overviews** launched 29 July 2025: narrated slides "enhanced with visuals, diagrams, quotes, and data" drawn from the user's documents. The Studio panel has four tiles (Audio Overviews, Video Overviews, Mind Maps, Reports), and a notebook can now hold several of each. English first. — [Google blog](https://blog.google/technology/google-labs/notebooklm-video-overviews-studio-upgrades/); [TechCrunch](https://techcrunch.com/2025/07/29/googles-notebooklm-rolls-out-video-overviews)
- **NotebookLM, 20 March 2026 update:** flashcard and quiz progress is saved across sessions for all users; flashcards and quizzes reached mobile; slide decks can be revised and exported to PPTX; new infographic styles. Slide revisions, "Cinematic Video Overviews" and the new infographic styles are restricted to users over 18. — [Google Workspace Updates, 20 Mar 2026](https://workspaceupdates.googleblog.com/2026/03/new-ways-to-customize-and-interact-with-your-content-in-NotebookLM.html); teacher-facing Classroom integration per [TeacherCast, Apr 2026](https://teachercast.net/edtech/google-notebook-lm-updates-april-2026/)
- One third-party source claims NotebookLM's Studio panel was renamed "Gemini Notebook". No other source confirms this, so treat it as unverified. — (aggregated search result; no primary source)
- **NotebookLM grounding:** a September 2025 arXiv study found NotebookLM had a "substantially lower hallucination rate" on document-extraction queries than alternatives, which it attributes to RAG with explicit citations. — [Not Wrong, But Untrue (arXiv 2509.25498)](https://arxiv.org/abs/2509.25498v1)
- **ChatGPT study mode** launched 29 July 2025 for logged-in Free, Plus, Pro and Team users. It walks through problems step by step with Socratic questions instead of giving final answers. Students can toggle it off, and there was no parental or admin lock at launch. — [TechCrunch](https://techcrunch.com/2025/07/29/openai-launches-study-mode-in-chatgpt)
- **ChatGPT deep research** was announced 2 February 2025 as an o3-based agent that synthesises online sources into cited reports. Pro users got it first and Plus users on 25 February 2025. A lighter o4-mini version followed in April 2025. February 2026 updates added connections to MCP servers and apps and the option to restrict searches to trusted sites. — [OpenAI](https://openai.com/index/introducing-deep-research/); [Wikipedia](https://en.wikipedia.org/wiki/ChatGPT_Deep_Research)
- **Gemini Guided Learning** launched 6 August 2025 as a toggle in the prompt box. Responses include images, diagrams, YouTube videos and interactive quizzes. Quizzes and flashcards require users aged 18 or older. — [9to5Google](https://9to5google.com/2025/08/06/gemini-guided-learning/); [Engadget](https://www.engadget.com/ai/geminis-new-guided-learning-mode-can-quiz-students-and-create-interactive-study-aids-181743349.html)
- **Gemini "interactive images"**, which turn static diagrams into explorable visuals, arrived around November 2025. This date comes from secondary sources only. — [AlternativeTo, Nov 2025](https://alternativeto.net/news/2025/11/google-adds-support-for-interactive-images-in-gemini-for-deeper-visual-learning)
- **Claude learning mode** launched in April 2025 for Claude for Education. It reached all Claude.ai users in mid-August 2025 as a Socratic style. Claude Code gained "Explanatory" and "Learning" output styles; in the Learning style, Claude writes part of the code and asks the user to finish it. — [VentureBeat, Apr 2025](https://venturebeat.com/ai/anthropic-flips-the-script-on-ai-in-education-claude-learning-mode-makes-students-do-the-thinking); [Engadget, Aug 2025](https://www.engadget.com/ai/anthropic-brings-claudes-learning-mode-to-regular-users-and-devs-170018471.html)
- **Claude inline interactive visuals** entered beta on 12 March 2026 on all plans, including free. Claude draws custom charts, diagrams and visualisations inline, sometimes unprompted, with buttons, sliders and fullscreen. The feature reached Claude Cowork on paid plans on 22 April 2026, and it is separate from Artifacts, which build app-like React outputs. — [Claude blog](https://claude.com/resources/articles/claude-builds-visuals); [The Decoder](https://the-decoder.com/claude-can-now-create-interactive-charts-and-visualizations-directly-in-chat/); [AlternativeTo, Mar 2026](https://alternativeto.net/news/2026/3/anthropic-s-claude-can-now-respond-with-interactive-visuals-such-as-charts-and-diagrams)
- A critique of Claude's visuals: the user "sees the chart but cannot see the code, data processing logic, or underlying assumptions behind it." — [The Signal (Substack)](https://thesignal.substack.com/p/claudes-new-interactive-visuals-are)
- **Perplexity Academic mode** limits search to scholarly sources. Guides disagree on its databases (Semantic Scholar, PubMed, arXiv) and warn that it does not guarantee peer-reviewed results only. One April 2026 blog lists an Education Pro tier at US$5/month; this is unverified. Only third-party guides were found. — [EducatorsTechnology, Feb 2026](https://www.educatorstechnology.com/2026/02/perplexity-ai-for-research.html); [TrueScho, 2026](https://truescho.com/en/blog/perplexity-ai-pro-research-2026)

#### Research-paper-specific readers and literature tools
- **SciSpace (Copilot / AI research agent):** chat with a PDF that explains jargon, tables and figures, plus a Chrome extension, citation generator, paraphraser and AI-text detector. The free tier caps daily uploads and queries. Premium is about US$12/month by most aggregator counts. Team and Lab prices conflict ($20 per user, $100 for five users, $160/month) and are unverified. — [GeekChamp 2026](https://geekchamp.com/scispace-pricing-reviews-2026/); [AI Tools Atlas](https://aitoolsatlas.ai/tools/scispace-ai-research-agent)
- **Elicit:** PRISMA-aligned systematic-review workflows that screen up to 5,000 papers, plus automated research reports. Pricing conflicts across aggregators: Plus at $7-12/month, Pro at $29-49/month, and the free tier described either as 5,000 one-time credits or as 2 reports/month. Unverified. — [CostBench](https://costbench.com/software/ai-research-tools/elicit); [AI Tools Atlas](https://aitoolsatlas.ai/tools/elicit/pricing)
- **Consensus:** the "Consensus Meter" gauges how far studies agree on yes/no questions. "Deep Search" automates literature reviews, but sources disagree on its scope (50 papers versus up to 1,000). Pro is $9-15/month and Deep is $45-65/month; unverified. — [ToolsForHumans](https://www.toolsforhumans.ai/ai-tools/consensus); [ComputerTech review](https://computertech.co/consensus-ai-review/)
- **Explainpaper:** highlight a passage to get a plain-language explanation. Pro is about $16/month (third party). **Scholarcy:** fixed-format "summary flashcards" covering claims, methods, findings and references, with conflicting prices ($4.99 or $9.99/month). — [Nextool comparison](https://nextool.ai/compare/explainpaper-vs-scholarcy)
- **ChatPDF:** free tier of 2 PDFs/day up to 120 pages; Plus about $20/month. **Humata:** cross-document Q&A with citations; one listing gives up to $199/month, which is unverified. Neither vendor says clearly whether uploads train their models. — [CASRAI guide](https://www.casrai.org/guides/chat-with-pdf-tools-for-researchers)
- **Paper Digest:** the free tier works only from DOIs and arXiv links; uploading local PDFs requires Pro, and pricing is not clearly published. — [FindAIList comparison](https://preview.findailist.com/compare/explainpaper-vs-paper-digest)
- **alphaXiv:** AI chat that answers questions about highlighted sections (February 2025), audio for papers (March 2025), linked paper code (March 2025) and AI-generated blog posts, plus line-by-line community discussion with ORCID verification. These dates come from search snippets of the alphaXiv changelog; fetching the page on 31 October 2026 returned HTTP 404. — [alphaXiv changelog (snippet)](https://www.alphaxiv.org/changelog); [G2](https://www.g2.com/products/alphaxiv/discuss)
- In a Hacker News thread comparing alphaXiv with the "asxiv" ask-arXiv tool, one commenter said the LLM could point to parts of a paper well but "could not explain parts of the equations based on other knowledge outside of the paper." — [HN item 45212535 (mirror)](https://hn.jakechampion.name/item/45212535)
- **Ai2 Semantic Reader:**
  - Scim skimming highlights are colour-coded by facet (Goal, Method, Results), with adjustable density and margin flags.
  - ScholarPhi gives just-in-time definitions of terms and symbols (CHI 2021).
  - Ai2's own materials disagree on Scim's venue (IUI'23 or CHI 2024).
  - Sources: [Ai2 case study](https://allenai.org/blog/case-study-iterative-design-for-skimming-support-5563dbe0899e); [Semantic Reader Open Research Platform](https://openreader.semanticscholar.org/)
- **Ai2 Asta** launched 26 August 2025:
  - It absorbed Paper Finder (now "Find Papers") and ScholarQA (now "Summarize Literature"), with "Analyze data" in partner beta.
  - It offers an MCP Scientific Corpus Tool covering more than 200M papers.
  - In AstaBench's first evaluation (2,400+ problems), only 18 of 57 agents could complete all the benchmarks, and their scores were "modest".
  - Ai2 listed "experiment replication" as a future capability.
  - Sources: [Ai2 blog](https://allenai.org/blog/asta); [The Letter Two, Aug 2025](https://thelettertwo.com/2025/08/26/ai2-asta-open-science-ai-framework/)
- ScholarQA, released January 2025, used RAG over at least 8 million papers on Claude 3.5 Sonnet. — [The Letter Two, Jan 2025](https://thelettertwo.com/2025/01/23/ai2-launches-scholarqa-beta-literature-review-tool/)
- **Papers with Code** stopped operating around 24 July 2025 (Meta sunset it). Hugging Face announced "Trending Papers" as its replacement on 25 July 2025. Anecdotal reports say the replacement has no leaderboards and no search by dataset or task, and the old API no longer responds. — [HyperAI](https://hyper.ai/en/news/42900); [CodeSOTA shutdown record (commercial site)](https://www.codesota.com/papers-with-code/shutdown)

#### Interactive explainers (Distill-style)
- **Transformer Explainer** (Georgia Tech Polo Club, with IBM Research) runs a live GPT-2 in the browser so users can watch next-token prediction on their own text. It is open source, and its CHI 2026 paper reports more than 490,000 users. — [CHI 2026 paper PDF](https://poloclub.github.io/papers/26-chi-transformer-explainer.pdf); [arXiv 2408.04619](https://arxiv.org/html/2408.04619v1); [GitHub](https://github.com/poloclub/transformer-explainer)
- **Google Research "Learn Your Way"** (LearnLM on Gemini 2.5 Pro) turns textbook PDFs into personalised interactive lessons:
  - In an RCT with 60 students aged 15-18, it beat a PDF reader on retention 3-5 days later: 78% versus 67% (Maginative reports 77% versus 68%).
  - Immediate scores were about 9% higher.
  - 93% of students wanted to use it again, against 67% for the reader.
  - The trial covered one chapter only.
  - Sources: [Maginative](https://www.maginative.com/article/learn-your-way-googles-new-ai-transforms-static-textbooks-into-interactive-personalized-lessons/); [arXiv 2509.18664](https://arxiv.org/html/2509.18664v1)

#### Agents that run code to reproduce papers (researcher-facing, not tutors)
- **PaperBench (OpenAI, April 2025):** 20 ICML 2024 Spotlight and Oral papers with author-approved hierarchical rubrics totalling 8,316 gradable tasks. Agents trail expert humans by roughly a factor of two. Sources conflict on the human baseline setup (48 hours per paper versus four weeks on a three-paper subset). — [Emergent Mind summary](https://www.emergentmind.com/topics/paperbench-benchmark); [arXiv 2504.01848 listing](https://api.emergentmind.com/papers/2504.01848)
- **Paper2Code / PaperCoder (KAIST, April 2025):** a multi-agent pipeline that generates code repositories from NeurIPS, ICML and ICLR 2024 papers. A 2026 ACL Findings paper (HiRAS) argues that Paper2Code's reference-free evaluation is "susceptible to evaluator hallucination" and proposes a revised protocol (P2C-Ex). — [arXiv 2504.17192](https://arxiv.org/pdf/2504.17192); [ACL Findings 2026](https://aclanthology.org/2026.findings-acl.377.pdf). DeepCode (arXiv, December 2025) is another open agentic-coding system evaluated on PaperBench — [arXiv 2512.07921](https://arxiv.org/pdf/2512.07921)
- **Paper2Agent (Stanford; arXiv 2509.06917, September 2025; later published in Nature):**
  - It turns a paper and its codebase into an MCP server that a chat agent can call, refining the server with tests it generates and runs.
  - Demonstrations cover AlphaGenome, Scanpy and TISSUE.
  - The resulting agents averaged 91.2% accuracy on tutorial-derived questions, against 80.3% for Claude Code with repository access.
  - The authors note that paper agents need ongoing maintenance as upstream code changes.
  - The Nature publication date conflicts across sources (September 2025 or September 2026).
  - Sources: [HF Papers](https://huggingface.co/papers/2509.06917); [Marginal Revolution, Sep 2026](https://marginalrevolution.com/marginalrevolution/2026/09/reimagining-research-papers-as-interactive-and-reliable-ai-agents.html)
- **"Coding-agents can replicate scientific machine learning papers"** (Purdue, 13 July 2026):
  - A "Paper-replication" skill turns each paper claim into a target with recorded evidence. Completion is judged by the workspace and validation checks, not by the agent's final message.
  - Setup: Codex with GPT-5.4, four papers (PIFT, two PINN papers, SINDy), three runs each.
  - All 158 targets reached "MATCHED", and 37 of 39 scalar anchors fell within paper-anchored thresholds.
  - Median time was 1.9-6.9 hours per paper, with a range of 1.2-13 hours.
  - Limitations: a small corpus and no ablation without the skill.
  - Source: [HF Papers 2607.02134](https://huggingface.co/papers/2607.02134.md)

### Inferences

**Comparison matrix.** This is a synthesis of the findings above. "Runs experiments" means the product writes and executes code that reproduces a paper's mechanism, as part of the product flow.

| Product (date of cited capability) | Core | Visual / interactive | Grounding | Runs experiments? | Price tier (unverified where noted) | Target user |
|---|---|---|---|---|---|---|
| NotebookLM (Jul 2025, Mar 2026) | Multi-source notebook Q&A | Audio and video overviews, mind maps, infographics, slides, flashcards and quizzes | Inline citations to sources; lower hallucination in one study | Not found | Free, with paid Google tiers (not verified this session) | Students, knowledge workers |
| ChatGPT study mode / deep research (Jul 2025, Feb 2025) | Socratic tutor; cited web reports | Chat (general ChatGPT tools not checked for study mode) | Web citations (deep research) | Not shown in study mode | Free to Pro | Students, general |
| Gemini Guided Learning (Aug 2025, Nov 2025) | Socratic tutor | Images, diagrams, YouTube, quizzes, interactive images | Not specified | Not found | Free app | Students |
| Claude learning mode + inline visuals (Aug 2025, Mar 2026) | Socratic tutor | Interactive charts and diagrams with sliders; Artifacts | Not specific to papers | Can write code, but code is hidden in inline visuals (critique) | Free to paid | General, students, developers |
| SciSpace | Chat with PDF; literature review | Limited | Cites passages | No | Freemium, ~$12/mo (aggregator) | Researchers, students |
| Elicit / Consensus | Literature search, synthesis, systematic review | Consensus Meter gauge | Paper-level citations | No | Freemium, conflicting prices | Researchers, evidence reviewers |
| Explainpaper / ChatPDF / Humata / Scholarcy / Paper Digest | Passage explanation, chat, summaries | Minimal | Varies | No | ~$5-20/mo (third party) | Students, professionals |
| alphaXiv (2025) | arXiv reader, chat, community comments | Audio, blogs, linked code | Highlighted section in context | Links to code; execution not found | Not verified | ML researchers |
| Semantic Reader / Asta (Ai2, 2023-2025) | Augmented reading; agentic literature tools | Skimming highlights, term definitions | Paper-anchored | Not yet ("experiment replication" listed as future) | Free (non-profit) | Researchers |
| Transformer Explainer (CHI 2026) | Hand-built interactive explainer for one model | Live GPT-2 visualisation | Fixed and reviewed | Runs a real model, but only one topic | Free, open source | Non-experts |
| PaperBench / Paper2Code / Paper2Agent / Paper-replication (2025-2026) | Agentic reproduction or "agentification" of papers | None aimed at learners | Rubrics, tests, recorded targets | Yes, at full scale, over hours | Research artefacts | Researchers, benchmarkers |
| **ClaimLab (Oct 2026)** | Stateful tutor over up to 5 selected PDF pages | Shared whiteboard with concept diagram, paper equation, verified quotes and plots; experiment knobs | Step-level evidence-type tags; verbatim quotes checked against the PDF; web citations | **Yes, at toy scale in minutes**, with learner knobs, plus three hand-checked attention-lab recipes | Hackathon demo (local) | Learners of ML/technical papers |

**Where ClaimLab is genuinely differentiated** (inferred from the absence of these features in the products surveyed):
1. **Executable mechanism, visible to the learner.** General assistants can generate a chart, but Claude's inline visuals are criticised for hiding code and assumptions. ClaimLab shows and runs the numpy code and exposes knobs, so it is "Transformer Explainer for any paper", generated on demand instead of hand-built.
2. **Evidence provenance at step level.** Each step is tagged as source quote, background, web, experiment or interpretation, and quotes are checked verbatim against the PDF. This directly targets the most common complaint about competitors: misattributed or unfindable quotes (see Q2).
3. **Assessment integrity.** A private answer key, deterministic grading for number and choice answers, and a two-variant independence rule. The surveyed study modes quiz learners, but none publishes an independence or mastery policy (not verified as absent; see Gaps).
4. **Explicit learning state.** A session can pause for a prerequisite and resume. Products advertise saved quiz progress (NotebookLM, March 2026), but no public evidence was found of a prerequisite-detour workflow.
5. **A gap between tutors and reproduction agents.** Reproduction agents take 1-13 hours per paper and do not teach. ClaimLab trades fidelity for a minutes-scale, toy-sized mechanism the learner can manipulate. That trade-off is the pitch.

**Where ClaimLab is behind:**
- **Breadth.** Five pages of one paper, against multi-source notebooks (NotebookLM), multi-paper synthesis (Elicit, Consensus, Asta) and corpora of 200M+ papers.
- **Output polish and formats.** No audio or video overview, slides, flashcards, mobile app or PPTX export.
- **Distribution and price.** Competitors are free or cheap, have huge user bases and run in the cloud. ClaimLab's demo is local.
- **Reproduction fidelity.** Toy-scale mechanisms do not reproduce reported numbers. PaperBench, Paper-replication and Paper2Agent check results against the paper itself.
- **Community and social layer.** alphaXiv has comments, ORCID and author interaction.
- **Figure understanding.** SciSpace advertises figure and table explanation. Whether ClaimLab reads the paper's figures is not established in this research.

**Closest competitive threat:** Claude (learning mode plus inline interactive visuals with sliders) or Gemini Guided Learning used with an uploaded PDF. A judge may ask "couldn't I just do this in Claude?" ClaimLab's answer must be verification and pedagogy: visible code, quotes checked against the PDF, evidence tags, a private key and two-variant mastery. Visuals alone are not the answer.

### Gaps
- Official pricing pages for SciSpace, Elicit, Consensus, ChatPDF, Humata, Explainpaper, Scholarcy and Paper Digest were not fetched. Aggregator figures conflict and may be stale.
- The alphaXiv changelog returned 404 on 31 October 2026. Its current features, pricing and any 2026 additions (such as deep research or code execution) are unverified.
- Launch dates for Claude Projects and Artifacts, and NotebookLM Audio Overviews, were not re-verified in this session, so they are omitted from the findings.
- Not verified: whether ChatGPT study mode, Gemini Guided Learning or NotebookLM can execute code within the learning flow. General ChatGPT and Gemini have code tools, but no source checked here ties them to study modes.
- PaperBench headline replication scores by model were not verified against the primary paper in this session.
- Gemini Guided Learning changes in 2026 and NotebookLM's pricing tiers were not checked.
- Whether any competitor uses an explicit mastery or independence rule comparable to two-variant credit: no public documentation was found either way.

---

## Q2. What gaps do users report in these tools (hallucination, shallow summaries, no verification, no active learning)?

### Takeaway
User complaints cluster around misattribution: wrong or fabricated sources, misread numbers, incomplete reading of documents, and quotes that cannot be found in the source. Grounded tools like NotebookLM do better than general chatbots but are still unreliable. HCI research adds that heavy grounding can clutter the interface, that experts find standard QA metrics too coarse, and that paper chat cannot explain equations from outside the paper. Learning-science evidence shows that unguarded AI harms learning while structured tutoring helps, which supports ClaimLab's private key and active checks. Peer-reviewed user studies on hallucination in paper-reading assistants specifically are sparse.

### Cited Findings
- **Reddit (r/PhD-style thread, 2026):**
  - One user found "all the attributed sources were wrong" and that "many of the case studies are likely to have been hallucinated."
  - Another researcher reported five citation errors in a couple of months where the title was correct but the author list was wrong.
  - These come from a third-party Reddit snapshot mirror, and the claims were summarised by search, so the mapping to individual posts is not verified.
  - Source: [Reddit snapshot mirror](https://reddit.sentinel-team.org/posts/1rhs7ac/snapshots/2026-03-02T19%3A23%3A45.392683Z)
- **r/notebooklm (spring 2026):**
  - Users say NotebookLM is "increasingly mixing up sources or putting them in the wrong context."
  - Others report it reads numbers backwards, does not read full documents and leaves critical information out. In one user's stricter "negative control" notebook, the tool could not find the passage it had "quoted".
  - Complaints came in waves from mid-February and in early April 2026.
  - Source: [r/notebooklm snapshot timeline](https://reddit.sentinel-team.org/subreddits/notebooklm/snapshots/2026-04-29T12%3A24%3A27.513748Z)
- A qualitative study of NotebookLM in clinical use warns that fact-checking "may be impossible or error-prone due to hallucinated or un-clickable citations." — [Moonlight review of the study](https://www.themoonlight.io/review/generative-ai-in-clinical-practice-novel-qualitative-evidence-of-risk-and-responsible-use-of-googles-notebooklm)
- An overview of scholarly LLMs lists the risks as "non-existent citations, misrepresented research findings, or inaccurately contextualized inferences." — [MDSOAR overview](https://mdsoar.org/items/22627559-daa8-4564-9e3d-e75430fd8af3/full)
- **Counterpoint:** NotebookLM's citation-grounded RAG had a substantially lower hallucination rate than alternatives on document-extraction queries. — [arXiv 2509.25498](https://arxiv.org/abs/2509.25498v1)
- **HCI evidence (2025-2026):**
  - **PaperTrail (CHI 2026):** a within-subjects study with 26 researchers. The system flags unsupported claims in answers and paper claims the answer omitted. The authors found the added grounding information cluttered the interface and reduced usability.
  - **Expert error schema (CHI 2026):** scholarly QA metrics "lack contextual nuance and fail to reflect how scientific domain experts assess LLM outputs."
  - Search results point to [arXiv 2602.21059](https://arxiv.org/pdf/2602.21059) and [arXiv 2602.21045](https://arxiv.org/pdf/2602.21045v1). Which paper is which was not verified.
- The **PaperAsk** benchmark found claim verification was the most revealing task, with hallucination at measurable rates. — [arXiv 2510.22242](https://arxiv.org/pdf/2510.22242.pdf)
- **DocVoyager (CHI 2025)** suggests goal-based questions to guide document reading; participants focused more easily on information relevant to their goals. — [Adobe Research](https://research.adobe.com/publication/docvoyager-anticipating-users-information-needs-and-guiding-document-reading-through-question-answering)
- **Equations and background:** paper chat "could not explain parts of the equations based on other knowledge outside of the paper." — [HN thread (mirror)](https://hn.jakechampion.name/item/45212535)
- **Opaque visuals:** users see Claude's generated charts but not the code or assumptions behind them. — [The Signal](https://thesignal.substack.com/p/claudes-new-interactive-visuals-are)
- **Unguarded AI harms learning** (Bastani et al., PNAS 2025, vol. 122):
  - Field experiment with nearly 1,000 high-school maths students.
  - After access was removed, the ChatGPT-like tutor ("GPT Base") group did worse than students who never had access, with a 17% grade reduction.
  - A safeguarded "GPT Tutor" largely offset the harm.
  - Caveat: one Turkish school, one subject, four 90-minute sessions.
  - Sources: [EconPapers](https://econpapers.repec.org/RePEc:nas:journl:v:122:y:2025:p:e2422633122); [Wharton Knowledge](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education); [caveat commentary](https://liveinthefuture.org/stories/ai-makes-students-worse)
- **Structured AI tutoring can help** (Kestin et al., Scientific Reports, June 2025):
  - A randomised crossover trial with 194 Harvard physics students using a GPT-4 tutor built around pedagogical principles.
  - Students "learned more than twice as much and spent less time" than in an active-learning class.
  - Caveats: two topics, short-term tests, an elite sample.
  - Sources: [KQED MindShift](https://www.kqed.org/mindshift/64694/an-ai-tutor-helped-harvard-students-learn-more-physics-in-less-time); [paper PDF copy](https://biblioteca.unisced.edu.mz/bitstream/123456789/3656/1/AI_Tutoring_Outperforms_Active_Learning.pdf)
- **Interactive lessons beat static PDFs on retention** (Learn Your Way RCT, n=60): 78% versus 67% after 3-5 days. — [Maginative](https://www.maginative.com/article/learn-your-way-googles-new-ai-transforms-static-textbooks-into-interactive-personalized-lessons/)
- **Agent-side reliability:** AstaBench found only "modest scores" for science agents. Reference-free evaluation of code generated from papers is vulnerable to evaluator hallucination. Paper agents need maintenance as dependencies change. — [Ai2 Asta](https://allenai.org/blog/asta); [ACL Findings 2026 (HiRAS)](https://aclanthology.org/2026.findings-acl.377.pdf); [Paper2Agent](https://huggingface.co/papers/2509.06917)
- **Privacy:** neither ChatPDF nor Humata explicitly confirms or rules out training on uploaded content. — [CASRAI](https://www.casrai.org/guides/chat-with-pdf-tools-for-researchers)
- **Lost infrastructure:** after Papers with Code shut down, its replacement reportedly has no leaderboards and no search by dataset or task (anecdotal). — [HyperAI](https://hyper.ai/en/news/42900)

### Inferences
- ClaimLab's verbatim quote verification and step-level evidence tags map directly onto the most frequent complaint, quotes that cannot be found or are misattributed. This should be **the first ten seconds of the demo**: show a quote being checked against the PDF, and ideally show a rejected quote.
- PaperTrail's clutter finding is a design warning. Evidence tags should be compact chips with details on demand, not long provenance blocks on every step.
- The HN equation complaint is answered by the "background" evidence type plus the experiment. ClaimLab can explain an equation with outside knowledge while labelling it honestly as background, not source. The pitch should name this.
- Bastani (harm without guardrails) together with Kestin (benefit from a structured tutor) is the strongest published support for ClaimLab's private answer key, check questions and two-variant rule. Cite both in the pitch to defend against the "simple education chatbot" anti-project label (see Q3).
- Competitors' visuals are generated but unverified. ClaimLab's reviewed attention-lab recipes and visible experiment code can be framed as "verifiable visuals", which matches Meta's "Best Practices for Verifiable Agents" session (Q3).
- No competitor publishes accuracy metrics for its own grounding. A small self-evaluation table from ClaimLab (quote-match rate, experiment success rate, grading agreement with the key) would stand out.

### Gaps
- No large-scale survey was found that quantifies how often users raise each complaint across tools. The Reddit evidence is anecdotal and came through a third-party mirror.
- No user studies were found specifically on SciSpace, ChatPDF, Elicit or alphaXiv accuracy.
- The CHI 2026 PaperTrail and error-schema papers were seen only through search snippets. Full results, effect sizes and which arXiv ID belongs to which paper were not verified.
- No evidence was found on whether learners actually use runnable experiment knobs, or learn more from them, in paper-reading contexts. Transformer Explainer reports usage but not learning gains in the sources checked.

---

## Q3. What has been published about the Meta hackathon ClaimLab is entered in (judging criteria, prizes, Meta-model requirement, past winners)?

### Takeaway
The event is real and partly verified. The **Meta Global AI Developer Hackathon** is run by Meta with Cerebral Valley: virtual and worldwide, up to 20,000 accepted participants, a US$1M cash pool, and submissions due **Wednesday 4 November 2026 at 9:00 PM ET**. The weighted rubric comes from the participant guide in the repo, not the public page:
- **Impact 30%**
- **Use of Meta AI Tooling 25%**
- **Technical Depth & Execution 20%**
- **Demo 25%**

Before scoring, Stage 1 is a pass/fail check on theme fit and real use of Meta models. The guide's list of projects to avoid ("anti-projects") explicitly includes **"Simple 'AI for Education' Chatbots"** and **"Basic RAG Applications"**, which is ClaimLab's main Stage 1 risk. No winners exist yet for this event: judging runs 5-8 November and the finals are on 9 November. Past Meta/Llama hackathon winners favoured multimodal and wearable builds, agents, and practical tools that turn documents into structured or visual output.

### Cited Findings

#### The event (public page, fetched 31 October 2026)
- "Meta Global AI Developer Hackathon", hosted by Meta and Cerebral Valley, virtual and worldwide, with up to 20,000 accepted applicants and free entry. Applications ran 13-25 October and the kickoff was 26 October.
  - Workshops and Discord office hours: 27 October to 4 November.
  - Submissions due 4 November, 9:00 PM ET.
  - Judging: 4-8 November.
  - Closing ceremony, live finals and winners: 9 November.
  - The page says dates may change at Meta's discretion.
  - Source: [Cerebral Valley event page](https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon)
- **Tracks** (public page): every project enters one track.
  - Indie Developer, for individuals and students, is "judged on creativity, technical ambition, and whether it works."
  - Startup is judged on "technical execution and whether it holds up in production."
  - **Themes:** "Build for Your World" and "Push the Frontier".
  - **Prize pool:** US$1,000,000 total, with no breakdown on the public page.
  - **Models:** the Muse Spark series, Muse Wonder, Muse Image and SAM 3.1 through the Meta Model API; Meta open weights; and the Muse Code coding agent.
  - **Judges:** none listed. The public page has no rubric weights and no anti-project list; the Official Rules were not reachable from it.
  - Source: [Cerebral Valley event page](https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon)
- Secondary listings describe the event as "a 10-day virtual competition" with $150 in Meta Model API credits per participant, organised by Meta Superintelligence Labs. — [CourseJoiner (aggregator)](https://coursejoiner.com/hackathon/meta-global-hackathon-2026-1/)

#### The participant guide (user-supplied snapshot in the repo; not independently verified against official rules)
- **Rules:**
  - Repositories must be public; teams have at most four members.
  - "Your demo must only highlight the specific features, code, and functionality that you built during the Hackathon"; failing to identify original contributions can mean disqualification.
  - A three-minute demo video is required and "serves as a primary artifact for evaluation alongside your code and live product."
  - Source: [Supplied participant guide](../../gemini-code-1793038385208.md) (`D:\Meta hackathon\gemini-code-1793038385208.md`; also referenced in `docs/19_HACKATHON_RULES.md` as `references/PARTICIPANT_GUIDE_SUPPLIED.md`)
- **Anti-projects:** medical-advice AI, "Basic RAG Applications", "Simple Image Analyzers", "Simple 'AI for Education' Chatbots", job screeners, nutrition coaches, personality analysers, sports coaches, and political or war projects. — [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Problem statements:**
  - "Build for Your World": bring Meta's models into your domain.
  - "Push the Frontier": use the models on challenges "in software, robotics, manufacturing, energy, materials, and beyond. Give a machine a new capability, **accelerate a scientific experiment**, or unlock a better way to understand and control a physical system."
  - Source: [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Judging process:**
  - Stage One is pass/fail on baseline viability: does the project fit the theme and "properly utilize the Meta Model API and/or Meta open-weight models built during the hackathon"?
  - Stage Two scores projects 0-10 on the rubric.
  - Stage Three: the top 5 per track advance, and "judges watch video demos live and rank projects using the same rubric."
  - Source: [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Rubric:**
  - Impact (30%): "real-world potential... Could this become something people use? Does it fit into one of the designated problem statements?"
  - Use of Meta AI Tooling (25%): "How creatively did this team use Meta's AI tooling? Did they go beyond basic integration and surface unexpected capabilities?"
  - Technical Depth & Execution (20%): "Is the engineering sound and thoughtfully refined?"
  - Demo (25%): "Is this a working, impressive demo? Does the product hold up live? Is the demo video compelling to watch?"
  - Source: [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Prizes:**
  - Indie track $400K (1st-5th: $150K, $100K, $75K, $50K, $25K).
  - Startup track $550K (1st-5th: $250K, $150K, $75K, $50K, $25K).
  - Meta bonus prizes ($50K total):
    - Most Viral Project, $20K: highest engagement on X through end of day 8 November.
    - Best Build on Meta Open Weight Models, $10K: Muse Glimmer or Muse Spark Open.
    - Community Vote, $10K: announced 16 November.
    - **Best Agentic Use-Case, $5K:** judged on "autonomy level, effectiveness, and practical utility".
    - Best Creative Build, $5K: Muse Image or Muse Wonder.
  - Source: [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Workshops:** these include "Agents 102: Best Practices for **Verifiable** Agents" (28 October) and a Fireworks session on Muse open models (30 October). — [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Conflicts between the guide and the public page:**
  - Judging start: the public page says 4 November, the guide says 5 November.
  - Fireworks credits: the public page says $100; the guide says $25 for shortlisted teams.
  - The guide's model list adds Muse Voice Transcribe, Muse Glimmer and Muse Spark Open.
  - Rubric weights and anti-projects appear only in the guide.
  - Sources: [public page](https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon) vs [guide](../../gemini-code-1793038385208.md)

#### Meta tooling available (relevant to the 25% "Use of Meta AI Tooling" criterion)
- Meta's model list, fetched 31 October 2026:
  - **muse-spark-1.3** is the "latest version and recommended for new work". It takes text, image, video, audio and PDF input and is tuned for agentic workflows. Audio support is "not fully supported" in 1.3, and 1.2 is recommended for audio.
  - **Muse Wonder (preview)** adds computer use, sub-agents, parallel tool calls and search grounding.
  - **Muse Image** is agentic: it "can search the web and run code before rendering".
  - **Muse Voice Transcribe** does real-time streaming transcription with diarisation, but has no speech synthesis.
  - **SAM 3.1** segments every match for a noun phrase in images and video.
  - **Muse Spark Open** is an 816B MoE with 42B active parameters; **Muse Glimmer** is self-hosted only.
  - Source: [Meta model docs](https://dev.meta.ai/docs/models)
- **Muse Spark 1.3** was released 2 September 2026. Meta reports about 20% fewer tool calls and about 25% fewer tokens than 1.2 (self-reported). The "max" reasoning setting followed on 4 September after a safety hold. Weights remain closed. — [ProPakistani](https://propakistani.pk/2026/09/03/meta-launches-muse-spark-1-3-with-faster-coding-and-smarter-agents/); [RuntimeWire](https://runtimewire.com/article/meta-alexandr-wang-muse-spark-1-3-max-safety-release)
- **Meta Model API public preview** (with Muse Spark 1.1, 9 July 2026): OpenAI-compatible, with structured outputs, parallel tool calls, file handling, prompt caching and **web search that returns cited answers**. Price $1.25 per 1M input tokens and $4.25 per 1M output tokens, initially limited to the US. — [Axios](https://www.axios.com/2026/07/09/meta-ai-spark-model-update-developer); [ProPakistani](https://propakistani.pk/2026/07/11/meta-launches-muse-spark-1-1-with-its-first-paid-ai-model-api/)

#### Past Meta/Llama hackathon winners (this event has no winners yet)
- **Llama 3 hackathon** (San Francisco, May 2024): 354 attendees, 51 projects in 24 hours, co-hosted with Cerebral Valley.
  - 1st: **OpenGlass**, smart glasses built for about $20 that identify what the wearer is looking at.
  - 2nd: **Deb8**, a multi-agent debate arena with a judge agent.
  - 3rd: **Team AAA**, an activation-ablation jailbreak.
  - Notable: SixthSense, an app for Ray-Ban Meta glasses.
  - Source: [Meta AI blog](https://ai.meta.com/blog/llama-3-hackathon-recap-cerebral-valley/)
- **LlamaCon hackathon** (San Francisco, May 2025): 238 developers, 44 projects, $35K in prizes.
  - 1st: **OrgLens**, an expert-matching knowledge graph.
  - 2nd: **Compliance Wizards**, fraud flagging with voice reporting.
  - 3rd: **Llama CCTV Operator**, natural-language video event detection.
  - **Best Llama API Usage: Geo-ML**, which turns long geology reports into structured data and 3D subsurface models.
  - Source: [Meta AI blog](https://ai.meta.com/blog/llamacon-hackathon/)
- **Llama Impact Hackathon:**
  - London (November 2024): more than 200 developers in 56 teams, focused on healthcare, clean energy and social mobility.
  - San Francisco (late 2024): 1,375 participants in 228 teams. The top on-site prize ($5K) went to **Llama Navigator AI**, a Chrome extension.
  - Sources: [Meta newsroom](https://about.fb.com/news/2024/11/metas-llama-impact-hackathon-pioneering-ai-solutions-for-public-good/); [lablab.ai summary](https://lablab.ai/ai-articles/llama-impact-hackathon-sf-summary)

#### Typical comparable AI-hackathon criteria (Devpost and similar)
- **Okta hackathon (Devpost):** three equally weighted criteria: creativity and originality, implementation (including how many sponsor features were used), and potential impact. — [Okta dev forum](https://devforum.okta.com/t/what-are-the-judging-criteria-for-the-hackathon/15842)
- **HackCC 2025 (Devpost):** technical complexity, potential impact, design and execution, and presentation. — [HackCC rules (mirror)](https://kelaenderkoe.pages.dev/patterns-https-hackcc-2025.devpost.com/rules)
- **Interledger hackathon:** quality of the idea (5), potential impact (5), implementation including demonstration and UX (10), out of 20. — [Interledger](https://interledger.org/summit/hackathon/resources/judging)

#### Local repo positioning (observed)
- `docs/SUBMISSION_KIT.md` line 20 names the track "*Meta Global AI Developer Hackathon — Developer Tools & Education Track*". **Neither the guide nor the public page has such a track.** The real tracks are Indie Developer and Startups, and the themes are Build for Your World and Push the Frontier. `docs/19_HACKATHON_RULES.md` already recommends **Push the Frontier** and the **Indie Developer** track. — local files `D:\Meta hackathon\docs\SUBMISSION_KIT.md`, `D:\Meta hackathon\docs\19_HACKATHON_RULES.md`

### Inferences
- **Stage 1 risk:** the biggest threat to ClaimLab's standing is being read as a "Simple 'AI for Education' Chatbot" or "Basic RAG". Because Stage 1 is pass/fail, this risk outweighs any single feature. The submission text, the first 15 seconds of the video, and the README should lead with "agent that reproduces a paper's mechanism as a runnable experiment and verifies its claims", mapped to the guide's wording "accelerate a scientific experiment" under Push the Frontier. Chat should come second.
- **Fix the track label** in `docs/SUBMISSION_KIT.md` before submission. A non-existent track name signals carelessness to Stage 1 reviewers.
- **Use of Meta AI Tooling (25%)** rewards going "beyond basic integration" and surfacing "unexpected capabilities". Calling muse-spark-1.3 for text and tool use alone is basic. Native PDF and image input (reading the paper's figures), SAM 3.1, Muse Image and Voice Transcribe are available and largely unused by ClaimLab, as far as this research can tell. Using TinyFish for web research while Meta's API has native cited web search may cost tooling points unless the choice is justified, or Meta search is offered as the default.
- **Demo (25%)** and the final round, where judges watch videos live, reward a single memorable moment. The Indie track's public wording, "whether it works", plus the rubric's "Does the product hold up live?", make a local-only demo a real liability: a hosted, judge-accessible build or a robust recorded live run matters.
- **Best Agentic Use-Case ($5K)** fits ClaimLab's design (tool selection, experiment execution, a pause-and-return state machine). Present the agent's decision trace explicitly.
- Meta running an "Agents 102: Best Practices for Verifiable Agents" session suggests the organisers value verification. ClaimLab's reviewed recipes, PDF-checked quotes and private-key grading are on-message.
- Past winners suggest judges reward concrete transformations of messy real inputs into structured or visual outputs (Geo-ML, CCTV Operator) and agentic novelty (Deb8). An education tool has not featured among the past winners found here, which reinforces positioning ClaimLab as a scientific-experiment agent.

### Gaps
- The official rules and participant-only portal were not accessed. The participant guide is a user-supplied snapshot of unknown date, and later organiser notices may supersede it. Its rubric weights, anti-project list and prize breakdown could not be confirmed on any public page.
- Judges' names and backgrounds are unpublished.
- This event has no winners yet: judging runs 4/5-8 November and the finals are on 9 November 2026.
- Not verified: whether third-party services (TinyFish) affect Stage 1 or tooling scores, and whether Meta's native search grounding is preferred.
- No rubric weights were published for earlier Meta/Llama hackathons (Llama 3, LlamaCon), so they cannot be compared with this one.

---

## Q4. Which features or demo moments would most strengthen ClaimLab?

### Takeaway
Under the actual rubric (Impact 30, Meta tooling 25, Demo 25, Depth 20) and a deadline about four days away (internal feature freeze 2 November, 22:00 IST, per `docs/19`), the highest-leverage moves are mostly framing and demo work on top of existing features, plus one or two cheap Meta-native additions:
1. A "claim check" moment that runs the toy experiment, compares it with what the paper reports, and states a match or mismatch with its caveats.
2. Showing the paper's own figure next to ClaimLab's plot using Muse Spark's vision input, optionally with SAM 3.1.
3. A small, honest evaluation table.
4. A shareable lesson artifact for the viral and community prizes.
5. Repositioning away from "education chatbot".

Audio narration and multi-paper comparison are lower value: they are commodity features, and Meta has no TTS model.

### Cited Findings
- Muse Spark 1.3 accepts PDF and image input, so it can read the paper's figures. SAM 3.1 segments objects named by a noun phrase. Muse Image "can search the web and run code before rendering". Muse Voice Transcribe streams transcription but offers **no speech synthesis**. — [Meta model docs](https://dev.meta.ai/docs/models)
- The Meta Model API offers native web search with cited answers, plus parallel tool calls and structured outputs. — [Axios](https://www.axios.com/2026/07/09/meta-ai-spark-model-update-developer)
- The rubric asks for unexpected capabilities ("go beyond basic integration") and a live, compelling demo, and the video is a "primary artifact for evaluation". — [Supplied participant guide](../../gemini-code-1793038385208.md)
- **Bonus prizes:** Most Viral ($20K, X engagement through 8 November), Community Vote ($10K), Best Agentic Use-Case ($5K). — [Supplied participant guide](../../gemini-code-1793038385208.md)
- The Paper-replication skill treats each paper claim as a target with recorded evidence and paper-anchored thresholds, and judges completion by checks rather than by the agent's say-so. 37 of 39 scalar anchors fell within thresholds, and its two misses were reported openly. — [HF Papers 2607.02134](https://huggingface.co/papers/2607.02134.md)
- PaperBench grades reproduction against author-approved hierarchical rubrics. — [Emergent Mind](https://www.emergentmind.com/topics/paperbench-benchmark)
- **Shareable formats:** NotebookLM exports slide decks to PPTX and offers multiple shareable overviews. Transformer Explainer reached more than 490,000 users as a free web explainer. — [Google Workspace Updates](https://workspaceupdates.googleblog.com/2026/03/new-ways-to-customize-and-interact-with-your-content-in-NotebookLM.html); [CHI 2026 paper](https://poloclub.github.io/papers/26-chi-transformer-explainer.pdf)
- Interactive lessons improved retention over a PDF (78% versus 67%) in the Learn Your Way trial. Unguarded AI cut later grades by 17%, while a safeguarded tutor mitigated the harm. — [Maginative](https://www.maginative.com/article/learn-your-way-googles-new-ai-transforms-static-textbooks-into-interactive-personalized-lessons/); [EconPapers (PNAS)](https://econpapers.repec.org/RePEc:nas:journl:v:122:y:2025:p:e2422633122)
- Users complain that quotes cannot be found in the source, and that grounding UI clutters the interface. — [r/notebooklm snapshot](https://reddit.sentinel-team.org/subreddits/notebooklm/snapshots/2026-04-29T12%3A24%3A27.513748Z); [arXiv 2602.21059](https://arxiv.org/pdf/2602.21059)
- Claude's visuals are criticised for hiding code and assumptions. — [The Signal](https://thesignal.substack.com/p/claudes-new-interactive-visuals-are)

### Inferences
Ranked by expected rubric gain per unit of effort in the remaining window. Effort labels are rough estimates made without reviewing ClaimLab's code.

1. **The "claim check" demo moment** (Impact, Depth, Demo; effort S-M). Pick one reported qualitative or numerical claim, for example "scaling by 1/sqrt(d_k) keeps softmax from saturating as d grows", or a trend in one of the paper's figures. Have the agent state the claim with its PDF-verified quote, run the toy experiment, and display a verdict: **reproduced trend / not reproduced / out of toy scope**, with the tolerance shown. Borrow the Paper-replication idea of claim → target → recorded evidence. Show an honest "partial" or "mismatch" case once, because it builds credibility. This is the moment that separates ClaimLab from Claude and Gemini visuals and from every reading tool in Q1. The attention lab's three hand-checked recipes are an ideal, low-risk vehicle.
2. **The paper's figure beside ClaimLab's plot, using Meta vision** (Meta tooling 25%; effort S-M). Pass the selected page image or PDF to muse-spark-1.3, ask it to locate and describe the relevant figure, and place the figure crop on the whiteboard next to the experiment plot. Then ask the learner whether the shapes agree. Optionally use **SAM 3.1** to segment the figure region or a specific curve. This is an "unexpected capability" story with little new infrastructure, and it also covers a gap against SciSpace's figure explanation.
3. **Show Meta tooling depth explicitly** (Meta tooling 25%; effort S). In the video and README, list each Meta capability used: reasoning-effort levels per step (low for formatting, high for experiment design), parallel tool calls, structured outputs for the evidence-typed steps, and native PDF input. Consider Meta's native cited web search as the default, with TinyFish as an optional add-on, or explain why TinyFish was chosen. Use muse-spark-1.3, which the docs recommend for new work.
4. **An evaluation-evidence panel** (Depth 20%; Impact; effort S-M). Run a small, honest eval and report it in the README and the video:
   - quote-verification pass and fail rates over N tutor turns;
   - experiment run success rate and median wall-clock time;
   - deterministic grading agreement with the key;
   - cost and latency per lesson in Meta tokens.
   Competitors publish no grounding metrics, and the repo's own handoff rules already require keeping evidence of failed checks.
5. **Repositioning copy** (Stage 1 pass/fail and Impact; effort S). Lead with "agentic experiment lab for research claims" under **Push the Frontier**, citing the guide's phrase "accelerate a scientific experiment". Name the user: someone who has to understand and check a paper's mechanism, such as a student, an engineer evaluating a method, or a reviewer. Cite Bastani (PNAS 2025) and Kestin (2025) in one line as the reason for the private key and active checks. Fix the "Developer Tools & Education Track" label in `docs/SUBMISSION_KIT.md`. Also enter the Best Agentic Use-Case bonus by showing the agent's decision trace: tool chosen, why, the result, and the next move.
6. **A shareable lesson artifact** (Demo, Impact, Most Viral and Community Vote; effort M). Export a finished lesson as a static HTML or PNG card: the claim, the verified quote, the experiment plot with its knob settings, the verdict, and the evidence-tag legend. A shareable card is ideal for the X post behind the $20K viral prize, which counts engagement through 8 November, and for the community gallery. It also partly answers NotebookLM's shareable overviews.
7. **A judge-accessible live build** (Demo 25%, "holds up live"; effort M, dependent on infrastructure and budget). The local-only demo is a risk under "Does the product hold up live?" If hosting is not feasible, record one uncut take of a live session against the real Meta API and say plainly that it is live, with no cached output. This is consistent with the repo's own rule against presenting a cached demo as live.
8. **Voice teach-back with Muse Voice Transcribe** (Meta tooling, active learning; effort M). The learner explains the mechanism aloud, and the transcript is judged as a provisional written answer under the existing policy. Note that muse-spark-1.3 audio is "not fully supported", so use Voice Transcribe for audio, not Spark. This is worth doing only if items 1-5 are finished.
9. **Accessibility basics** (Technical depth polish; effort S): keyboard focus on whiteboard objects, alt text or text equivalents for diagrams and plots, colour-blind-safe evidence-tag colours, and captions in the video. These are cheap, and judges notice them.
10. **Lower priority, defer past the hackathon:**
    - **Audio narration or "audio overviews":** Meta has no TTS, so this needs a non-Meta TTS, dilutes the Meta-tooling story, and copies NotebookLM's strongest feature.
    - **Multi-paper comparison and library search:** commodity territory dominated by Elicit, Consensus, Asta and NotebookLM.
    - Mobile, flashcards and PPTX export.
    - Full-scale reproduction of reported numbers: researcher territory that takes hours per paper.

**Suggested 3-minute video arc** (an inference):
1. (0:00-0:15) The problem: AI reading tools misquote papers and don't let you test claims; show one quote failing verification.
2. (0:15-1:30) Upload, select pages and ask; paged evidence-tagged steps; the whiteboard fills in; the paper's figure appears beside the diagram (Meta vision).
3. (1:30-2:15) The agent writes and runs the experiment; the learner turns a knob; the claim-check verdict appears.
4. (2:15-2:40) A check question graded against the private key, and two-variant mastery.
5. (2:40-3:00) The evaluation table, the Meta capabilities used, and what was built during the event (a disqualification safeguard).

### Gaps
- Not determined in this research: whether ClaimLab already passes page or figure images to muse-spark-1.3, or whether its experiments can be compared automatically with numbers extracted from the paper. That needs a codebase review.
- There is no evidence on how judges weigh third-party tools such as TinyFish against Meta-native capabilities.
- Not verified: hosting feasibility, budget for a public demo within the $150 Meta credit, and US-only API availability for judges or hosting regions (the API preview was initially US-only).
- There is no published evidence on the learning gain from runnable experiment knobs specifically. ClaimLab should not claim measured learning gains without its own data.
