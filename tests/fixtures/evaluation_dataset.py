"""
High-quality evaluation dataset for AI agent testing

This dataset contains carefully curated test cases covering:
- Clear positive cases (relevant, high-quality tenders)
- Clear negative cases (irrelevant tenders)
- Edge cases (ambiguous, borderline cases)
- Category-specific challenges
- Rating validation cases

Each test case includes expected outcomes for validation.
"""

from typing import List, Dict, Optional
from enum import Enum


class TestCaseCategory(str, Enum):
    """Category of test case for organizing evaluations"""
    CLEAR_RELEVANT = "clear_relevant"
    CLEAR_IRRELEVANT = "clear_irrelevant"
    EDGE_CASE = "edge_case"
    CATEGORY_TEST = "category_test"
    RATING_VALIDATION = "rating_validation"


class EvaluationTestCase:
    """Single evaluation test case with expected outcomes"""
    
    def __init__(
        self,
        tender_id: str,
        category: TestCaseCategory,
        title: str,
        description: str,
        organization: str,
        estimated_value: Optional[str] = None,
        expected_relevance: bool = True,
        expected_confidence_min: float = 0.7,
        expected_categories: Optional[List[str]] = None,
        expected_score_range: Optional[tuple] = None,
        expected_recommendation: Optional[str] = None,
        notes: str = "",
        edge_case_reasoning: str = ""
    ):
        self.tender_id = tender_id
        self.category = category
        self.title = title
        self.description = description
        self.organization = organization
        self.estimated_value = estimated_value
        self.expected_relevance = expected_relevance
        self.expected_confidence_min = expected_confidence_min
        self.expected_categories = expected_categories or []
        self.expected_score_range = expected_score_range
        self.expected_recommendation = expected_recommendation
        self.notes = notes
        self.edge_case_reasoning = edge_case_reasoning
    
    def to_tender_dict(self) -> Dict:
        """Convert to tender dictionary for processing"""
        return {
            "id": self.tender_id,
            "title": self.title,
            "description": self.description,
            "organization": self.organization,
            "estimated_value": self.estimated_value,
            "deadline": "2026-06-30",  # Default deadline
        }


# =============================================================================
# CLEAR RELEVANT CASES - High confidence, obvious matches
# =============================================================================

EVAL_001_AI_CYBERSECURITY = EvaluationTestCase(
    tender_id="EVAL-001",
    category=TestCaseCategory.CLEAR_RELEVANT,
    title="AI-Powered Threat Detection and Response System",
    description="""
    National Defense Agency requires an advanced artificial intelligence system
    for cybersecurity threat detection and automated response. The solution must:
    
    - Deploy machine learning models for real-time threat pattern recognition
    - Integrate with existing SIEM and SOC infrastructure
    - Provide automated incident response with human oversight
    - Include threat intelligence correlation and analysis
    - Support behavioral analytics and anomaly detection
    - Ensure compliance with defense-grade security standards
    
    Technical stack should include modern ML frameworks, microservices architecture,
    and cloud-native deployment capabilities. Experience with government security
    clearance required.
    """,
    organization="National Defense Cyber Command",
    estimated_value="€2,500,000",
    expected_relevance=True,
    expected_confidence_min=0.9,
    expected_categories=["cybersecurity", "ai"],
    expected_score_range=(8.0, 10.0),
    expected_recommendation="go",
    notes="Perfect match: combines AI, cybersecurity, and software development"
)

EVAL_002_CUSTOM_SOFTWARE = EvaluationTestCase(
    tender_id="EVAL-002",
    category=TestCaseCategory.CLEAR_RELEVANT,
    title="Enterprise Resource Planning System Development",
    description="""
    Large manufacturing company seeks custom ERP software development to replace
    legacy systems. Requirements include:
    
    - Custom web-based application with modern UI/UX
    - Integration with existing SAP and Oracle databases
    - Real-time inventory and supply chain management
    - Advanced reporting and analytics dashboard
    - Mobile application for field workers
    - RESTful API for third-party integrations
    
    Technology preferences: React/Angular frontend, Python/Java backend,
    PostgreSQL database. Agile development methodology required with
    bi-weekly sprints and continuous deployment.
    """,
    organization="EuroManufacturing GmbH",
    estimated_value="€1,800,000",
    expected_relevance=True,
    expected_confidence_min=0.85,
    expected_categories=["software"],
    expected_score_range=(7.0, 9.0),
    expected_recommendation="go",
    notes="Clear software development project with modern tech stack"
)

EVAL_003_ML_PLATFORM = EvaluationTestCase(
    tender_id="EVAL-003",
    category=TestCaseCategory.CLEAR_RELEVANT,
    title="Machine Learning Platform for Healthcare Diagnostics",
    description="""
    Healthcare consortium requires ML platform for medical imaging analysis.
    The system will support radiologists in detecting abnormalities in X-rays,
    CT scans, and MRI images.
    
    Core requirements:
    - Deep learning models for image classification and segmentation
    - DICOM integration and medical imaging standards compliance
    - Explainable AI for clinical decision support
    - GDPR and HIPAA compliance
    - High availability (99.9% uptime)
    - FDA/CE marking certification support
    
    Must demonstrate prior healthcare AI experience and understanding of
    clinical validation processes.
    """,
    organization="European Healthcare Innovation Network",
    estimated_value="€3,200,000",
    expected_relevance=True,
    expected_confidence_min=0.88,
    expected_categories=["ai", "software"],
    expected_score_range=(7.5, 9.5),
    expected_recommendation="go",
    notes="High-value AI project in specialized domain"
)

EVAL_004_SECURITY_AUDIT = EvaluationTestCase(
    tender_id="EVAL-004",
    category=TestCaseCategory.CLEAR_RELEVANT,
    title="Penetration Testing and Security Audit Services",
    description="""
    Financial institution requires comprehensive cybersecurity assessment including:
    
    - Full penetration testing of web applications and APIs
    - Network infrastructure security audit
    - Social engineering and phishing simulation
    - Code review and vulnerability assessment
    - Compliance audit (PCI-DSS, ISO 27001)
    - Security training for development teams
    
    Deliverables: detailed vulnerability reports, remediation roadmap,
    executive summary, and quarterly re-testing.
    """,
    organization="National Banking Authority",
    estimated_value="€450,000",
    expected_relevance=True,
    expected_confidence_min=0.90,
    expected_categories=["cybersecurity"],
    expected_score_range=(7.0, 9.0),
    expected_recommendation="go",
    notes="Pure cybersecurity services, well within expertise area"
)


# =============================================================================
# CLEAR IRRELEVANT CASES - High confidence rejections
# =============================================================================

EVAL_005_OFFICE_FURNITURE = EvaluationTestCase(
    tender_id="EVAL-005",
    category=TestCaseCategory.CLEAR_IRRELEVANT,
    title="Office Furniture and Equipment Supply",
    description="""
    Government office building renovation requires:
    - 200 ergonomic office chairs
    - 150 height-adjustable desks
    - 50 conference room tables
    - Filing cabinets and storage solutions
    - Delivery and installation services
    
    All furniture must meet EU sustainability standards and be delivered
    within 8 weeks.
    """,
    organization="Ministry of Administrative Affairs",
    estimated_value="€180,000",
    expected_relevance=False,
    expected_confidence_min=0.95,
    expected_categories=[],
    notes="Physical goods procurement, no technology component"
)

EVAL_006_CONSTRUCTION = EvaluationTestCase(
    tender_id="EVAL-006",
    category=TestCaseCategory.CLEAR_IRRELEVANT,
    title="Data Center Building Construction",
    description="""
    Construction of new data center facility including:
    - Reinforced concrete structure (5000 sqm)
    - Electrical infrastructure and power distribution
    - HVAC and cooling systems installation
    - Physical security (fencing, gates, surveillance)
    - Fire suppression systems
    
    Civil engineering and construction expertise required. Must comply
    with Tier III data center design standards.
    """,
    organization="National IT Infrastructure Agency",
    estimated_value="€15,000,000",
    expected_relevance=False,
    expected_confidence_min=0.92,
    expected_categories=[],
    notes="Physical construction, not software/IT services"
)

EVAL_007_CATERING = EvaluationTestCase(
    tender_id="EVAL-007",
    category=TestCaseCategory.CLEAR_IRRELEVANT,
    title="Conference Catering and Event Management",
    description="""
    Tech conference organizer needs catering services for 3-day event:
    - Daily breakfast, lunch, and coffee breaks for 500 attendees
    - Gala dinner for 400 people
    - Dietary accommodations (vegan, halal, kosher, allergies)
    - On-site event coordination staff
    - Audio-visual equipment rental
    """,
    organization="European Tech Summit",
    estimated_value="€120,000",
    expected_relevance=False,
    expected_confidence_min=0.98,
    expected_categories=[],
    notes="Event services, despite tech industry context"
)

EVAL_008_VEHICLE_FLEET = EvaluationTestCase(
    tender_id="EVAL-008",
    category=TestCaseCategory.CLEAR_IRRELEVANT,
    title="Electric Vehicle Fleet Procurement",
    description="""
    City government seeks to purchase and maintain electric vehicle fleet:
    - 50 electric sedans for administrative use
    - 20 electric vans for maintenance teams
    - Installation of 30 charging stations
    - 5-year maintenance and service contract
    - Driver training programs
    """,
    organization="City of Amsterdam",
    estimated_value="€2,800,000",
    expected_relevance=False,
    expected_confidence_min=0.94,
    expected_categories=[],
    notes="Vehicle procurement, not technology services"
)


# =============================================================================
# EDGE CASES - Ambiguous, borderline, or tricky scenarios
# =============================================================================

EVAL_009_HARDWARE_DOMINANT = EvaluationTestCase(
    tender_id="EVAL-009",
    category=TestCaseCategory.EDGE_CASE,
    title="Network Infrastructure Upgrade with Management Software",
    description="""
    Hospital network infrastructure modernization project:
    - Replace 500 network switches and routers (80% of budget)
    - Install fiber optic cabling throughout facility
    - Configure network monitoring software
    - Basic network management dashboard (20% of budget)
    
    Hardware procurement and installation is primary focus. Software
    component is standard vendor tool configuration.
    """,
    organization="Regional Hospital Network",
    estimated_value="€900,000",
    expected_relevance=False,
    expected_confidence_min=0.70,
    expected_categories=[],
    edge_case_reasoning="Primarily hardware (80%), minimal software component",
    notes="Test filter precision: can agent correctly reject hardware-heavy projects?"
)

EVAL_010_LOW_CODE_PLATFORM = EvaluationTestCase(
    tender_id="EVAL-010",
    category=TestCaseCategory.EDGE_CASE,
    title="No-Code Platform Implementation and Training",
    description="""
    Small business association wants to implement Microsoft Power Platform:
    - Configure Power Apps for membership management
    - Set up Power Automate workflows
    - Power BI dashboard for analytics
    - 5-day training workshop for 20 staff members
    
    No custom development required. Primarily configuration and training
    on vendor platform.
    """,
    organization="Small Business Federation",
    estimated_value="€45,000",
    expected_relevance=False,
    expected_confidence_min=0.65,
    expected_categories=[],
    edge_case_reasoning="Configuration vs development boundary; low value",
    notes="Tests whether agent recognizes difference between custom dev and platform config"
)

EVAL_011_AI_BUT_HARDWARE = EvaluationTestCase(
    tender_id="EVAL-011",
    category=TestCaseCategory.EDGE_CASE,
    title="AI-Enabled Security Cameras Procurement",
    description="""
    Smart city initiative for AI-powered surveillance system:
    - 200 AI-capable security cameras with edge processing (70% budget)
    - Centralized video management software (licensing only)
    - Some custom integration with city systems (30% budget)
    
    The AI capabilities are embedded in camera hardware. Limited software
    development for integration APIs.
    """,
    organization="Smart City Authority",
    estimated_value="€1,200,000",
    expected_relevance=False,
    expected_confidence_min=0.60,
    expected_categories=[],
    edge_case_reasoning="AI mentioned but primarily hardware procurement",
    notes="Tests if 'AI' keyword causes false positive when context is hardware"
)

EVAL_012_RESEARCH_NOT_PRODUCT = EvaluationTestCase(
    tender_id="EVAL-012",
    category=TestCaseCategory.EDGE_CASE,
    title="Cybersecurity Research Study and White Paper",
    description="""
    University research grant for cybersecurity study:
    - Literature review of emerging threats
    - Theoretical framework development
    - Survey of industry practices
    - Academic white paper publication
    - Conference presentation
    
    This is pure research work, no system development or implementation.
    Academic credentials and publication record required.
    """,
    organization="European Cybersecurity Research Institute",
    estimated_value="€75,000",
    expected_relevance=False,
    expected_confidence_min=0.70,
    expected_categories=[],
    edge_case_reasoning="Cybersecurity topic but research, not development",
    notes="Tests domain keyword filtering vs actual service type"
)

EVAL_013_MAINTENANCE_ONLY = EvaluationTestCase(
    tender_id="EVAL-013",
    category=TestCaseCategory.EDGE_CASE,
    title="Legacy System Maintenance and Support",
    description="""
    Government agency needs maintenance for existing COBOL-based system:
    - Bug fixes and minor patches
    - 24/7 on-call support
    - Documentation updates
    - No new features or modernization
    - COBOL and mainframe expertise required
    
    5-year maintenance contract for legacy system with no development work.
    """,
    organization="Tax Administration",
    estimated_value="€600,000",
    expected_relevance=False,
    expected_confidence_min=0.65,
    expected_categories=[],
    edge_case_reasoning="Software-related but pure maintenance, outdated tech",
    notes="Tests if agent distinguishes development from maintenance"
)


# =============================================================================
# RATING VALIDATION CASES - For testing scoring accuracy
# =============================================================================

EVAL_014_HIGH_VALUE_LOW_FIT = EvaluationTestCase(
    tender_id="EVAL-014",
    category=TestCaseCategory.RATING_VALIDATION,
    title="Aerospace Software System Development",
    description="""
    Space agency requires mission-critical software for satellite control:
    - Real-time embedded systems (C/C++)
    - Extreme reliability requirements (aerospace standards)
    - 10-year maintenance commitment
    - Security clearance at highest level required
    - Must demonstrate aerospace industry experience
    
    Very high contract value but requires specialized aerospace expertise,
    security clearances, and long-term commitment that may not match
    a small tech consultancy profile.
    """,
    organization="European Space Agency",
    estimated_value="€8,000,000",
    expected_relevance=True,
    expected_confidence_min=0.75,
    expected_categories=["software"],
    expected_score_range=(4.0, 6.0),
    expected_recommendation="no-go",
    notes="High value but poor strategic fit - tests if rating considers company profile"
)

EVAL_015_PERFECT_FIT_SMALL = EvaluationTestCase(
    tender_id="EVAL-015",
    category=TestCaseCategory.RATING_VALIDATION,
    title="Cybersecurity Assessment for Startup Incubator",
    description="""
    Tech incubator needs security services for 20 startup companies:
    - Web application security audits
    - Basic penetration testing
    - Security awareness training
    - Quarterly vulnerability scans
    - Standard technology stack (web apps, APIs)
    
    Perfect match for capabilities but relatively small contract value.
    Low complexity, good for portfolio building.
    """,
    organization="TechHub Incubator",
    estimated_value="€85,000",
    expected_relevance=True,
    expected_confidence_min=0.90,
    expected_categories=["cybersecurity", "software"],
    expected_score_range=(6.5, 8.0),
    expected_recommendation="go",
    notes="Perfect fit but low value - tests scoring balance"
)

EVAL_016_COMPETITIVE_MARKET = EvaluationTestCase(
    tender_id="EVAL-016",
    category=TestCaseCategory.RATING_VALIDATION,
    title="Standard Website Development for Municipality",
    description="""
    City government needs new public-facing website:
    - Standard CMS implementation (WordPress/Drupal)
    - Responsive design, accessibility compliance
    - Content migration from old site
    - Basic contact forms and search
    - 12-month support period
    
    Straightforward project but highly competitive market segment with
    many qualified bidders. Likely won on price rather than expertise.
    """,
    organization="City of Brussels",
    estimated_value="€120,000",
    expected_relevance=True,
    expected_confidence_min=0.85,
    expected_categories=["software"],
    expected_score_range=(5.0, 6.5),
    expected_recommendation="no-go",
    notes="Relevant but commoditized, low win probability"
)


# =============================================================================
# CATEGORY-SPECIFIC TESTS - Challenge category detection
# =============================================================================

EVAL_017_MULTI_CATEGORY = EvaluationTestCase(
    tender_id="EVAL-017",
    category=TestCaseCategory.CATEGORY_TEST,
    title="Intelligent Security Operations Center Solution",
    description="""
    Build next-generation SOC combining multiple technology areas:
    - AI/ML for threat detection and prediction
    - Security information and event management (SIEM)
    - Custom software development for SOC automation
    - Integration with existing security tools
    - Advanced analytics and threat intelligence
    
    Comprehensive solution requiring expertise across AI, cybersecurity,
    and software development.
    """,
    organization="Financial Services Authority",
    estimated_value="€2,200,000",
    expected_relevance=True,
    expected_confidence_min=0.88,
    expected_categories=["cybersecurity", "ai", "software"],
    expected_score_range=(8.0, 9.5),
    expected_recommendation="go",
    notes="Should detect all three categories"
)

EVAL_018_AI_ONLY = EvaluationTestCase(
    tender_id="EVAL-018",
    category=TestCaseCategory.CATEGORY_TEST,
    title="Natural Language Processing Model Development",
    description="""
    Insurance company needs NLP solution for claims processing:
    - Custom transformer-based models for text classification
    - Named entity recognition for insurance documents
    - Sentiment analysis of customer feedback
    - Model training pipeline and MLOps infrastructure
    - No security-specific requirements
    - Standard business application context
    """,
    organization="European Insurance Group",
    estimated_value="€650,000",
    expected_relevance=True,
    expected_confidence_min=0.85,
    expected_categories=["ai"],
    expected_score_range=(7.0, 8.5),
    notes="Pure AI/ML project, should not tag as cybersecurity"
)


# =============================================================================
# Collect all test cases
# =============================================================================

ALL_TEST_CASES: List[EvaluationTestCase] = [
    # Clear relevant
    EVAL_001_AI_CYBERSECURITY,
    EVAL_002_CUSTOM_SOFTWARE,
    EVAL_003_ML_PLATFORM,
    EVAL_004_SECURITY_AUDIT,
    
    # Clear irrelevant
    EVAL_005_OFFICE_FURNITURE,
    EVAL_006_CONSTRUCTION,
    EVAL_007_CATERING,
    EVAL_008_VEHICLE_FLEET,
    
    # Edge cases
    EVAL_009_HARDWARE_DOMINANT,
    EVAL_010_LOW_CODE_PLATFORM,
    EVAL_011_AI_BUT_HARDWARE,
    EVAL_012_RESEARCH_NOT_PRODUCT,
    EVAL_013_MAINTENANCE_ONLY,
    
    # Rating validation
    EVAL_014_HIGH_VALUE_LOW_FIT,
    EVAL_015_PERFECT_FIT_SMALL,
    EVAL_016_COMPETITIVE_MARKET,
    
    # Category tests
    EVAL_017_MULTI_CATEGORY,
    EVAL_018_AI_ONLY,
]


def get_test_cases_by_category(category: TestCaseCategory) -> List[EvaluationTestCase]:
    """Get all test cases for a specific category"""
    return [tc for tc in ALL_TEST_CASES if tc.category == category]


def get_relevant_test_cases() -> List[EvaluationTestCase]:
    """Get all test cases that should be classified as relevant"""
    return [tc for tc in ALL_TEST_CASES if tc.expected_relevance]


def get_irrelevant_test_cases() -> List[EvaluationTestCase]:
    """Get all test cases that should be classified as irrelevant"""
    return [tc for tc in ALL_TEST_CASES if not tc.expected_relevance]


# Statistics for dataset balance
DATASET_STATS = {
    "total_cases": len(ALL_TEST_CASES),
    "relevant_cases": len(get_relevant_test_cases()),
    "irrelevant_cases": len(get_irrelevant_test_cases()),
    "clear_relevant": len(get_test_cases_by_category(TestCaseCategory.CLEAR_RELEVANT)),
    "clear_irrelevant": len(get_test_cases_by_category(TestCaseCategory.CLEAR_IRRELEVANT)),
    "edge_cases": len(get_test_cases_by_category(TestCaseCategory.EDGE_CASE)),
    "rating_validation": len(get_test_cases_by_category(TestCaseCategory.RATING_VALIDATION)),
    "category_tests": len(get_test_cases_by_category(TestCaseCategory.CATEGORY_TEST)),
}
