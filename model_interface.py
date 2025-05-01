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
                timeout=3600,
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

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=os.environ["HUGGINGFACE_TOKEN"],
        )

        # Set pad token to eos token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # Configure model with optimized memory settings
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            token=os.environ["HUGGINGFACE_TOKEN"],
            low_cpu_mem_usage=True,
            max_memory={0: "20GB"},  # Using most of our available GPU memory
        ).to(
            self.device
        )  # Ensure model is on the correct device

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a prompt string for Llama 3 Instruct."""
        formatted_prompt = ""

        # Find system message if it exists
        system_msg = next(
            (msg["content"] for msg in messages if msg["role"] == "system"), None
        )

        # Start conversation
        formatted_prompt = "<s>"

        # Add system message if it exists
        if system_msg:
            formatted_prompt += f"[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n"
        else:
            formatted_prompt += "[INST] "

        # Add the conversation history
        for i, msg in enumerate(messages):
            if msg["role"] == "system":
                continue

            if msg["role"] == "user":
                if i == len(messages) - 1:  # If this is the last message
                    formatted_prompt += f"{msg['content']} [/INST]"
                else:
                    formatted_prompt += f"{msg['content']} [/INST]"
            elif msg["role"] == "assistant":
                formatted_prompt += f" {msg['content']}</s><s>[INST] "

        return formatted_prompt

    def generate_response(
        self, messages: List[Dict[str, str]], max_length: int = 2048
    ) -> str:
        prompt = self._format_messages(messages)

        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True,
        )

        # Create position IDs tensor
        position_ids = torch.arange(len(inputs["input_ids"][0])).unsqueeze(0)

        # Move all tensors to the correct device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        position_ids = position_ids.to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                position_ids=position_ids,  # Explicitly pass position IDs
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Only decode the new tokens
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        return response.strip()


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
