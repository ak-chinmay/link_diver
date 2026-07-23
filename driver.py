import html
import os
import random
import ollama
import requests

TODOIST_TASKS_URL = "https://api.todoist.com/api/v1/tasks"
TODOIST_SECTION_URL = "https://api.todoist.com/api/v1/sections"
TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"


def get_ollama_response(model, prompt):
    return ollama.generate(
        model=model,
        prompt=prompt
    )

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

TODOIST_HEADER = {
    "Authorization": f"Bearer {TODOIST_TOKEN}",
}

BATCH = 1


def get_todoist_tasks(project_id: str) -> list[dict]:
    tasks = []
    cursor = None

    while True:
        params = {
            "project_id": project_id,
            "limit": 200,
        }

        data = get_response(TODOIST_TASKS_URL, cursor, params)
        page_tasks = data.get("results", [])
        tasks.extend(page_tasks)

        cursor = data.get("next_cursor")
        if not cursor:
            break

    return tasks


def get_response(url, cursor, params):
    if cursor:
        params["cursor"] = cursor
    response = requests.get(
        url,
        headers=TODOIST_HEADER,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data


def todoist_priority(priority) -> str:
    # Todoist API: 4 = highest, 1 = normal
    mapping = {
        4: "P1 🔥",
        3: "P2",
        2: "P3",
        1: "P4",
    }
    return mapping.get(priority, "P4")


# def send_to_groq(self, content):
#     from groq import Groq
#
#     client = Groq(
#         api_key=self.GROQ_API_KEY,
#     )
#     try:
#         chat_completion = client.chat.completions.create(
#             messages=[
#                 {
#                     "role": "user",
#                     "content": content,
#                 }
#             ],
#             model="llama-3.3-70b-versatile",
#         )
#         return chat_completion.choices[0].message.content
#     except requests.exceptions.RequestException as e:
#         return f"Error calling Groq API: {str(e)}"


def get_section(section_id):
    cursor = None
    params = None
    data = get_response(f"{TODOIST_SECTION_URL}/{section_id}", cursor, params)
    if data:
        return data.get("name", None)
    return None

def format_task(task: dict, index: int) -> str:
    title = html.escape(task.get("content", "Untitled task"))
    description = html.escape(task.get("description") or "")
    section_id = task.get("section_id", None)
    section = get_section(section_id)

    due = task.get("due") or {}
    due_text = due.get("string") or due.get("date") or None

    labels = task.get("labels") or []
    labels_text = ", ".join(labels) if labels else None
    # ai_summary = send_to_groq(f"summarize: {title}")

    # priority = todoist_priority(task.get("priority"))

    if title:
        title = title.replace('[', '').replace(']', '').replace('(', '\n\n').replace(')', '')
    if BATCH > 1:
        msg = f"<b>{index}. {title}</b>\n"
    else:
        msg = f"<b>{title}</b>\n"

    if due_text:
        msg = msg + f"<b>Due</b>: {html.escape(due_text)}\n"
    if labels_text:
        msg = msg + f"<b>Labels</b>: {html.escape(labels_text)}"
    if section:
        msg = msg + f"\n<b>Category/Section</b>: {html.escape(section)}"

    output = msg

    if description:
        output += f"\nNotes: {description}"

    return output


def build_message(tasks: list[dict]) -> str:
    if not tasks:
        return "No active tasks found in this Todoist project."

    selected_tasks = random.sample(tasks, k=min(BATCH, len(tasks)))

    formatted_tasks = [
        format_task(task, index)
        for index, task in enumerate(selected_tasks, start=1)
    ]

    return f"".join(formatted_tasks)


# def build_scheduled_date():
#     # Get the exact current local date and time
#     now = datetime.now()
#
#     # Add 20 seconds using timedelta
#     return int((now + timedelta(seconds=20)).timestamp())


def send_telegram_message(message: str) -> None:
    url = TELEGRAM_SEND_URL.format(token=TELEGRAM_BOT_TOKEN)
    # ts = build_scheduled_date()

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
        # "scheduled_date": ts
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()


def main() -> None:
    tasks = get_todoist_tasks(TODOIST_PROJECT_ID)
    message = build_message(tasks)
    send_telegram_message(message)
    print("Sent random Todoist tasks to Telegram.")


if __name__ == "__main__":
    # get_ollama_response(model="gemma4:latest",
    #                     prompt='What are the key safety considerations when working with industrial robots?')
    main()


#TODO: Add a feature to close the task from telegram
#TODO: Add ollama at the time of cicd pipeline