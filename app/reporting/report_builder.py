from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from ..models import ResumeParsed, MatchResult, InterviewOutcome

def render_report(out_dir: str, resume: ResumeParsed, match: MatchResult, outcome: InterviewOutcome) -> str:
    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent.parent.parent / "templates")),
        autoescape=select_autoescape(["html","xml"])
    )
    tpl = env.get_template("report.html.j2")
    html = tpl.render(resume=resume, match=match, outcome=outcome)
    out_path = Path(out_dir) / f"{resume.candidate_id}.html"
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
