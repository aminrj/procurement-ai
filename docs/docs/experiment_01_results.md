# Experiment 1: Prompt Engineering Impact

## Hypothesis
More specific prompts will increase confidence scores.

## Test Setup
- Same tender: "AI-Powered Cybersecurity Platform"
- 3 prompt variations: Vague, Criteria-based, Example-based
- Temperature: 0.1 (for consistency)
- Model: Llama 3.1 8B

## Results

| Prompt Version | Relevant | Confidence | Response Time |
|----------------|----------|------------|---------------|
| V1 (Vague)     | True     | 0.85       | Not measured |
| V2 (Criteria)  | True     | 0.92       | Not measured |
| V3 (Examples)  | True     | 0.95       | Not measured |

## Key Findings

1. **Example-based prompts achieve highest confidence**: 11.8% higher than vague, 3.3% higher than criteria
2. **Progressive improvement with specificity**: Each version shows increasing confidence
3. **All prompts correctly identify relevance**: 100% accuracy on this tender

## Reasoning Quality

V1: "The tender seeks an AI‑powered cybersecurity platform tailored for critical infrastructure, which aligns with our AI and cybersecurity expertise" (basic alignment)

V2: "The tender seeks an AI-based threat detection and response system for monitoring network traffic across government infrastructure, which directly aligns with our capabilities in AI, cybersecurity, and software development" (detailed technical match)

V3: "The tender explicitly requests an AI-based threat detection and response system for critical infrastructure monitoring, which perfectly matches the AI threat detection example" (reference-based with high specificity)

## Recommendation
Use example-based prompts (V3) for production:
- Highest confidence (0.95)
- Most specific reasoning
- Clear reference framework
- Demonstrates few-shot learning effectiveness

## Next Steps
Test on 20 diverse tenders to validate consistency across different tender types and complexity levels.