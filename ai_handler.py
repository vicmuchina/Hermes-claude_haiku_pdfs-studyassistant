import threading
from config import client, model

def start_ai_thread(self):
    threading.Thread(target=ai_worker, args=(self,), daemon=True).start()

def ai_worker(self):
    while True:
        task_type, content = self.ai_queue.get()
        if task_type == "highlight":
            self.messages.append({"role": "user", "content": f"Analyze this highlighted text: {content}"})
        elif task_type == "message":
            self.messages.append({"role": "user", "content": content})
        elif task_type == "pdf":
            self.messages.append({"role": "user", "content": f"Here's the full content of the PDF: {content[:1000]}... [truncated]"})
        
        response = completion(self.messages)
        self.messages.append({"role": "assistant", "content": response})
        self.root.after(0, self.update_chat_history, f"AI: {response}\n")
        self.ai_queue.task_done()

def completion(messages):
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return completion.choices[0].message.content