from abc import ABC, abstractmethod
import os
import requests
import torch
from typing import List, Dict
from transformers import AutoModelForCausalLM, AutoTokenizer


class BaseModelInterface(ABC):
    """Abstract base class for model interfaces."""

    @abstractmethod
    def generate_response(
        self, messages: List[Dict[str, str]], max_length: int = 2048
    ) -> str:
        """Generate a response given a list of messages."""
        pass


class OllamaInterface(BaseModelInterface):
    """Interface for Ollama API."""

    def __init__(self, base_url="http://localhost:11434/api/chat", model="llama3"):
        self.base_url = base_url
        self.model = model

    def generate_response(
        self, messages: List[Dict[str, str]], max_length: int = 2048
    ) -> str:
        try:
            response = requests.post(
                self.base_url,
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return data["message"]["content"]
            else:
                raise RuntimeError(f"Error: Status code {response.status_code}")

        except (requests.exceptions.RequestException, KeyError) as e:
            raise RuntimeError(f"Error in generate_response: {str(e)}")


class HuggingFaceInterface(BaseModelInterface):
    """Interface for direct HuggingFace model usage."""

    def __init__(self, model_name="meta-llama/Meta-Llama-3-8B-Instruct", device=None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Loading model on {self.device}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=os.environ["HUGGINGFACE_TOKEN"],
        )

        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with basic configurations
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            token=os.environ["HUGGINGFACE_TOKEN"],
            low_cpu_mem_usage=True,
            max_memory={0: "16GB"},
        )

        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate_response(
        self, messages: List[Dict[str, str]], max_length: int = 2048
    ) -> str:
        """Generate a response to a series of messages using the simplest possible approach."""
        try:
            # Clear cache before starting
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Convert messages to prompt string
            prompt = self._format_simple_prompt(messages)

            # Tokenize the prompt
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=1024,
            ).to(self.device)

            # Generate output
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.1,
                )

            # Decode just the new tokens
            generated_text = self.tokenizer.decode(
                output[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
            )

            # Clear cache after generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return generated_text.strip()

        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise RuntimeError(f"Generation failed: {str(e)}")

    def _format_simple_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a simple prompt string for Llama 3 Instruct.
        Uses the official Meta format from documentation.
        """
        prompt = ""

        # Extract system message if present
        system_msg = None
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
                break

        # Start with user/assistant pairs
        for i, msg in enumerate(messages):
            if msg["role"] == "system":
                continue  # Handle separately

            if msg["role"] == "user":
                # If we have a system message and this is the first user message, include it
                if system_msg and not prompt:
                    prompt += f"<s>[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{msg['content']} [/INST]"
                else:
                    prompt += f"<s>[INST] {msg['content']} [/INST]"

            elif msg["role"] == "assistant" and i < len(messages) - 1:
                # Only add assistant responses if they're not the last message
                prompt += f" {msg['content']}</s>"

        return prompt


# Global model instance (per process)
_model = None


def get_model(use_cluster: bool = False) -> BaseModelInterface:
    """Get or create the model instance for the current process.

    Args:
        use_cluster: If True, use HuggingFace interface, otherwise use Ollama
    """
    global _model
    if _model is None:
        if use_cluster:
            # Initialize model in the current process
            _model = HuggingFaceInterface()
        else:
            _model = OllamaInterface()
    return _model


def is_cluster() -> bool:
    """Detect if we're running on a cluster by checking environment variables."""
    return any(
        [
            os.environ.get("SLURM_JOB_ID"),  # SLURM
            os.environ.get("PBS_JOBID"),  # PBS
            os.environ.get("LSB_JOBID"),  # LSF
            os.environ.get("SGE_TASK_ID"),  # SGE
        ]
    )
