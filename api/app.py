"""FastAPI 服务 — word2md REST API，可被 Dify 等第三方调用。"""

import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from engine import convert

app = FastAPI(
    title="word2md",
    description="Word (.docx) 报告高保真转换服务 — HTML/Markdown/JSON",
    version="0.1.0",
)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/v1/convert")
async def convert_endpoint(
    file: UploadFile = File(...),
    output: str = Form("html"),
    extract_images: bool = Form(True),
):
    """上传 .docx 文件，返回转换结果 JSON。"""
    if output not in ("html", "markdown", "json"):
        raise HTTPException(status_code=400, detail=f"Invalid output mode: {output}")

    tmp_dir = tempfile.mkdtemp()
    try:
        file_path = Path(tmp_dir) / file.filename
        content = await file.read()
        file_path.write_bytes(content)

        images_dir = Path(tmp_dir) / "images"
        result = convert(
            str(file_path),
            output_mode=output,
            extract_images=extract_images,
            images_dir=images_dir,
        )

        return {
            "success": True,
            "data": {
                "content": result["content"],
                "metadata": {**result["metadata"], "filename": file.filename},
                "stats": result["stats"],
                "images": result["images"],
            },
            "error": None,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": str(e)},
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
