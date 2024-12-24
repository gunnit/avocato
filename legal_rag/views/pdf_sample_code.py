import os
from typing import Optional
from dotenv import load_dotenv
import anthropic
from constants import DEFAULT_ANTHROPIC_MODEL, DEFAULT_MAX_TOKENS
from contract_analysis_schema_german import (
    ContractAnalysisSchema,
    ExtractedContractItem,
)

from anthropic.types import TextBlock

from prompts import SYSTEM_PROMPT, TASKS, TASKS_NAMES
from settings import VERSION, ANTHROPIC_API_KEY, LANGUSE_USER
from utils.document_utils import split_pdf_into_chunks
from utils.llm_utils import calculate_costs_and_usage, construct_messages
from utils.ocr import pdf2txts_cached
from utils.schema_utils import preprocess_results, save_results

from langfuse.decorators import langfuse_context, observe

load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACTS_DIR = os.path.join(CURRENT_DIR, "../contracts")

client = anthropic.Client(api_key=ANTHROPIC_API_KEY)


def extract_data_from_pdf_by_contract_id(contract_id: str, use_cache: bool = False):
    # Find the PDF file with the given contract ID using a mask
    pdf_files = [
        f for f in os.listdir(CONTRACTS_DIR) if f.startswith(f"{contract_id}_")
    ]

    if not pdf_files:
        raise FileNotFoundError(f"No PDF file found for contract ID: {contract_id}")

    # Use the first matching file
    pdf_path = os.path.join(CONTRACTS_DIR, pdf_files[0])

    # Create schema instance with contract_id
    schema = ContractAnalysisSchema(contract_id=contract_id)

    # Extract data using the existing function
    return extract_data_from_pdf(pdf_path, schema, use_cache)


@observe
def extract_data_from_pdf_chunk(messages):
    try:
        # Send the messages to the API
        response = get_response(messages=messages)

        # Debug print the raw response
        if isinstance(response.content, list) and len(response.content) > 0:
            if isinstance(response.content[0], TextBlock):
                text_block: TextBlock = response.content[0]
                print("Raw response text:", text_block.text)  # Debug print

                # Try to find the complete JSON object
                try:
                    # Find the last closing brace
                    last_brace_index = text_block.text.rindex("}")
                    valid_json = "{" + text_block.text[: last_brace_index + 1]

                    model = ContractAnalysisSchema.model_validate_json(valid_json)
                    return model.extracted_items
                except ValueError as json_error:
                    print(f"JSON parsing error: {json_error}")
                    return None
        else:
            print("No response from API")
            return None

    except Exception as e:
        print(
            "Error occurred while calling the API:",
            str(e),
        )
        return None


@observe(as_type="generation")
def get_response(**kwargs):
    langfuse_context.update_current_observation(
        name="Generate response from Anthropic API",
    )
    kwargs_clone = kwargs.copy()
    input = kwargs_clone.pop("messages", None)
    model = kwargs_clone.pop("model", DEFAULT_ANTHROPIC_MODEL)
    max_tokens = kwargs_clone.pop("max_tokens", DEFAULT_MAX_TOKENS)

    if input is None:
        raise ValueError("messages is required")

    langfuse_context.update_current_observation(
        input=input, model=model, metadata=kwargs_clone
    )

    response = client.beta.prompt_caching.messages.create(
        model=model,
        betas=["pdfs-2024-09-25", "prompt-caching-2024-07-31"],
        system=SYSTEM_PROMPT,
        max_tokens=max_tokens,
        **kwargs,
    )

    total_input_tokens, total_output_tokens, total_input_cost, total_output_cost = (
        calculate_costs_and_usage(response.usage)
    )

    # See docs for more details on token counts and usd cost in Langfuse
    # https://langfuse.com/docs/model-usage-and-cost

    langfuse_context.update_current_observation(
        model=model,
        usage={
            "input": total_input_tokens,
            "output": total_output_tokens,
            "input_cost": total_input_cost,
            "output_cost": total_output_cost,
        },
    )
    return response


@observe()
def extract_task_from_pdf(
    base64_chunks: list[str],
    ocr_data: list[str],
    schema: ContractAnalysisSchema,
    task_name: str,
    task_instruction: str,
    task_group_instructions: str,
    use_cache: bool = True,
):

    langfuse_context.update_current_observation(
        name=f"Extract {task_name} from PDF",
        tags=[
            "extract_task_from_pdf",
            f"version_{VERSION}",
            f"task_{task_name}",
            f"contract_{schema.contract_id}",
        ],
    )

    all_results: list[ExtractedContractItem] = []
    for idx, base64_data in enumerate(base64_chunks):
        print(f"Processing chunk {idx}... for task {task_name}")
        if ocr_data:
            ocr_data_str = "\n".join(ocr_data[idx])
        else:
            ocr_data_str = None
        messages = construct_messages(
            schema,
            base64_data,
            task=task_instruction,
            cost_cat_instructions=task_group_instructions,
            ocr_data=ocr_data_str,
            should_cache_document=use_cache,
            should_cache_schema=use_cache,
        )
        extracted_contract_items = extract_data_from_pdf_chunk(messages)

        if extracted_contract_items is None:
            print(f"There was an error extracting data from chunk {idx}")
        else:
            all_results.extend(extracted_contract_items)
    return all_results


@observe()
def extract_data_from_pdf(
    pdf_path: str,
    schema: ContractAnalysisSchema,
    use_cache: bool = True,
    use_ocr: bool = True,
    chunk_size: int = 10,
):
    langfuse_context.update_current_trace(
        name=f"Extract data from PDF contract '{schema.contract_id}'",
        tags=[
            "extract_data_from_pdf",
            f"version_{VERSION}",
            f"contract_{schema.contract_id}",
        ],
        user_id=LANGUSE_USER,
    )
    print(f"Processing contract: {schema.contract_id}")  # Print the PDF path

    # Initialize a list to hold results from each page
    all_tasks_results: list[ExtractedContractItem] = []

    base64_chunks, ocr_data_chunks = split_pdf_into_chunks(pdf_path, chunk_size)
    for task_name, task_group_instructions, task_instruction in zip(
        TASKS_NAMES.keys(), TASKS_NAMES.values(), TASKS
    ):
        task_results = extract_task_from_pdf(
            base64_chunks,
            ocr_data_chunks if use_ocr else [],
            schema,
            task_name,
            task_instruction,
            use_cache,
        )
        all_tasks_results.extend(task_results)

    trace_id = langfuse_context.get_current_trace_id()

    model = preprocess_results(all_tasks_results, schema.contract_id, trace_id)
    return model  # Return the concatenated results


# Example usage
if __name__ == "__main__":
    import argparse

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Extract data from PDF contract")
    parser.add_argument(
        "--pdf-path",
        help="Path to the PDF contract file",
        type=str,
        default="contracts/01-MV_2008-02-21_Edeka_MV.pdf",
    )
    parser.add_argument(
        "--contract-id",
        help="Contract ID (defaults to first 5 chars of PDF filename)",
        default=None,
    )

    args = parser.parse_args()
    pdf_path = args.pdf_path
    if args.contract_id:
        contract_id = args.contract_id
    else:
        contract_id = pdf_path.split("/")[-1][
            :5
        ]  # Extract the first 5 characters of the contract name

    contract_id = pdf_path.split("/")[-1][
        :5
    ]  # Extract the first 5 characters of the contract name
    schema = ContractAnalysisSchema(contract_id=contract_id, extracted_items=[])
    result = extract_data_from_pdf(pdf_path, schema, use_cache=len(TASKS) > 1)
    save_results(result, contract_id)