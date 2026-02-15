"""
Sample knowledge base documents for testing

This file contains high-quality example bid documents that can be imported
into the knowledge base to demonstrate RAG capabilities.
"""

SAMPLE_DOCUMENTS = [
    {
        "id": "kb_cybersecurity_001",
        "category": "cybersecurity",
        "title": "AI-Powered Threat Detection - Government Sector",
        "content": """## Executive Summary

Our proposed AI-powered threat detection solution delivers enterprise-grade security specifically tuned for government infrastructure. With 99.2% detection accuracy and sub-100ms response times, we address the critical need for real-time threat identification and automated containment.

Our team has successfully deployed similar systems for 15+ government agencies, maintaining a perfect security record across 50M+ daily transactions.

## Technical Approach

**Three-Tier Detection Architecture:**

1. **Real-Time Pattern Recognition**  
   Neural network models trained on 5+ years of government sector threat data, achieving 99.2% accuracy with <0.1% false positive rate. Models retrain weekly on newly identified threats.

2. **Behavioral Analytics**  
   Unsupervised learning algorithms identify zero-day threats and insider risks by detecting anomalous behavior patterns before they escalate to security incidents.

3. **Automated Response Integration**  
   Seamless integration with existing SIEM infrastructure (Splunk, QRadar, ArcSight), enabling immediate containment actions while alerting security teams through multiple channels.

## Implementation Timeline

- **Phase 1 (Weeks 1-4):** Infrastructure setup, data integration, baseline establishment
- **Phase 2 (Weeks 5-8):** Model training, validation against historical incident data
- **Phase 3 (Weeks 9-12):** Production deployment, team training, documentation handover

## Compliance & Certifications

Our team holds ISO 27001, SOC 2 Type II, and government security clearance. All data processing occurs on-premises, ensuring complete data sovereignty and regulatory compliance.""",
        "metadata": {
            "year": 2025,
            "success_rate": 0.95,
            "client_sector": "government"
        }
    },
    {
        "id": "kb_ai_predictive_001",
        "category": "ai",
        "title": "Predictive Maintenance AI Platform",
        "content": """## Solution Overview

Our predictive maintenance platform leverages advanced AI to reduce equipment downtime by 40% and maintenance costs by 25%. The system monitors 200+ sensor parameters in real-time, predicting failures 72 hours in advance with 94% accuracy.

## Technical Architecture

**Built on Open Standards:**  
TensorFlow, FastAPI, PostgreSQL - ensuring full transparency, no vendor lock-in, and seamless integration with existing systems.

**Data Pipeline:**  
Ingests sensor data at 1000 Hz, processes using Apache Kafka for real-time streaming, maintains 2-year historical archive for continuous model improvement.

**ML Models:**  
Ensemble approach combining LSTM networks (for temporal patterns) and Random Forests (for feature importance), retrained weekly with operational data feedback loop.

**Alert System:**  
Multi-channel notifications (email, SMS, dashboard) with configurable thresholds, escalation procedures, and work order integration.

## Proven Business Value

Based on 12-month pilot deployments:
- 40% reduction in unplanned downtime
- 25% decrease in maintenance costs  
- 15% extension of equipment lifespan
- ROI achieved within 8 months

## Team Expertise

Our lead architect (PhD ML, MIT) has deployed AI systems in 15+ industrial facilities. The team includes 3 PhDs, 8 senior engineers, all with 5+ years production AI experience.""",
        "metadata": {
            "year": 2025,
            "success_rate": 0.88,
            "roi_months": 8
        }
    },
    {
        "id": "kb_software_crm_001",
        "category": "software",
        "title": "Custom CRM System - Enterprise Grade",
        "content": """## Project Scope

We will develop a cloud-native CRM system tailored to your organization's unique workflows, replacing legacy systems while preserving 15 years of customer data integrity through zero-downtime migration.

## Development Methodology

**Agile with Weekly Client Reviews:**  
Every Friday, you see working software, provide feedback, and adjust priorities. This approach catches issues early and ensures the system matches your evolving needs.

**Technology Stack:**
- **Frontend:** React with TypeScript (type safety prevents 80% of runtime errors)
- **Backend:** Python FastAPI, PostgreSQL (battle-tested for enterprise scale)
- **Cloud:** AWS with auto-scaling (handles 10x traffic spikes seamlessly)
- **Security:** OAuth2, AES-256 encryption at rest and in transit, SOC 2 Type II certified

## Data Migration Strategy

**Zero Data Loss Guaranteed:**

1. Automated backup before each migration step  
2. Parallel running (old + new systems) for 30 days  
3. 100% data reconciliation validation before legacy shutdown  
4. Rollback plan at every stage

We've migrated 50M+ customer records across 20 projects with perfect track record.

## Support & Maintenance

- **Year 1:** Included in project cost (24/7 support, <2hr response time)
- **Year 2+:** Optional SLA packages with 99.9% uptime guarantee

## Client References

Similar CRM projects for [Company A] ($5M revenue increase) and [Company B] (35% productivity gain) available for reference calls.""",
        "metadata": {
            "year": 2024,
            "success_rate": 0.92,
            "project_scale": "enterprise"
        }
    },
    {
        "id": "kb_data_analytics_001",
        "category": "data_analytics",
        "title": "Business Intelligence Dashboard Suite",
        "content": """## Vision

Transform raw operational data into actionable insights with real-time dashboards that executives actually use. Our BI platform consolidates 15+ data sources into unified, drill-down visualizations accessible from any device.

## Key Features

**Executive Dashboard:**  
6 critical KPIs updated every 5 minutes - revenue trends with ML forecasting, operational efficiency metrics, customer satisfaction tracking, all with historical comparison and anomaly alerts.

**Departmental Views:**  
Customized dashboards for sales (pipeline, conversion rates), operations (throughput, bottlenecks), and finance (cash flow, profitability) with role-based access control.

**Mobile-First Design:**  
Full functionality on tablets and phones - executives check KPIs during commute, managers respond to alerts in real-time.

## Technical Implementation

**Platform:** Tableau/Power BI (client preference) with custom connectors for your ERP, CRM, and legacy systems.

**Data Pipeline:**  
Hourly ETL processes with data quality validation at each step (completeness checks, anomaly detection, referential integrity).

**Performance:**  
2-second page loads even with 5-year historical data (10M+ records), achieved through intelligent caching and incremental updates.

## Training & Adoption

3-day workshop for power users plus recorded tutorials for all staff. Our approach achieves 85% adoption rate within first month (vs. industry average of 40%).

## ROI Typically

Clients report 20% faster decision-making, 30% reduction in reporting overhead, and £200K+ annual savings from operational insights.""",
        "metadata": {
            "year": 2025,
            "success_rate": 0.87,
            "adoption_rate": 0.85
        }
    },
    {
        "id": "kb_cloud_migration_001",
        "category": "cloud",
        "title": "AWS Cloud Migration - Zero Downtime",
        "content": """## Migration Strategy

We execute low-risk, phased cloud migrations that maintain business continuity. Your customers experience zero downtime, and you gain cloud benefits immediately.

## Our Proven Approach

**Assessment Phase (Weeks 1-2):**
- Inventory all applications and dependencies (automated discovery tools)
- Categorize by migration complexity (lift-and-shift vs. re-architecture)
- Identify quick wins and cost optimization opportunities
- Risk analysis with mitigation strategies

**Migration Waves:**

*Wave 1 - Non-critical systems*  
Build confidence, test procedures, train team (weeks 3-6)

*Wave 2 - Business applications*  
Migrate during low-usage windows with immediate rollback capability (weeks 7-12)

*Wave 3 - Mission-critical services*  
Full redundancy, comprehensive testing, staged cutover (weeks 13-16)

## Cloud Architecture

**High Availability:**  
Multi-AZ deployment across 3 availability zones, automatic failover, 99.99% uptime SLA

**Auto-Scaling:**  
Handles traffic spikes automatically (tested to 10x normal load), reduces costs during low usage (typically 30-40% savings vs. on-demand pricing)

**Disaster Recovery:**  
RPO = 1 hour, RTO = 4 hours, automated backups, tested quarterly

## Cost Governance

Budget alerts, rightsizing recommendations (right-sizing reduces costs 30-40%), reserved instance strategies, detailed cost allocation by department.

## Security & Compliance

All resources configured following CIS benchmarks, continuous monitoring via AWS Security Hub, automated compliance reporting for SOC 2, ISO 27001, GDPR.""",
        "metadata": {
            "year": 2025,
            "success_rate": 0.91,
            "average_savings": 0.35
        }
    }
]


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    
    # Export to JSON for easy import
    output_file = Path(__file__).parent.parent / "data" / "sample_kb.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(SAMPLE_DOCUMENTS, f, indent=2)
    
    print(f"✅ Exported {len(SAMPLE_DOCUMENTS)} sample documents to {output_file}")
    print("\nTo import into knowledge base:")
    print(f"  python scripts/manage_kb.py import {output_file}")
