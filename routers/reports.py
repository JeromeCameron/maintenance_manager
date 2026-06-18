import io

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlmodel import Session

from auth.dependencies import get_current_user
from schema.database import get_session
from utils.weekly_report import generate_weekly_report
from utils.weekly_report_html import generate_weekly_report_html

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/weekly", status_code=status.HTTP_200_OK)
def download_weekly_report(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    pdf_bytes = generate_weekly_report(session)
    filename = f"weekly_maintenance_report.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/weekly-html", response_class=HTMLResponse)
def view_weekly_report(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    html = generate_weekly_report_html(session)
    return HTMLResponse(content=html)
