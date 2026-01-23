# Learning Path

**Master LLM Engineering in 6 Hours**

This guide will take you from zero to building production-ready AI systems.

---

## Who Is This For?

- **Python developers** wanting to learn LLM engineering
- **AI enthusiasts** looking for practical projects  
- **Procurement professionals** interested in automation
- **Students/job seekers** building portfolio projects

**Prerequisites:**
- Basic Python knowledge (functions, async/await helpful but not required)
- Ability to install software
- Curiosity and willingness to experiment

---

## The Fast.ai Approach

1. **Start with working code** - Run it first, understand later
2. **Learn by doing** - Build real things, not toy examples
3. **Progressive complexity** - Each step builds on the last
4. **Iterate quickly** - Make changes, see results immediately

---

## Step-by-Step Journey

### Phase 1: Foundations (45 minutes)

#### [01_hello_llm.ipynb](learn/01_hello_llm.ipynb) - 15 minutes
**What:** Make your first LLM API call  
**Why:** Understand the basics of talking to AI models  
**Outcome:** You can call an LLM and get responses

#### [02_structured_outputs.ipynb](learn/02_structured_outputs.ipynb) - 30 minutes
**What:** Get JSON instead of free text  
**Why:** Reliable, predictable outputs for production  
**Outcome:** You can extract structured data from LLMs

---

### Phase 2: Building Agents (3 hours)

#### [03_filter_agent.ipynb](learn/03_filter_agent.ipynb) - 1 hour
**What:** Build an AI that classifies tenders  
**Why:** Learn prompt engineering and classification  
**Outcome:** Working agent that filters relevant opportunities

**Key Concepts:**
- Prompt engineering patterns
- Temperature settings
- Error handling
- Confidence scores

#### [04_rating_agent.ipynb](learn/04_rating_agent.ipynb) - 1 hour
**What:** Build an AI that scores opportunities  
**Why:** Multi-dimensional evaluation with reasoning  
**Outcome:** Agent that provides actionable ratings

**Key Concepts:**
- Complex prompts with multiple criteria
- Structured reasoning
- Business logic integration

#### [05_doc_generator.ipynb](learn/05_doc_generator.ipynb) - 1 hour
**What:** Generate professional bid documents  
**Why:** Creative generation with constraints  
**Outcome:** AI that writes persuasive proposals

**Key Concepts:**
- Higher temperature for creativity
- Context management
- Long-form generation

---

### Phase 3: Production Systems (2 hours)

#### [06_orchestration.ipynb](learn/06_orchestration.ipynb) - 1 hour
**What:** Chain agents into a workflow  
**Why:** Build complete AI systems  
**Outcome:** Full pipeline from input to output

**Key Concepts:**
- Sequential workflows
- Conditional logic
- Error recovery
- Performance monitoring

#### [07_production_ready.ipynb](learn/07_production_ready.ipynb) - 1 hour
**What:** Deploy your system  
**Why:** Make it usable by others  
**Outcome:** Deployed AI system

**Key Concepts:**
- API design
- Configuration management
- Logging and monitoring
- Testing strategies

---

## Deep Dive Experiments

Once you've completed the main path, explore these advanced topics:

### [exp_01_prompt_engineering.ipynb](learn/experiments/exp_01_prompt_engineering.ipynb)
Compare prompt strategies and measure impact on accuracy

### [exp_02_temperature.ipynb](learn/experiments/exp_02_temperature.ipynb)
Understand temperature's effect on output quality

### [exp_03_models.ipynb](learn/experiments/exp_03_models.ipynb)
Benchmark different model sizes and providers

### [exp_04_lmstudio_vs_groq.ipynb](learn/experiments/exp_04_lmstudio_vs_groq.ipynb)
Local vs cloud: cost, speed, and quality tradeoffs

### [exp_05_langgraph.ipynb](learn/experiments/exp_05_langgraph.ipynb)
Advanced orchestration with LangGraph

---

## Learning Tips

### 1. Run Before Reading
Don't just read the notebooks - **run every cell**. See the outputs, modify the code, break things and fix them.

### 2. Experiment Freely
- Change prompts and see what happens
- Adjust temperatures
- Try different inputs
- Break the code intentionally

### 3. Document Your Journey
Keep notes about:
- What worked and what didn't
- Interesting prompt patterns you discover
- Performance characteristics you observe

### 4. Build Your Own Version
After completing each notebook, try building a variation:
- Different domain (HR, sales, legal)
- Different use case
- Different architecture

---

## What You'll Know After This Path

### Technical Skills
- LLM API integration  
- Prompt engineering  
- Structured outputs with Pydantic  
- Multi-agent systems  
- Async Python programming  
- Production deployment  

### Practical Knowledge
- When to use LLMs vs traditional code  
- How to handle LLM limitations  
- Cost optimization strategies  
- Testing AI systems  
- Debugging LLM applications  

### Portfolio Projects
- Working AI system with code on GitHub  
- Blog posts documenting your learning  
- Benchmark results and experiments  
- Deployed demo others can try  

---

## After Completion

### Next Steps

1. **Customize for your domain**
   - Replace procurement with your industry
   - Adapt the agents for your use cases

2. **Add advanced features**
   - Vector database for semantic search
   - Fine-tuning for domain expertise
   - Multi-modal capabilities (images, PDFs)

3. **Share your work**
   - Blog about your experiments
   - Create YouTube tutorials
   - Contribute improvements back

### Job Opportunities

With these skills, you're qualified for:
- LLM Engineer / AI Engineer roles
- ML Engineer positions working with LLMs
- Full-stack developer with AI capabilities
- Technical founder building AI products

---

## Track Your Progress

Use this checklist:

- [ ] Completed 01_hello_llm.ipynb
- [ ] Completed 02_structured_outputs.ipynb
- [ ] Completed 03_filter_agent.ipynb
- [ ] Completed 04_rating_agent.ipynb
- [ ] Completed 05_doc_generator.ipynb
- [ ] Completed 06_orchestration.ipynb
- [ ] Completed 07_production_ready.ipynb
- [ ] Completed at least 2 experiments
- [ ] Built custom variation
- [ ] Deployed working system
- [ ] Wrote blog post about learning
- [ ] Shared project publicly

---

## Get Help

- **Stuck?** Check the [Issues](https://github.com/yourusername/procurement-ai/issues)
- **Questions?** Use [Discussions](https://github.com/yourusername/procurement-ai/discussions)
- **Found a bug?** Submit a PR!

---

## Celebrate Milestones

After each phase, take a moment to appreciate what you've built:

- **After Phase 1:** You can interact with LLMs programmatically
- **After Phase 2:** You've built a complete AI agent system
- **After Phase 3:** You have a deployable production system

**This is a significant achievement!**

---

**Ready to start? Open [01_hello_llm.ipynb](learn/01_hello_llm.ipynb) and let's go!**
