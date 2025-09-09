import os, io, json, time, tempfile, subprocess
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from gtts import gTTS

from ..interview.ai_interviewer import AIInterviewer
from ..ingestion.parser import parse_resume
from ..screening.matcher import compute_match
from ..reporting.report_builder import render_report
from ..main import load_requirements

STATE_PATH = Path("data/realtime_state.json")
RESUMES_DIR = Path("input/resumes")

app = FastAPI(title="AI-HR Realtime API")

def load_state() -> Dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_state(state: Dict[str, Any]):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def ffmpeg_resample_to_wav16k_mono(in_bytes: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as f_in:
        f_in.write(in_bytes)
        in_path = f_in.name
    out_path = in_path + ".wav"
    try:
        cmd = ["ffmpeg", "-y", "-i", in_path, "-ac", "1", "-ar", "16000", out_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        data = Path(out_path).read_bytes()
        return data
    finally:
        for p in (in_path, out_path):
            try: os.remove(p)
            except: pass

def openai_transcribe(wav_bytes: bytes) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            wav_path = f.name
        try:
            with open(wav_path, "rb") as audio:
                try:
                    resp = client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=audio)
                except Exception:
                    resp = client.audio.transcriptions.create(model="whisper-1", file=audio)
            text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else None)
            return text or ""
        finally:
            try: os.remove(wav_path)
            except: pass
    except Exception:
        return ""

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/stt")
async def stt(channel_id: str = Form(...), user_id: str = Form(...), audio: UploadFile = File(...)):
    raw = await audio.read()
    wav = ffmpeg_resample_to_wav16k_mono(raw)
    text = openai_transcribe(wav) or ""
    state = load_state()
    ch = state.setdefault(channel_id, {"transcript": [], "qa_idx": 0, "questions": [], "candidate_id": None, "started": False})
    ch["transcript"].append({"role": "candidate", "user_id": user_id, "text": text, "ts": time.time()})
    if not ch["started"]:
        ch["started"] = True
        ai = AIInterviewer()
        resume_text = ""
        ch["questions"] = ai.ask_questions(resume_text)
        ch["qa_idx"] = 0
    next_q = None
    if ch["questions"]:
        idx = ch["qa_idx"]
        if len([t for t in ch["transcript"] if t["role"] == "ai"]) == 0:
            next_q = ch["questions"][0]
            ch["transcript"].append({"role": "ai", "text": next_q, "ts": time.time()})
        else:
            if text and len(text.split()) >= 8 and idx+1 < len(ch["questions"]):
                ch["qa_idx"] = idx + 1
                next_q = ch["questions"][ch["qa_idx"]]
                ch["transcript"].append({"role": "ai", "text": next_q, "ts": time.time()})
    save_state(state)
    return {"text": text, "next_question": next_q}

@app.get("/tts")
def tts(text: str):
    tts = gTTS(text=text, lang="ru")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    tts.save(tmp)
    def iterfile():
        with open(tmp, "rb") as fbin:
            while True:
                chunk = fbin.read(8192)
                if not chunk: break
                yield chunk
        try: os.remove(tmp)
        except: pass
    return StreamingResponse(iterfile(), media_type="audio/mpeg")

@app.post("/finish")
def finish(channel_id: str = Form(...), candidate_id: str = Form(None)):
    state = load_state()
    ch = state.get(channel_id)
    if not ch:
        return JSONResponse({"error": "no_state"}, status_code=404)
    ai = AIInterviewer()
    answers = [t["text"] for t in ch["transcript"] if t["role"] == "candidate"]
    cand_id = candidate_id or ch.get("candidate_id") or "unknown"
    resume = None
    if (RESUMES_DIR / cand_id).exists():
        try:
            resume = parse_resume(str(RESUMES_DIR / cand_id))
        except Exception:
            resume = None
    outcome = ai.run(cand_id, resume.raw_text if resume else "", answers)
    report_path = None
    if resume:
        try:
            req = load_requirements("input/requirements")
            match = compute_match(resume, req)
            report_path = render_report("reports", resume, match, outcome)
        except Exception:
            report_path = None
    return {"decision": outcome.decision, "rationale": outcome.rationale, "report": report_path}
