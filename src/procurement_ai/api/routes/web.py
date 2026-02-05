"""WebUI Routes
Server-side rendered pages using HTMX + Tailwind
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_

from procurement_ai.api.dependencies import get_db
from procurement_ai.storage.models import Organization, TenderDB, AnalysisResult, TenderStatus
from procurement_ai.storage.repositories import (
    TenderRepository,
    AnalysisRepository,
    BidDocumentRepository,
)
from procurement_ai.orchestration.simple_chain import ProcurementOrchestrator
from procurement_ai.models import Tender as TenderModel
from procurement_ai.config import Config

router = APIRouter(prefix="/web", tags=["web"])

# Templates directory
templates = Jinja2Templates(directory="src/procurement_ai/api/templates")


def _resolve_web_org_id(session) -> int | None:
    """Resolve organization id used by the web UI."""
    org = (
        session.query(Organization)
        .filter(
            Organization.slug == Config.WEB_ORGANIZATION_SLUG,
            Organization.is_deleted == False,
        )
        .first()
    )
    if org:
        return org.id

    fallback = (
        session.query(Organization.id)
        .filter(Organization.is_deleted == False)
        .order_by(Organization.id.asc())
        .first()
    )
    return fallback[0] if fallback else None


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db = Depends(get_db)
):
    """Main dashboard page"""
    with db.get_session() as session:
        org_id = _resolve_web_org_id(session)
        if org_id is None:
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "stats": {"total": 0, "pending": 0, "analyzed": 0, "high_rated": 0},
                    "tenders": [],
                    "error": "No organization found. Run scripts/setup_api_test.sh first.",
                },
            )

        # Get statistics
        stats = {
            "total": session.query(func.count(TenderDB.id)).filter(TenderDB.organization_id == org_id).scalar() or 0,
            "pending": session.query(func.count(TenderDB.id)).filter(
                TenderDB.organization_id == org_id,
                TenderDB.status == TenderStatus.PENDING
            ).scalar() or 0,
            "analyzed": session.query(func.count(TenderDB.id)).filter(
                TenderDB.organization_id == org_id,
                TenderDB.status == TenderStatus.COMPLETE
            ).scalar() or 0,
            "high_rated": session.query(func.count(AnalysisResult.id)).join(TenderDB).filter(
                TenderDB.organization_id == org_id,
                AnalysisResult.overall_score >= 7.0
            ).scalar() or 0,
        }
        
        # Get tenders with latest analysis
        query = session.query(TenderDB).options(
            joinedload(TenderDB.analysis)
        ).filter(
            TenderDB.organization_id == org_id,
            TenderDB.is_deleted == False
        )
        
        # Apply filters
        if status and status.strip():
            try:
                # Handle both lowercase form values and enum values
                status_enum = TenderStatus(status.lower())
                query = query.filter(TenderDB.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    TenderDB.title.ilike(search_term),
                    TenderDB.description.ilike(search_term),
                    TenderDB.organization_name.ilike(search_term)
                )
            )
        
        tenders = query.order_by(TenderDB.created_at.desc()).limit(50).all()
        
        # Add latest_analysis to each tender
        for tender in tenders:
            tender.latest_analysis = tender.analysis
        
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "tenders": tenders
    })


@router.get("/tenders", response_class=HTMLResponse)
async def get_tenders(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db = Depends(get_db)
):
    """Get tender list (for HTMX updates)"""
    with db.get_session() as session:
        org_id = _resolve_web_org_id(session)
        if org_id is None:
            return templates.TemplateResponse("tender_list.html", {"request": request, "tenders": []})

        query = session.query(TenderDB).options(
            joinedload(TenderDB.analysis)
        ).filter(
            TenderDB.organization_id == org_id,
            TenderDB.is_deleted == False
        )
        
        if status and status.strip():
            try:
                status_enum = TenderStatus(status.lower())
                query = query.filter(TenderDB.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    TenderDB.title.ilike(search_term),
                    TenderDB.description.ilike(search_term),
                    TenderDB.organization_name.ilike(search_term)
                )
            )
        
        tenders = query.order_by(TenderDB.created_at.desc()).limit(50).all()
        
        for tender in tenders:
            tender.latest_analysis = tender.analysis
    
    return templates.TemplateResponse("tender_list.html", {
        "request": request,
        "tenders": tenders
    })


@router.get("/tender/{tender_id}", response_class=HTMLResponse)
async def tender_detail(
    request: Request,
    tender_id: int,
    db = Depends(get_db)
):
    """Tender detail modal"""
    with db.get_session() as session:
        org_id = _resolve_web_org_id(session)
        if org_id is None:
            tender = None
            return templates.TemplateResponse("tender_detail.html", {"request": request, "tender": tender})

        tender = session.query(TenderDB).options(
            joinedload(TenderDB.analysis)
        ).filter(
            TenderDB.id == tender_id,
            TenderDB.organization_id == org_id
        ).first()
        
        if tender:
            tender.latest_analysis = tender.analysis
    
    return templates.TemplateResponse("tender_detail.html", {
        "request": request,
        "tender": tender
    })


@router.post("/analyze/{tender_id}", response_class=HTMLResponse)
async def analyze_tender(
    request: Request,
    tender_id: int,
    db = Depends(get_db)
):
    """Analyze tender with AI pipeline"""
    with db.get_session() as session:
        org_id = _resolve_web_org_id(session)
        if org_id is None:
            return HTMLResponse("<div class='text-red-600'>No organization found</div>", status_code=500)

        tender_repo = TenderRepository(session)
        analysis_repo = AnalysisRepository(session)
        doc_repo = BidDocumentRepository(session)
        
        tender_db = tender_repo.get_by_id(tender_id, org_id=org_id)
        if not tender_db:
            return HTMLResponse("<div class='text-red-600'>Tender not found</div>", status_code=404)
        
        # Update status to processing
        tender_db.status = TenderStatus.PROCESSING
        session.commit()
        
        # Convert to domain model
        tender = TenderModel(
            id=tender_db.external_id,
            title=tender_db.title,
            description=tender_db.description,
            organization=tender_db.organization_name,
            deadline=tender_db.deadline or "",
            estimated_value=tender_db.estimated_value
        )
        
        # Run analysis
        try:
            config = Config()
            orchestrator = ProcurementOrchestrator(config)
            result = await orchestrator.process_tender(tender)
            
            # Extract filter result fields
            is_relevant = result.filter_result.is_relevant if result.filter_result else False
            confidence = result.filter_result.confidence if result.filter_result else 0.0
            filter_categories = [c.value for c in result.filter_result.categories] if result.filter_result else []
            filter_reasoning = result.filter_result.reasoning if result.filter_result else None
            
            # Extract rating result fields
            overall_score = result.rating_result.overall_score if result.rating_result else None
            strategic_fit = result.rating_result.strategic_fit if result.rating_result else None
            win_probability = result.rating_result.win_probability if result.rating_result else None
            resource_requirements = result.rating_result.effort_required if result.rating_result else None
            strengths = result.rating_result.strengths if result.rating_result else []
            risks = result.rating_result.risks if result.rating_result else []
            recommendation = result.rating_result.recommendation if result.rating_result else None
            
            # Save analysis with individual fields
            analysis = analysis_repo.upsert(
                tender_id=tender_id,
                is_relevant=is_relevant,
                confidence=confidence,
                filter_categories=filter_categories,
                filter_reasoning=filter_reasoning,
                overall_score=overall_score,
                strategic_fit=strategic_fit,
                win_probability=win_probability,
                resource_requirements=resource_requirements,
                strengths=strengths,
                risks=risks,
                recommendation=recommendation
            )

            if result.bid_document:
                doc_repo.upsert(
                    tender_id=tender_id,
                    executive_summary=result.bid_document.executive_summary,
                    capabilities=result.bid_document.technical_approach,
                    approach=result.bid_document.timeline_estimate,
                    value_proposition=result.bid_document.value_proposition,
                )
            
            # Update tender status
            if result.status == "complete":
                tender_db.status = TenderStatus.COMPLETE
            elif result.status == "filtered_out":
                tender_db.status = TenderStatus.FILTERED_OUT
            elif result.status == "rated_low":
                tender_db.status = TenderStatus.RATED_LOW
            else:
                tender_db.status = TenderStatus.ERROR
            tender_db.processing_time = result.processing_time
            tender_db.error_message = result.error
            session.commit()
            
            # Prepare analysis for template
            tender_db.latest_analysis = analysis
            
            return templates.TemplateResponse("analysis_result.html", {
                "request": request,
                "tender": tender_db,
                "analysis": analysis
            })
            
        except Exception as e:
            tender_db.status = TenderStatus.ERROR
            session.commit()
            return HTMLResponse(f"<div class='text-red-600 p-4'>Error analyzing tender: {str(e)}</div>", status_code=500)


@router.get("/scrape-modal", response_class=HTMLResponse)
async def scrape_modal(request: Request):
    """Modal for scraping new tenders"""
    return HTMLResponse("""
    <!-- Modal Overlay -->
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40" 
         onclick="document.getElementById('modal-container').innerHTML = ''"></div>

    <!-- Modal Panel -->
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <div class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                            <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                        </div>
                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                            <h3 class="text-lg font-medium leading-6 text-gray-900">
                                Fetch New Tenders
                            </h3>
                            <div class="mt-2">
                                <p class="text-sm text-gray-500">
                                    This will fetch the latest tenders from TED Europa and add them to your database.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                    <button 
                        onclick="alert('Scraping feature coming soon! For now, run: python scripts/fetch_and_store.py'); document.getElementById('modal-container').innerHTML = ''"
                        type="button" 
                        class="inline-flex w-full justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm">
                        Fetch Tenders
                    </button>
                    <button 
                        onclick="document.getElementById('modal-container').innerHTML = ''" 
                        type="button" 
                        class="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:mt-0 sm:w-auto sm:text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>
    """)
