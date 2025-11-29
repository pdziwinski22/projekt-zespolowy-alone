from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .config import BASE_DIR, UPLOAD_DIR, PROCESSED_DIR
from .services.image_processing import process_image
from .services.logging_service import init_db, log_operation, get_logs
from .services.openai_client import describe_image, generate_image_dalle

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# To wywołanie teraz automatycznie zaktualizuje Twoją bazę o kolumnę 'model'!
init_db()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process(
    request: Request,
    file: UploadFile = File(...),
    effect: str = Form(...),
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    original_path = UPLOAD_DIR / file.filename
    with original_path.open("wb") as f:
        f.write(await file.read())

    result_filename, ai_desc, tokens_in, tokens_out = process_image(
        original_path, PROCESSED_DIR, effect,
    )

    log_operation(
        original_filename=file.filename,
        result_filename=result_filename,
        effect=effect,
        ai_description=ai_desc,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model="gpt-4o"  # <--- Dodajemy model
    )

    return templates.TemplateResponse("index.html", {
        "request": request, "active_tab": "process",
        "original_image": f"/static/uploads/{file.filename}",
        "processed_image": f"/static/processed/{result_filename}",
        "ai_desc": ai_desc, "effect": effect,
    })

@app.post("/analyze-medical", response_class=HTMLResponse)
async def analyze_medical(request: Request, file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original_path = UPLOAD_DIR / file.filename
    with original_path.open("wb") as f:
        f.write(await file.read())

    ai_desc, tokens_in, tokens_out = describe_image(original_path, mode="medical")
    
    log_operation(
        original_filename=file.filename,
        result_filename=file.filename,
        effect="medical_analysis",
        ai_description=ai_desc,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model="gpt-4o" # <--- Dodajemy model
    )

    return templates.TemplateResponse("index.html", {
        "request": request, "active_tab": "medical",
        "medical_image": f"/static/uploads/{file.filename}",
        "medical_desc": ai_desc,
    })

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, prompt: str = Form(...)):
    image_url = generate_image_dalle(prompt)
    
    log_operation(
        original_filename=prompt[:100],
        result_filename="DALL-E Cloud Image",
        effect="dall-e-3",
        ai_description="Wygenerowano obraz z promptu użytkownika.",
        tokens_in=0,
        tokens_out=0,
        model="dall-e-3" # <--- Dodajemy model
    )

    return templates.TemplateResponse("index.html", {
        "request": request, "active_tab": "generate",
        "generated_url": image_url, "prompt": prompt,
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_view(request: Request):
    # Teraz get_logs zwraca dwie rzeczy: listę logów i sumę kosztów
    logs, total_cost = get_logs()
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "logs": logs, "total_cost": total_cost},
    )