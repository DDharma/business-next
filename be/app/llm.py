from langchain_openai import ChatOpenAI

from .config import get_settings


def make_llm(temperature: float = 0.2, **kwargs) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        base_url=s.lm_studio_url,
        api_key="lm-studio",
        model=s.lm_studio_model,
        temperature=temperature,
        **kwargs,
    )
