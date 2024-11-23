# Dataset for Italian Legal Assistant Fine-tuning

This dataset is designed for fine-tuning language models to create a specialized Italian legal assistant, with particular focus on recent criminal law jurisprudence from the Cassazione.

## Dataset Structure

The dataset consists of two main files:

1. `legal_training.jsonl` - Contains 30 training examples covering both civil and criminal law
2. `legal_validation.jsonl` - Contains 13 validation examples for evaluating model performance

## Content Coverage

### Recent Criminal Law Jurisprudence (2024)
- Ne bis in idem principles
  - Administrative/criminal proceedings intersection
  - International cooperation in evidence gathering
- Precautionary Measures
  - Tempus regit actum application
  - Restraining orders in plea bargaining
- Public Official Offenses
  - Political criticism defense
  - Local government officials' qualification
- Economic Crimes
  - Embezzlement by public service employees
  - Unauthorized practice of law
- Procedural Issues
  - Jurisdictional competence
  - International cooperation
  - Evidence admissibility

### Criminal Procedure
- Plea Bargaining
- Jurisdictional Competence
- Evidence Rules
- Appeal Procedures
- Statute of Limitations
- International Cooperation
  - Transnational intercepts
  - Evidence sharing

### Civil Law
- Civil Procedure
- Contract Law
- Legal Documentation
- Damage Calculations
- Procedural Requirements

## Data Format

Each example follows the chat completion format with:
- System message defining the assistant's role
- User message containing a legal query
- Assistant message providing:
  - Relevant laws and articles
  - Recent Cassazione decisions with citations
  - Legal principles and interpretation
  - Procedural requirements
  - Practical implications

## Usage Instructions

1. Use `legal_training.jsonl` as the training file
2. Use `legal_validation.jsonl` as the validation file
3. Recommended model: gpt-4o-mini-2024-07-18
4. Suggested hyperparameters:
   - n_epochs: 3-4
   - batch_size: default
   - learning_rate_multiplier: default

## Expected Capabilities

The fine-tuned model should be able to:
1. Provide accurate legal advice incorporating 2024 jurisprudence
2. Reference specific Cassazione decisions with proper citations
3. Explain complex legal principles and their practical application
4. Apply legal rules to specific situations
5. Identify relevant procedural requirements
6. Maintain professional legal terminology
7. Structure responses with clear legal reasoning
8. Handle international and transnational legal issues

## Data Quality Assurance

Each example has been verified for:
1. Legal Accuracy
- Current and correct legal principles
- Accurate citation of recent jurisprudence
- Proper interpretation of laws

2. Professional Standards
- Formal legal terminology
- Clear structure and organization
- Logical reasoning flow

3. Practical Utility
- Real-world applicability
- Procedural guidance
- Implementation considerations

4. Citation Quality
- Complete references to laws
- Specific Cassazione decisions
- Relevant articles and sections

## Best Practices for Use

1. Regular Updates
- Monitor new Cassazione decisions
- Update examples with recent jurisprudence
- Remove outdated legal interpretations

2. Quality Control
- Verify legal accuracy
- Check citation formats
- Ensure professional terminology
- Test practical applicability

3. Implementation
- Start with recent examples
- Monitor validation metrics
- Test across different legal scenarios
- Maintain consistent formatting

## Training Recommendations

1. Initial Training
- Begin with core legal principles
- Focus on recent jurisprudence
- Emphasize practical application

2. Validation Process
- Test against known legal scenarios
- Verify citation accuracy
- Check reasoning consistency

3. Ongoing Maintenance
- Regular updates with new decisions
- Removal of obsolete interpretations
- Quality assurance reviews
