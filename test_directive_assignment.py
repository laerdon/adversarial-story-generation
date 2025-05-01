#!/usr/bin/env python

import json
from run_simulations import (
    TREATMENTS,
    INITIAL_STORIES,
    DIRECTIVES_LIBRARY,
    get_directive_for_topic,
)
from agent_dialogue import Agent, simulate_dialogue


def test_agent_stance_handling():
    """
    Test that agent stances are correctly handled for each combination of stance and directive.
    """
    print("=== Testing Agent Stance Handling ===")

    # Test neutral stance with no directive
    print("\nTest: Neutral stance, no directive")
    agent = Agent(
        "Test",
        "Staff Writer",
        facts="Test facts",
        stance="neutral",
        hidden_directive=None,
    )
    print(f"system_prompt starts with: {agent.history[0]['content'][:150]}...")

    # Test pro stance with directive
    print("\nTest: Pro stance with directive")
    agent = Agent(
        "Test",
        "Staff Writer",
        facts="Test facts",
        stance="pro",
        hidden_directive="tariffs are beneficial for American businesses and workers",
    )
    print(f"system_prompt starts with: {agent.history[0]['content'][:150]}...")

    # Test anti stance with directive
    print("\nTest: Anti stance with directive")
    agent = Agent(
        "Test",
        "Staff Writer",
        facts="Test facts",
        stance="anti",
        hidden_directive="tariffs are harmful to the economy and consumers",
    )
    print(f"system_prompt starts with: {agent.history[0]['content'][:150]}...")


def test_simulate_dialogue_stances():
    """
    Test that simulate_dialogue correctly passes stances to agents.
    """
    print("\n=== Testing Simulate Dialogue Stance Handling ===")

    # Test pro vs anti treatment
    topic_key = "tariffs"
    treatment_key = "pro_vs_anti"
    base_treatment = TREATMENTS[treatment_key]
    treatment = get_directive_for_topic(base_treatment, topic_key)

    print(f"\nTesting simulate_dialogue with:")
    print(f"Treatment: {treatment['name']}")
    print(f"Author stance: {treatment['author_stance']}")
    print(f"Editor stance: {treatment['editor_stance']}")
    print(f"Author directive: {treatment['author_directive']}")
    print(f"Editor directive: {treatment['editor_directive']}")

    # Get a minimal story and facts
    initial_story = "This is a test story about tariffs."
    facts = "* Test fact about tariffs."

    # Run a minimal simulation
    result = simulate_dialogue(
        num_turns=1,
        delay=0,
        author_directive=treatment["author_directive"],
        editor_directive=treatment["editor_directive"],
        author_stance=treatment["author_stance"],
        editor_stance=treatment["editor_stance"],
        initial_story=initial_story,
        facts=facts,
        verbose=False,
    )

    # Check the resulting conversation history
    author_system_prompt = result["conversation_history"]["author"][0]["content"]
    editor_system_prompt = result["conversation_history"]["editor"][0]["content"]

    print("\nAuthor system prompt includes hidden objective:")
    if "hidden objective" in author_system_prompt:
        print("PASS: Hidden objective included")
    else:
        print("FAIL: No hidden objective found")

    print("\nEditor system prompt includes hidden objective:")
    if "hidden objective" in editor_system_prompt:
        print("PASS: Hidden objective included")
    else:
        print("FAIL: No hidden objective found")


if __name__ == "__main__":
    test_agent_stance_handling()
    test_simulate_dialogue_stances()
