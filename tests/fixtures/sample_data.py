"""
Sample tender data for testing
"""

SAMPLE_TENDERS = [
    {
        "title": "AI-Powered Cybersecurity Platform Development",
        "description": """
        The National Cybersecurity Agency requires a sophisticated AI-based threat 
        detection and response system. The solution must integrate machine learning 
        algorithms for real-time threat analysis, automated incident response, and 
        comprehensive security monitoring across cloud and on-premise infrastructure.
        
        Key requirements:
        - Real-time threat detection using ML/AI
        - Integration with existing SIEM systems
        - Automated incident response workflows
        - Compliance with government security standards
        - 24/7 monitoring and support
        """,
        "organization_name": "National Cybersecurity Agency",
        "deadline": "2025-04-15",
        "estimated_value": "€2,000,000",
        "external_id": "NCA-2025-001",
        "source": "ted_europa",
    },
    {
        "title": "Cloud Migration Services for Legacy Systems",
        "description": """
        Ministry of Finance seeks experienced cloud migration partner to modernize 
        legacy systems. Project involves migrating 50+ applications to cloud 
        infrastructure while maintaining data security and compliance.
        """,
        "organization_name": "Ministry of Finance",
        "deadline": "2025-05-30",
        "estimated_value": "€1,500,000",
        "external_id": "MOF-2025-042",
        "source": "ted_europa",
    },
    {
        "title": "Office Furniture Supply Contract",
        "description": """
        City council requires office furniture for new administrative building.
        Includes desks, chairs, filing cabinets, and meeting room furniture.
        """,
        "organization_name": "City Council",
        "deadline": "2025-03-20",
        "estimated_value": "€50,000",
        "external_id": "CC-2025-18",
        "source": "manual",
    },
]

MOCK_LLM_RESPONSES = {
    "filter_match": """
    {
        "is_match": true,
        "confidence": 0.85,
        "reasoning": "Strong alignment with company capabilities in AI/ML and cybersecurity"
    }
    """,
    "filter_no_match": """
    {
        "is_match": false,
        "confidence": 0.92,
        "reasoning": "Tender is for office furniture, outside our technology services focus"
    }
    """,
    "rating_high": """
    {
        "score": 90,
        "reasoning": "Excellent strategic fit with strong revenue potential",
        "pros": [
            "Large contract value (€2M)",
            "Government client provides stability",
            "Perfect match for AI/ML expertise",
            "Long-term partnership opportunity"
        ],
        "cons": [
            "Tight deadline may be challenging",
            "Government compliance requirements",
            "High competition expected"
        ]
    }
    """,
    "rating_medium": """
    {
        "score": 65,
        "reasoning": "Moderate fit with acceptable terms",
        "pros": [
            "Reasonable contract value",
            "Standard cloud migration services"
        ],
        "cons": [
            "Legacy system complexity unknown",
            "Potential scope creep risk"
        ]
    }
    """,
    "proposal": """
    # Proposal: AI-Powered Cybersecurity Platform
    
    ## Executive Summary
    We propose a comprehensive AI-driven cybersecurity solution leveraging our 10+ years 
    of experience in machine learning and threat detection.
    
    ## Technical Approach
    Our solution combines:
    - Advanced ML algorithms for threat detection
    - Real-time monitoring and automated response
    - Seamless SIEM integration
    
    ## Timeline
    - Month 1-2: Requirements and design
    - Month 3-6: Development and testing
    - Month 7-8: Deployment and training
    
    ## Pricing
    Total project cost: €1,850,000 (competitive 7.5% under budget)
    """,
}
