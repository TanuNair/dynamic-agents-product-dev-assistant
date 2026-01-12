class ConversationMemory:
    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get(self):
        return self.messages.copy()

    def summary(self, llm):
        text = "\n".join([f"{m['role']}: {m['content']}" for m in self.messages])

        prompt = f"Summarize the following conversation briefly:\n{text}"
        return llm.invoke(prompt)
