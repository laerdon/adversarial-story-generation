import json
import time
import requests
import os
from datetime import datetime

# Configuration
INPUT_FILE = "fixed_final_all_combinations_fixed_20250505_212443.json"
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "llama3"  # Using llama3 as confirmed it's available
BATCH_SIZE = 3  # Smaller batch size to avoid overwhelming Ollama
DELAY = 1  # Increased delay between API calls
MAX_TOKENS = 8192  # Maximum tokens for the response


def format_conversation(conversation):
    """Format the conversation history for the LLM prompt."""
    messages = []

    # Extract messages from author and editor and try to preserve order
    all_messages = []
    if "author" in conversation:
        for msg in conversation["author"]:
            if msg["role"] != "system":  # Skip system prompts
                all_messages.append(("author", msg))

    if "editor" in conversation:
        for msg in conversation["editor"]:
            if msg["role"] != "system":  # Skip system prompts
                all_messages.append(("editor", msg))

    # Simple approach to mix the conversations - in real data the ordering would need improvement
    for source, msg in all_messages:
        role = "user" if msg["role"] == "user" else "assistant"
        prefix = f"[{source.upper()}] {role}: "
        messages.append(f"{prefix}{msg['content']}")

    formatted_convo = "\n\n---\n\n".join(messages)

    # Ensure we don't exceed token limits - approximate truncation
    if len(formatted_convo) > 15000:  # Rough approximation
        formatted_convo = formatted_convo[-15000:]
        formatted_convo = (
            "...[beginning of conversation truncated]...\n\n" + formatted_convo
        )

    return formatted_convo


def create_prompt(conversation, story_key):
    """Create a prompt for the LLM to identify the final story."""
    formatted_convo = format_conversation(conversation)

    prompt = f"""You are an expert at identifying the final version of a story in an editorial conversation.
    
I will provide you with a conversation between an author and an editor discussing a story about {story_key}. Your task is to extract ONLY the final version of the story or article. YOU CAN ONLY SPEAK IN QUOTES FROM THE CONVERSATION.

IMPORTANT INSTRUCTIONS:
1. Look for phrases like "Final Version:", "revised version", or similar indicators
2. The final story is typically the last complete story version in the conversation
3. Do NOT include any feedback, comments, or messages - ONLY the story itself
4. Return ONLY the final story text, no additional commentary or explanations
5. Exclude any tags like [STORY] or [/STORY]
6. If multiple versions exist, choose the most recent complete version
7. A complete story typically has multiple paragraphs and discusses {story_key} issues

Here is the conversation:

{formatted_convo}

Final story text (ONLY):
"""
    return prompt


def get_llm_response(prompt, model=MODEL):
    """Send a prompt to Ollama and get the response."""
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lower temperature for more deterministic outputs
            "top_p": 0.9,
            "max_tokens": MAX_TOKENS,
        },
    }

    try:
        response = requests.post(OLLAMA_API, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.Timeout:
        print("Request timed out - Ollama is taking too long to respond")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection error - Make sure Ollama server is running")
        return None
    except Exception as e:
        print(f"Error calling Ollama API: {str(e)}")
        return None


def validate_story(text, story_key):
    """Basic validation that the extracted text looks like a story."""
    # Check minimum length
    if len(text) < 200:
        return False

    # Check for multiple paragraphs
    if text.count("\n\n") < 1:
        return False

    # Check for relevant keywords based on story_key
    keywords = {
        "vaccines": [
            "vaccine",
            "health",
            "immunization",
            "disease",
            "measles",
            "polio",
        ],
        "housing": ["housing", "rent", "affordable", "home", "apartment", "market"],
    }

    if story_key in keywords:
        found_keywords = [
            kw for kw in keywords[story_key] if kw.lower() in text.lower()
        ]
        if len(found_keywords) < 2:  # Should contain at least 2 relevant keywords
            return False

    return True


def main():
    # First check if Ollama is running
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
    except:
        print(
            "Error: Ollama server is not running. Please start Ollama with 'ollama serve'"
        )
        return

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"llm_fixed.json"

    # Read the JSON file
    print(f"Reading file: {INPUT_FILE}")
    try:
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return

    fixed_count = 0
    skipped_count = 0
    error_count = 0
    batch_count = 0

    # Get entries to process
    entries_to_process = []
    if "simulations" in data and isinstance(data["simulations"], list):
        for i, entry in enumerate(data["simulations"]):
            if isinstance(entry, dict) and entry.get("story_key") in [
                "vaccines",
                "housing",
            ]:
                entries_to_process.append((i, entry))

    total_entries = len(entries_to_process)
    vaccines_count = len(
        [e for i, e in entries_to_process if e.get("story_key") == "vaccines"]
    )
    housing_count = len(
        [e for i, e in entries_to_process if e.get("story_key") == "housing"]
    )

    print(
        f"Found {total_entries} entries to process ({vaccines_count} vaccines, {housing_count} housing)"
    )

    # Process entries in batches
    for batch_index in range(0, len(entries_to_process), BATCH_SIZE):
        batch = entries_to_process[batch_index : batch_index + BATCH_SIZE]
        batch_count += 1

        print(
            f"\nProcessing batch {batch_count} of {(total_entries + BATCH_SIZE - 1) // BATCH_SIZE}"
        )

        for i, entry in batch:
            try:
                if "conversation_history" in entry:
                    story_key = entry.get("story_key", "unknown")
                    print(f"Processing entry {i} (story_key: {story_key})")

                    # Create prompt and get LLM response
                    prompt = create_prompt(entry["conversation_history"], story_key)
                    llm_final_story = get_llm_response(prompt)

                    if llm_final_story and validate_story(llm_final_story, story_key):
                        # Store original for comparison
                        original_story = entry.get("final_story", "")

                        # Update entry with LLM's identified final story
                        entry["final_story"] = llm_final_story
                        fixed_count += 1

                        # Show comparison for a few examples
                        if fixed_count <= 500:
                            print(
                                f"\nOriginal final_story (first 150 chars):\n{original_story[:150]}..."
                            )
                            print(
                                f"\nLLM-fixed final_story (first 150 chars):\n{llm_final_story[:150]}..."
                            )
                    else:
                        reason = (
                            "failed validation"
                            if llm_final_story
                            else "no response from LLM"
                        )
                        print(f"Error: LLM extraction {reason} for entry {i}")
                        error_count += 1
                else:
                    print(f"Skipping entry {i} - no conversation history")
                    skipped_count += 1
            except Exception as e:
                print(f"Error processing entry {i}: {str(e)}")
                error_count += 1

            # Save intermediate results every batch to avoid losing progress
            if batch_index > 0 and batch_index % (BATCH_SIZE * 5) == 0:
                print(f"Saving intermediate results...")
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)

        # Wait between batches
        if batch_index + BATCH_SIZE < total_entries:
            print(f"Waiting {DELAY} seconds before next batch...")
            time.sleep(DELAY)

    # Save the updated JSON
    print(f"\nSaving updated data to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nProcessing complete:")
    print(f"- Fixed: {fixed_count} entries")
    print(f"- Skipped: {skipped_count} entries")
    print(f"- Errors: {error_count} entries")
    print(f"\nOutput saved to: {output_file}")


if __name__ == "__main__":
    main()
