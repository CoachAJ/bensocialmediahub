import os
import json

def render_skool_quiz_embed(
    question: str,
    options: list[str],
    correct_idx: int,
    explanation: str,
    output_path: str
):
    """
    Renders an interactive, standalone HTML quiz card embed for Skool community posts.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "quiz_template.html")
    
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        # Fallback inline template
        template = """<!DOCTYPE html>
<html><body><h3>{{QUESTION}}</h3><div id="opts"></div><p id="exp">{{EXPLANATION}}</p>
<script>
const options = {{OPTIONS_JSON}};
const correctIdx = {{CORRECT_IDX}};
</script></body></html>"""

    rendered = (
        template
        .replace("{{QUESTION}}", question)
        .replace("{{OPTIONS_JSON}}", json.dumps(options))
        .replace("{{CORRECT_IDX}}", str(correct_idx))
        .replace("{{EXPLANATION}}", explanation)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    # Mirror to dashboard/quizzes for direct serving via Netlify and Master Hub
    dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard", "quizzes")
    os.makedirs(dashboard_dir, exist_ok=True)
    filename = os.path.basename(output_path)
    dashboard_quiz_path = os.path.join(dashboard_dir, filename)
    try:
        with open(dashboard_quiz_path, "w", encoding="utf-8") as f:
            f.write(rendered)
    except Exception:
        pass
