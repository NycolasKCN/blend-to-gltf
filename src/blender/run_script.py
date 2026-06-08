import os
import asyncio
from pathlib import Path
from logger import logger
from fastapi import HTTPException


BLENDER_BIN = os.environ.get("BLENDER_BIN", "blender")
SCRIPT_PATH = Path(__file__).parent / "extract_animations.py"
JOB_TIMEOUT = int(os.environ.get("JOB_TIMEOUT", "120"))


async def run_blender(job_dir: Path, output:Path, blend_file: Path, armature_name: str = "Armature.001") -> Path:
    """
    Executa o Blender em background e aguarda a conclusão.
    Retorna o Path do .glb gerado ou lança HTTPException em caso de erro.
    """

    cmd = [
        BLENDER_BIN,
        "--background",
        "--python", str(SCRIPT_PATH),
        "--",
        str(blend_file.name),
        "--output", str(output.absolute()),
        "--armature-name", armature_name,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(job_dir),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=JOB_TIMEOUT)
        
        log_out = stdout.decode(errors="replace").strip()
        log_err = stderr.decode(errors="replace").strip()

        if log_out:
            logger.info(f"[BLENDER STDOUT - {blend_file.name}]:\n{log_out}")
        
        if log_err:
            logger.warning(f"[BLENDER STDERR - {blend_file.name}]:\n{log_err}")

    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(
            status_code=504,
            detail=f"Timeout: o Blender demorou mais de {JOB_TIMEOUT}s."
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Blender não encontrado em '{BLENDER_BIN}'. "
                   "Defina a variável de ambiente BLENDER_BIN com o caminho correto."
        )

    if proc.returncode != 0:
        error_log = stderr.decode(errors="replace")[-2000:]  # últimas 2000 chars
        raise HTTPException(
            status_code=500,
            detail=f"Blender retornou erro (código {proc.returncode}):\n{error_log}"
        )

    if not output.exists():
        raise HTTPException(
            status_code=500,
            detail="Blender finalizou sem erros mas o .glb não foi gerado."
        )

    return output
