"""Sample tender data for testing and examples"""

from procurement_ai.models import Tender

SAMPLE_TENDERS = [
    Tender(
        id="TED-2025-001",
        title="AI-Powered Cybersecurity Platform for Critical Infrastructure",
        description="""The National Cybersecurity Agency seeks a vendor to develop an 
        artificial intelligence-based threat detection and response system. The solution 
        must monitor network traffic across government infrastructure, identify anomalies 
        using machine learning, and provide automated incident response. Integration with 
        existing SIEM tools required. Must handle 100TB+ daily data volume with real-time 
        processing capabilities.""",
        organization="National Cybersecurity Agency",
        deadline="2025-04-15",
        estimated_value="€3,200,000",
    ),
    Tender(
        id="TED-2025-002",
        title="Office Furniture Procurement for New Government Building",
        description="""Supply and installation of ergonomic office furniture for 500 
        workstations including desks, chairs, storage cabinets, and meeting room furniture. 
        Must meet sustainability criteria and include 5-year warranty.""",
        organization="Ministry of Public Works",
        deadline="2025-03-01",
        estimated_value="€450,000",
    ),
    Tender(
        id="TED-2025-003",
        title="Custom CRM Software Development for Healthcare Network",
        description="""Healthcare network requires custom customer relationship management 
        software to manage patient interactions, appointment scheduling, and medical records 
        integration. Must be GDPR and HIPAA compliant, include mobile app, and integrate 
        with existing hospital management systems. Cloud-based SaaS solution preferred.""",
        organization="Regional Healthcare Authority",
        deadline="2025-05-30",
        estimated_value="€1,800,000",
    ),
]
