import os
import random
import html
import requests


TODOIST_TASKS_URL = "https://api.todoist.com/api/v1/tasks"
TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


TODOIST_TOKEN = required_env("TODOIST_TOKEN")
TODOIST_PROJECT_ID = required_env("TODOIST_PROJECT_ID")
TELEGRAM_BOT_TOKEN = required_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = required_env("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")


def get_todoist_tasks(project_id: str) -> list[dict]:
    tasks = []
    cursor = None

    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
    }

    while True:
        params = {
            "project_id": project_id,
            "limit": 200,
        }

        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            TODOIST_TASKS_URL,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        page_tasks = data.get("results", [])
        tasks.extend(page_tasks)

        cursor = data.get("next_cursor")
        if not cursor:
            break

    return tasks


def todoist_priority(priority) -> str:
    # Todoist API: 4 = highest, 1 = normal
    mapping = {
        4: "P1 🔥",
        3: "P2",
        2: "P3",
        1: "P4",
    }
    return mapping.get(priority, "P4")

def send_to_groq(self, content):
    from groq import Groq

    client = Groq(
        api_key=self.GROQ_API_KEY,
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except requests.exceptions.RequestException as e:
        return f"Error calling Groq API: {str(e)}"


def format_task(task: dict, index: int) -> str:
    title = html.escape(task.get("content", "Untitled task"))
    description = html.escape(task.get("description") or "")

    due = task.get("due") or {}
    due_text = due.get("string") or due.get("date") or "No due date"

    labels = task.get("labels") or []
    labels_text = ", ".join(labels) if labels else "No labels"
    # ai_summary = send_to_groq(f"summarize: {title}")

    # priority = todoist_priority(task.get("priority"))

    output = (
        f"<b>{index}. {title}</b>\n"
        # f"<b>AI Summary: {ai_summary}</b>\n"
        # f"Priority: {priority}\n"
        f"Due: {html.escape(due_text)}\n"
        f"Labels: {html.escape(labels_text)}"
    )

    if description:
        output += f"\nNotes: {description}"

    return output


def build_message(tasks: list[dict]) -> str:
    if not tasks:
        return "No active tasks found in this Todoist project."

    selected_tasks = random.sample(tasks, k=min(3, len(tasks)))

    formatted_tasks = [
        format_task(task, index)
        for index, task in enumerate(selected_tasks, start=1)
    ]

    return "<b>🎯 Random 3 Todoist Tasks</b>\n\n" + "\n\n".join(formatted_tasks)


def send_telegram_message(message: str) -> None:
    url = TELEGRAM_SEND_URL.format(token=TELEGRAM_BOT_TOKEN)

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()


def main() -> None:
    tasks = get_todoist_tasks(TODOIST_PROJECT_ID)
    message = build_message(tasks)
    send_telegram_message(message)
    print("Sent random Todoist tasks to Telegram.")


if __name__ == "__main__":
    main()