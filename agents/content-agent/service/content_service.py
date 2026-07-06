def generate_content(channel: str, topic: str, tone: str) -> dict:
    hook = f"Stop scrolling: here's the fastest way to improve {topic}."
    body = [
        f"Open with a bold opinion tailored for {channel}.",
        "Show a concrete pain point in the first 3 seconds.",
        "Give 3 fast, specific takeaways and end with a call to action.",
    ]
    return {
        "channel": channel,
        "topic": topic,
        "tone": tone,
        "title": f"{channel.title()} content plan for {topic}",
        "script": [hook, *body],
        "cta": "Comment your niche for a tailored version.",
    }

