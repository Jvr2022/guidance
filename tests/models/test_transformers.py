import pytest

from guidance import gen, select, models, assistant, system, user

from ..utils import get_model


def test_gpt2():
    gpt2 = get_model("transformers:gpt2")
    lm = gpt2 + "this is a test" + gen("test", max_tokens=10)
    assert len(str(lm)) > len("this is a test")


def test_recursion_error():
    """This checks for an infinite recursion error resulting from a terminal node at the root of a grammar."""
    gpt2 = get_model("transformers:gpt2")

    # define a guidance program that adapts a proverb
    lm = (
        gpt2
        + f"""Tweak this proverb to apply to model instructions instead.
    {gen('verse', max_tokens=2)}
    """
    )
    assert len(str(lm)) > len(
        "Tweak this proverb to apply to model instructions instead.\n\n"
    )


TRANSFORMER_MODELS = {
    "gpt2": {},
    # "microsoft/phi-2": {"trust_remote_code": True},
}


@pytest.mark.parametrize(["model_name", "model_kwargs"], TRANSFORMER_MODELS.items())
def test_transformer_smoke_gen(model_name, model_kwargs):
    my_model = get_model(f"transformers:{model_name}", **model_kwargs)

    prompt = "How many sides has a triangle?"
    lm = my_model + prompt + gen(name="answer", max_tokens=2)
    assert len(lm["answer"]) > 0, f"Output: {lm['answer']}"
    # Inexact, but at least make sure not too much was produced
    assert len(lm["answer"]) < 8, f"Output: {lm['answer']}"


@pytest.mark.parametrize(["model_name", "model_kwargs"], TRANSFORMER_MODELS.items())
def test_transformer_smoke_select(model_name, model_kwargs):
    my_model = get_model(f"transformers:{model_name}", **model_kwargs)

    prompt = """How many sides has a triangle?

p) 4
t) 3
w) 10"""
    lm = my_model + prompt + select(["p", "t", "w"], name="answer")
    assert lm["answer"] in ["p", "t", "w"]


pytest.mark.skip("Don't overload the build machines")
def test_phi3_transformers_orig():
    import torch
    from transformers import AutoModelForCausalLM, pipeline, AutoTokenizer

    torch.random.manual_seed(0)
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct", 
        device_map="mps",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )

    generation_args = {
        "max_new_tokens": 5,
        "return_full_text": True,
        "temperature": 0.0,
        "do_sample": False,
    }

    input_text = "You are a counting bot. Just keep counting numbers. 1,2,3,4"
    output = pipe(input_text, **generation_args)
    assert "5" in (output[0]['generated_text'])


@pytest.mark.skip("Don't overload the build machines")
def test_phi3_loading():
    lm = models.Transformers(
        r"microsoft/Phi-3-mini-4k-instruct", trust_remote_code=True
    )
    lm += f"""You are a counting bot. Just keep counting numbers. 1,2,3,4, <|assistant|>"""
    lm += gen("five", max_tokens=10)
    assert "5" in lm["five"]


@pytest.mark.skip("Don't overload the build machines")
def test_phi3_chat():
    lm = models.Transformers(
        r"meta-llama/Meta-Llama-3-8B-Instruct", trust_remote_code=True
    )
    # System prompts raise exceptions for phi-3 models that don't have a system role.
    # TODO [HN]: Decide if we should perhaps merge with first user message as a default w/ warning?
    # with system():
    #     lm += "You are a counting bot. Just keep counting numbers."
    # lm += "You are a counting bot. Just keep counting numbers."
    with user():
        lm += "Tell me what you want, what you really really want."
    with assistant():
        lm += "I'll tell you what I want, what I really really want." 
        lm += gen(name="five", max_tokens=1)

    assert len(lm["five"] > 0) 


@pytest.mark.skip("Don't overload the build machines")
def test_phi3_failure_minimal():
    lm = models.Transformers(
        r"microsoft/Phi-3-mini-4k-instruct", trust_remote_code=True, device_map="mps"
    )
    # NOTE: This SHOULD NOT raise an exception, but guidance currently has a bug where 
    # directly passing in newlines next to special tokens for a tokenizer that does rstrip on those tokens
    # (like phi-3) will cause a tokenization mismatch issue. 
    # We're leaving this test in so that we can reliably reproduce and debug this in the future. 
    with pytest.raises(Exception):
        lm += f"""numbers.<|user|>\n1,2,3,4<|end|>\n<|assistant|>\n"""
        lm += gen("five", max_tokens=10)

@pytest.mark.skip("Don't overload the build machines")
def test_phi3_chat_fixed():
    lm = models.Transformers(
        r"microsoft/Phi-3-mini-4k-instruct", trust_remote_code=True, device_map="mps"
    )

    lm += "You are a counting bot. Just keep counting numbers."
    with user():
        lm += "1,2,3,4"
    with assistant():
        lm += gen(name="five", max_tokens=10)

    assert "5" in lm["five"]

