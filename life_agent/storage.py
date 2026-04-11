import os
import re
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "life-system"))

def get_daily_path(date_str: str) -> str:
    # date_str like 2026-04-10
    year, month, day = date_str.split("-")
    dir_path = os.path.join(BASE_DIR, "daily", year, month)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{date_str}.md")

def generate_daily_template(date_str: str, current_score_data: dict) -> str:
    path = get_daily_path(date_str)
    if os.path.exists(path):
        return path
    
    template = f"""# Date: {date_str}

## Plan (Morning)

### Family
- [ ] 

### Career
- [ ] 

### Money
- [ ] 

### Health
- [ ] 

### Happiness
- [ ] 

### Self
- [ ] 

---

## Execution (What actually happened)

### Done

### Missed

---

## Alignment Check (Agent will fill)

Aligned Tasks: 0  
Misaligned Tasks: 0  

Reason:
- 

---

## Reflection (Night)

- What went well:
- What went wrong:
- Why:
- What to improve tomorrow:

---

## Score

Points: {current_score_data.get('points', 0)}  
Streak: {current_score_data.get('streak', 0)} days  
Status: {current_score_data.get('status', 'IN GAME')}
"""
    with open(path, "w") as f:
        f.write(template)
    return path

def read_daily(date_str: str) -> str:
    path = get_daily_path(date_str)
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        return f.read()

def write_section(date_str: str, section_header: str, new_content: str) -> bool:
    path = get_daily_path(date_str)
    if not os.path.exists(path):
        return False
    
    with open(path, "r") as f:
        content = f.read()
    
    escaped_header = re.escape(section_header)
    pattern = re.compile(f"({escaped_header}.*?)(?=\\n---|\\n## |\\Z)", re.DOTALL)
    
    if pattern.search(content):
        # We replace the whole matched section with new_content. 
        new_text = pattern.sub(new_content.strip(), content, count=1)
        with open(path, "w") as f:
            f.write(new_text)
        return True
    return False

def append_mistake(date_str: str, content: str):
    dir_path = os.path.join(BASE_DIR, "mistakes")
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, f"{date_str}.md")
    
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode) as f:
        f.write(f"\n- {content}")
