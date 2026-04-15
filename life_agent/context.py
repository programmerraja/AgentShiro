import os
import json
import datetime
from life_agent.storage import read_daily
from life_agent.gamification import load_score

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "life-system")
)


def _read_file_safe(rel_path: str) -> str:
    path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def generate_last_7_days_summary(
    model_name: str,
) -> str:
    from agentshiro.llm import completion

    today = datetime.datetime.now()
    summary_text = ""
    for i in range(7):
        d = today - datetime.timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        content = read_daily(date_str)
        if content:
            summary_text += f"\n--- {date_str} ---\n{content}\n"

    if not summary_text.strip():
        return "No activity recorded in the last 7 days."

    prompt = (
        "Summarize the following daily logs identifying key tasks done, alignment with goals, and patterns over the last 7 days (Keep it concise):\n"
        + summary_text
    )

    print(
        "\n[System] Generating 7-day summary using mini-agent (this might take a few seconds)..."
    )
    try:
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to generate summary: {str(e)}"


def build_context_snapshot():
    now = datetime.datetime.now()
    today_date = now.strftime("%Y-%m-%d")

    # Load state
    score_data = load_score()
    today_task_list = read_daily(today_date)

    # Compute basic variables
    week_start = now - datetime.timedelta(days=now.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    context = {
        "{{TODAY_DATE}}": today_date,
        "{{currentTime}}": now.strftime("%H:%M:%S"),
        "{{dayOfWeek}}": now.strftime("%A"),
        "{{weekNumber}}": str(now.isocalendar()[1]),
        "{{weekStartDate}}": week_start.strftime("%Y-%m-%d"),
        "{{weekEndDate}}": week_end.strftime("%Y-%m-%d"),
        "{{TIME_OF_DAY}}": (
            "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening"
        ),
        "{{TODAY_TASK_LIST}}": (
            today_task_list if today_task_list else "No tasks logged today."
        ),
        "{{CURRENT_STREAK}}": str(score_data.get("streak", 0)),
        "{{CURRENT_POINTS}}": str(score_data.get("points", 0)),
        "{{currentLevel}}": str(score_data.get("level", 1)),
        "{{currentStatus}}": score_data.get("status", "IN GAME"),
    }

    # Generate the 7 days summary dynamically using the mini-agent
    # context["{{last7DaysSummary}}"] = generate_last_7_days_summary(model_name)

    # snapshot_path = os.path.join(BASE_DIR, "system", "context-snapshot.json")
    # os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    # with open(snapshot_path, "w", encoding="utf-8") as f:
    #     json.dump(context, f, indent=4)

    return context
