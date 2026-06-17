from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4 as uuid
import shutil

from logger import logger
from src.blender.cache import check_cache, init_db, register_cache
from src.blender.run_script import run_blender
from src.vlibras.vlibras_api import GlosaDictionary, Tasks, DownloadBlend

load_dotenv()

OUT_DIR = Path("./glb")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR = Path("./tmp/blender-api")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

dictionary: GlosaDictionary = GlosaDictionary("https://wikiback.vlibras.gov.br/dictionary-published/1")
tasks: Tasks = Tasks("https://wikiback.vlibras.gov.br/object-task")
download: DownloadBlend = DownloadBlend("https://wikiback.vlibras.gov.br/download")

init_db()
app: FastAPI = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/static/glb/glosa/{glosa}", response_class=FileResponse)
async def get_glb_file(glosa: str):
    cached_path = check_cache(glosa)
    if cached_path:
        logger.info(f"Cache para '{glosa}' encontrado, retornando imediatamente.")
        return FileResponse(
            path=str(cached_path),
            filename=f"{glosa}.glb",
            media_type="model/gltf-binary"
        )

    logger.info(f"Cache MISS para '{glosa}'. Iniciando processo de geração.")
    
    try:
        task_id: int = dictionary.search_glosa_task_id(glosa)
        blend_path: str = tasks.get_blend_path(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    job_id = uuid().hex
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    glb_file:Path|None = None

    try:
        blend_file = job_dir / f"{glosa}.blend" 
        out = OUT_DIR / f"{glosa}.glb" 

        download.download(blend_path, blend_file)
        glb_file = await run_blender(job_dir, out, blend_file)
        
    except Exception as e:
        logger.error(e)
        shutil.rmtree(job_dir, ignore_errors=True)
        raise e
    finally:
        logger.info("Cleaning job directory")
        shutil.rmtree(job_dir, ignore_errors=True)

    register_cache(glosa, glb_file)

    return FileResponse(
        path=str(glb_file),
        filename=f"{glosa}.glb",
        media_type="model/gltf-binary"
    )

@app.get("/static/glb/model/{name}", response_class=FileResponse)
def get_model(name: str) -> FileResponse:
    moldel_path: Path = Path("./glb/models/icaro.glb")
    return FileResponse(
        path=str(moldel_path),
        filename="icaro.glb",
        media_type="model/gltf-binary"
    )

@app.get("/blend/{glosa}", response_class=FileResponse)
def get_blend(glosa: str) -> FileResponse:
    try:
        task_id: int = dictionary.search_glosa_task_id(glosa)
        blend_path: str = tasks.get_blend_path(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    job_id = uuid().hex
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        blend_file = job_dir / f"{glosa}.blend" 

        download.download(blend_path, blend_file)
    except Exception as e:
        logger.error(e)
        shutil.rmtree(job_dir, ignore_errors=True)
        raise e

    return FileResponse(
        path=str(blend_file),
        filename=f"{glosa}.blend",
    )

@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
