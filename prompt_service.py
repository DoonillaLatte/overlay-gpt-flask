from registry import prompt_registry

def handle_prompt(prompt_type, text):
    prompt = prompt_registry.get(prompt_type)
    if not prompt:
        return "Unsupported prompt type"
    return prompt.generate_prompt(text)
