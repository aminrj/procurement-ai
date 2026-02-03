"""
Tender Analysis Routes
Core endpoints for submitting and retrieving tender analyses
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from procurement_ai.api.schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    TenderListResponse,
    TenderResponse,
    FilterResultResponse,
    RatingResultResponse,
    BidDocumentResponse,
)
from procurement_ai.api.dependencies import (
    get_current_organization,
    get_db_session,
    get_config,
    get_llm_service,
    get_db,
)
from procurement_ai.storage.models import Organization, TenderStatus
from procurement_ai.storage.repositories import (
    TenderRepository,
    AnalysisRepository,
    BidDocumentRepository,
    OrganizationRepository,
)
from procurement_ai.storage import DatabaseManager
from procurement_ai.models import Tender
from procurement_ai.orchestration.simple_chain import ProcurementOrchestrator
from procurement_ai.config import Config
from procurement_ai.services.llm import LLMService

router = APIRouter(prefix="/api/v1", tags=["tenders"])


async def process_tender_background(
    tender_id: int,
    tender_data: Tender,
    organization_id: int,
    db: DatabaseManager,
    config: Config,
    llm_service: LLMService,
):
    """Background task to process tender with AI"""
    try:
        # Run orchestrator
        orchestrator = ProcurementOrchestrator(config=config, llm_service=llm_service)
        result = await orchestrator.process_tender(tender_data)

        # Store results in database
        with db.get_session() as session:
            tender_repo = TenderRepository(session)
            analysis_repo = AnalysisRepository(session)
            doc_repo = BidDocumentRepository(session)

            # Update tender status
            if result.status == "complete":
                tender_repo.update_status(tender_id, TenderStatus.ANALYZED)
            elif result.status.startswith("error"):
                tender_repo.update_status(tender_id, TenderStatus.ERROR)  # Use ERROR instead of FAILED
            elif result.status == "filtered_out":
                tender_repo.update_status(tender_id, TenderStatus.REJECTED)
            elif result.status == "rated_low":
                tender_repo.update_status(tender_id, TenderStatus.ANALYZED)

            # Store analysis
            if result.filter_result and result.rating_result:
                analysis_repo.create(
                    tender_id=tender_id,
                    is_relevant=result.filter_result.is_relevant,
                    confidence=result.filter_result.confidence,
                    filter_categories=[c.value for c in result.filter_result.categories],
                    filter_reasoning=result.filter_result.reasoning,
                    overall_score=result.rating_result.overall_score,
                    strategic_fit=result.rating_result.strategic_fit,
                    win_probability=result.rating_result.win_probability,
                    strengths=result.rating_result.strengths,
                    risks=result.rating_result.risks,
                    recommendation=result.rating_result.recommendation,
                )

            # Store bid document
            if result.bid_document:
                doc_repo.create(
                    tender_id=tender_id,
                    executive_summary=result.bid_document.executive_summary,
                    capabilities=result.bid_document.technical_approach,  # Map field
                    approach=result.bid_document.timeline_estimate,  # Map field
                    value_proposition=result.bid_document.value_proposition,
                )

    except Exception as e:
        # Log error and update status
        error_msg = str(e)[:500]  # Limit error message length
        with db.get_session() as session:
            tender_repo = TenderRepository(session)
            tender_repo.update_status(tender_id, TenderStatus.ERROR)
            # Store error for debugging (if update method supports it)
            # tender_repo.update(tender_id, error_message=error_msg)


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_tender(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    organization: Organization = Depends(get_current_organization),
    session: Session = Depends(get_db_session),
    config: Config = Depends(get_config),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Submit a tender for AI analysis
    
    This endpoint accepts a tender and starts background processing.
    Returns immediately with status "processing".
    Use GET /tenders/{id} to check results.
    """
    # Check if organization can analyze more tenders
    if not organization.can_analyze():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly analysis limit reached ({organization.analyses_this_month}/{organization.monthly_analysis_limit})",
        )

    tender_repo = TenderRepository(session)
    org_repo = OrganizationRepository(session)

    # Create tender in database
    tender_db = tender_repo.create(
        organization_id=organization.id,
        title=request.title,
        description=request.description,
        organization_name=request.organization_name,
        deadline=request.deadline,
        estimated_value=request.estimated_value,
        external_id=request.external_id,
        source=request.source,
    )

    # Update usage count and mark as processing
    org_repo.update_usage(organization.id)
    tender_repo.update_status(tender_db.id, TenderStatus.PROCESSING)

    # Convert to Tender model for orchestrator
    tender_data = Tender(
        id=str(tender_db.external_id or tender_db.id),  # Convert int to string
        title=tender_db.title,
        description=tender_db.description,
        organization=tender_db.organization_name,
        deadline=tender_db.deadline or "",
        estimated_value=tender_db.estimated_value or "",
    )

    # Start background processing
    db = Depends(get_db)
    background_tasks.add_task(
        process_tender_background,
        tender_db.id,
        tender_data,
        organization.id,
        get_db(),  # Pass database instance
        config,
        llm_service,
    )

    # Return tender with processing status
    return AnalysisResponse(
        tender=TenderResponse.model_validate(tender_db),
        status="processing",
        processing_time=None,
        filter_result=None,
        rating_result=None,
        bid_document=None,
    )


@router.get("/tenders", response_model=TenderListResponse)
def list_tenders(
    page: int = 1,
    page_size: int = 20,
    organization: Organization = Depends(get_current_organization),
    session: Session = Depends(get_db_session),
):
    """
    List all tenders for the authenticated organization
    
    Supports pagination via page and page_size query parameters.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

    tender_repo = TenderRepository(session)

    # Calculate offset from page
    offset = (page - 1) * page_size

    # Get paginated tenders
    tenders = tender_repo.list_by_organization(
        organization.id, limit=page_size, offset=offset
    )
    
    # Get total count
    total = tender_repo.count_by_organization(organization.id)

    total_pages = (total + page_size - 1) // page_size

    return TenderListResponse(
        tenders=[TenderResponse.model_validate(t) for t in tenders],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/tenders/{tender_id}", response_model=AnalysisResponse)
def get_tender_analysis(
    tender_id: int,  # Database uses integer IDs
    organization: Organization = Depends(get_current_organization),
    session: Session = Depends(get_db_session),
):
    """
    Get tender and its analysis results
    
    Returns tender info, analysis, and generated bid document if available.
    """
    tender_repo = TenderRepository(session)
    analysis_repo = AnalysisRepository(session)
    doc_repo = BidDocumentRepository(session)

    # Get tender
    tender = tender_repo.get_by_id(tender_id, organization.id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    # Get analysis
    analysis = analysis_repo.get_latest_by_tender(tender_id)

    # Get bid document
    bid_doc = doc_repo.get_latest_by_tender(tender_id)

    # Build response
    response = AnalysisResponse(
        tender=TenderResponse.model_validate(tender),
        status=tender.status.value,
        processing_time=tender.processing_time,  # Use tender's processing_time, not analysis
    )

    # Add analysis results if available
    if analysis:
        response.filter_result = FilterResultResponse(
            is_relevant=analysis.is_relevant,
            confidence=analysis.confidence,
            categories=[c for c in (analysis.filter_categories or [])],
            reasoning=analysis.filter_reasoning or "",
        )

        if analysis.overall_score is not None:
            response.rating_result = RatingResultResponse(
                overall_score=analysis.overall_score,
                strategic_fit=analysis.strategic_fit or 0.0,
                win_probability=analysis.win_probability or 0.0,
                effort_required=0.0,  # MVP: Hardcoded, can be calculated later
                strengths=analysis.strengths or [],
                risks=analysis.risks or [],
                recommendation=analysis.recommendation or "",
            )

    # Add bid document if available
    if bid_doc:
        # Note: Field mapping due to schema evolution
        # Old DB: capabilities, approach → API: technical_approach, timeline_estimate
        response.bid_document = BidDocumentResponse(
            executive_summary=bid_doc.executive_summary,
            technical_approach=bid_doc.capabilities,
            value_proposition=bid_doc.value_proposition,
            timeline_estimate=bid_doc.approach,
        )

    return response
