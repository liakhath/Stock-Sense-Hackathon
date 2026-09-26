from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import CurrentUser, Engine
from app.schemas.reports import ImportReport
from app.services.importer import import_products, template_csv

router = APIRouter(prefix="/import", tags=["Import"])
MAX_BYTES = 5 * 1024 * 1024


@router.get("/products/template")
def download_template():
    """CSV template with the expected columns and 2 example rows."""
    return Response(template_csv(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="stocksense_products_template.csv"'})


@router.post("/products", response_model=ImportReport)
async def import_products_file(eng: Engine, user: CurrentUser, file: UploadFile = File(...),
                               dry_run: bool = True, create_locations: bool = True):
    """Upload .csv or .xlsx. Default is a dry run (preview only).
    Call again with ?dry_run=false to actually save."""
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 5 MB)")
    try:
        return import_products(eng, file.filename or "", content, user=user,
                               dry_run=dry_run, create_locations=create_locations)
    except ValueError as e:
        raise HTTPException(400, str(e))