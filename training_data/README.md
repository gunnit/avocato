# Dataset for Italian Legal Assistant Fine-tuning

This dataset is designed for fine-tuning language models to create a specialized Italian legal assistant. The data is formatted according to OpenAI's chat fine-tuning specifications.

## Dataset Structure

The dataset consists of two main files:

1. `legal_training.jsonl` - Contains the primary training examples
2. `legal_validation.jsonl` - Contains validation examples for evaluating model performance

## Data Format

Each example follows the chat completion format with:
- System message defining the assistant's role
- User message containing a legal query
- Assistant message providing a detailed, professional response with references to Italian law

## Content Coverage

The dataset includes examples covering various aspects of Italian law:
- Civil Procedure (decreto ingiuntivo, termini processuali)
- Contract Law (responsabilità contrattuale)
- Criminal Procedure (costituzione di parte civile)
- Legal Documentation (memorie difensive)
- Damage Calculations (danno biologico)
- Procedural Requirements and Deadlines

## Usage Instructions

1. Use `legal_training.jsonl` as the training file when creating a fine-tuning job
2. Use `legal_validation.jsonl` as the validation file to monitor training progress
3. Recommended model: gpt-4o-mini-2024-07-18
4. Suggested hyperparameters:
   - n_epochs: 3-4
   - batch_size: default
   - learning_rate_multiplier: default

## Fine-tuning Steps

1. Upload the training file:
```python
from openai import OpenAI
client = OpenAI()

client.files.create(
  file=open("legal_training.jsonl", "rb"),
  purpose="fine-tune"
)
```

2. Upload the validation file:
```python
client.files.create(
  file=open("legal_validation.jsonl", "rb"),
  purpose="fine-tune"
)
```

3. Create the fine-tuning job:
```python
client.fine_tuning.jobs.create(
  training_file="file-abc123", # Replace with your training file ID
  validation_file="file-def456", # Replace with your validation file ID
  model="gpt-4o-mini-2024-07-18"
)
```

## Data Quality

Each example in the dataset:
- Contains accurate legal information
- Includes relevant legal citations
- Maintains professional language and tone
- Follows a consistent format
- Provides comprehensive yet concise responses

## Expected Outcomes

The fine-tuned model should be able to:
- Provide accurate Italian legal advice
- Reference relevant laws and jurisprudence
- Maintain professional communication style
- Handle various types of legal queries
- Give structured and detailed responses

## Monitoring Training

Monitor the training progress using:
```python
client.fine_tuning.jobs.list_events(
  fine_tuning_job_id="ftjob-abc123" # Replace with your job ID
)
```

## Best Practices

1. Start with the provided examples and gradually add more specific cases
2. Monitor validation loss to prevent overfitting
3. Test the model with various legal queries before production use
4. Keep the system message consistent across all examples
5. Ensure responses maintain professional legal terminology
