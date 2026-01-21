"""
Script to seed all 93 ISO 27001 controls into Pinecone knowledge base.
This makes controls searchable for AI chat assistant and gap analysis.

Usage:
    python seed_controls_to_pinecone.py
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal
from app.models import Control, Framework, ControlGroup
from app.services.pinecone_service import index_control_embedding


# All 93 controls with their descriptions
CONTROLS_DATA = [
    # A.5 - Organizational controls (37 controls)
    ("A.5.1", "Policies for information security", "Create and maintain Information security policies approved by management."),
    ("A.5.2", "Information security roles and responsibilities", "Clearly define who is responsible for security tasks and decisions."),
    ("A.5.3", "Segregation of duties", "Divide tasks so no single person can misuse access or commit fraud."),
    ("A.5.4", "Management responsibilities", "Management must actively support and enforce security policies."),
    ("A.5.5", "Contact with authorities", "Establish procedures for reporting security incidents to legal authorities."),
    ("A.5.6", "Contact with special interest groups", "Manage relationships with security groups and forums appropriately."),
    ("A.5.7", "Threat intelligence", "Collect and analyze information about potential threats to the organization."),
    ("A.5.8", "Information security in project management", "Include security requirements in all project planning and execution."),
    ("A.5.9", "Inventory of Information and assets", "Keep a list of all information assets (hardware, software, data)."),
    ("A.5.10", "Acceptance of information and other associated assets", "Verify and document all assets before adding them to inventory."),
    ("A.5.11", "Return of assets", "Ensure all assets are returned when employees leave or contracts end."),
    ("A.5.12", "Classification of information", "Classify data (e.g., public, internal, confidential) based on sensitivity."),
    ("A.5.13", "Labelling of information", "Label all information according to its classification level."),
    ("A.5.14", "Information transfer", "Protect data when transferring via email, FTP, or physical media."),
    ("A.5.15", "Access control", "Control who can access what information and systems."),
    ("A.5.16", "Identity management", "Manage user identities and their access rights throughout their lifecycle."),
    ("A.5.17", "Authentication information", "Securely manage passwords, tokens, and other authentication credentials."),
    ("A.5.18", "Access rights", "Grant, review, and revoke access rights based on job requirements."),
    ("A.5.19", "Information security in supplier relationships", "Ensure suppliers meet your security requirements."),
    ("A.5.20", "Addressing information security within supplier agreements", "Include security clauses in all supplier contracts."),
    ("A.5.21", "Managing information security in the ICT supply chain", "Assess and manage security risks in your technology supply chain."),
    ("A.5.22", "Monitoring, review and change management of supplier services", "Regularly review supplier security practices and contracts."),
    ("A.5.23", "Information security for use of cloud services", "Ensure cloud providers meet your organization's security needs."),
    ("A.5.24", "Information security incident management planning and preparation", "Plan how to detect, report, and respond to security incidents."),
    ("A.5.25", "Assessment and decision on information security events", "Establish criteria for identifying and classifying security events."),
    ("A.5.26", "Response to information security incidents", "Have procedures to contain, investigate, and recover from incidents."),
    ("A.5.27", "Learning from information security incidents", "Document lessons learned and improve security based on incidents."),
    ("A.5.28", "Collection of evidence", "Preserve evidence during incident investigations following legal requirements."),
    ("A.5.29", "Information security during disruption", "Maintain security during business disruptions or emergencies."),
    ("A.5.30", "Information and communication technology readiness for business continuity", "Ensure IT systems can support business continuity plans."),
    ("A.5.31", "Legal, statutory, regulatory and contractual requirements", "Identify and comply with all applicable laws and contracts."),
    ("A.5.32", "Intellectual property rights", "Protect and respect intellectual property rights."),
    ("A.5.33", "Protection of records", "Protect important records from loss, destruction, or tampering."),
    ("A.5.34", "Privacy and protection of PII", "Protect personal data and comply with privacy laws."),
    ("A.5.35", "Independent review of information security", "Conduct regular independent security audits and reviews."),
    ("A.5.36", "Compliance with policies, rules and standards for information security", "Regularly check compliance with security policies and standards."),
    ("A.5.37", "Documented operating procedures", "Document all security procedures and keep them up to date."),
    
    # A.6 - People controls (8 controls)
    ("A.6.1", "Screening", "Background checks for new employees before hiring."),
    ("A.6.2", "Terms and conditions of employment", "Employment contracts must mention security responsibilities."),
    ("A.6.3", "Information security awareness, education and training", "Train employees on security policies and risks."),
    ("A.6.4", "Disciplinary process", "Have clear consequences for security policy violations."),
    ("A.6.5", "Termination or change of employment responsibilities", "Ensure ex-employees lose access and respect confidentiality."),
    ("A.6.6", "Confidentiality or non-disclosure agreements", "Require employees and contractors to sign confidentiality agreements."),
    ("A.6.7", "Remote working", "Secure devices and connections for remote workers."),
    ("A.6.8", "Information security event reporting", "Encourage employees to report security events and concerns."),
    
    # A.7 - Physical and environmental controls (14 controls)
    ("A.7.1", "Physical security perimeters", "Define and protect secure areas with barriers or access control."),
    ("A.7.2", "Physical entry control", "Restrict and monitor entry into buildings or rooms."),
    ("A.7.3", "Securing offices, rooms and facilities", "Secure all areas containing sensitive information or systems."),
    ("A.7.4", "Physical security monitoring", "Monitor physical access to secure areas continuously."),
    ("A.7.5", "Protecting against physical and environmental threats", "Protect facilities from fire, flood, or theft."),
    ("A.7.6", "Working in secure areas", "Control and monitor activities in secure areas."),
    ("A.7.7", "Supporting utilities", "Ensure stable power and air conditioning for IT systems."),
    ("A.7.8", "Cabling security", "Protect network and power cables from tampering or damage."),
    ("A.7.9", "Equipment maintenance", "Maintain equipment properly to prevent security issues."),
    ("A.7.10", "Secure disposal or re-use of equipment", "Erase data before disposing or reusing equipment."),
    ("A.7.11", "Clear desk and clear screen policy", "Avoid leaving sensitive info visible or unlocked."),
    ("A.7.12", "Equipment siting and protection", "Place and protect equipment to prevent unauthorized access."),
    ("A.7.13", "Storage media", "Securely store and handle all storage media."),
    ("A.7.14", "Supporting utilities", "Ensure reliable utilities (power, cooling) for IT systems."),
    
    # A.8 - Technological controls (34 controls)
    ("A.8.1", "User endpoint devices", "Secure laptops, mobiles, and desktops."),
    ("A.8.2", "Privileged access rights", "Restrict and monitor admin privileges."),
    ("A.8.3", "Information access restriction", "Limit access to information based on business needs."),
    ("A.8.4", "Access to source code", "Protect source code from unauthorized changes."),
    ("A.8.5", "Secure authentication", "Use strong passwords or MFA (multi-factor authentication)."),
    ("A.8.6", "Capacity management", "Monitor and manage system capacity to prevent service disruption."),
    ("A.8.7", "Protection against malware", "Use antivirus and keep systems updated."),
    ("A.8.8", "Management of technical vulnerabilities", "Patch systems and fix known vulnerabilities."),
    ("A.8.9", "Configuration management", "Document and control system configurations."),
    ("A.8.10", "Information deletion", "Securely delete data no longer needed."),
    ("A.8.11", "Data masking", "Mask sensitive data in non-production environments."),
    ("A.8.12", "Data loss prevention", "Use tools to prevent unauthorized data transfers."),
    ("A.8.13", "Backup", "Regularly back up important data securely."),
    ("A.8.14", "Redundancy", "Use redundant systems to ensure availability."),
    ("A.8.15", "Logging", "Record user and system activities."),
    ("A.8.16", "Monitoring activities", "Continuously monitor logs for suspicious actions."),
    ("A.8.17", "Clock synchronization", "Synchronize system clocks for accurate logging."),
    ("A.8.18", "Use of privileged utility programs", "Control and monitor use of admin tools."),
    ("A.8.19", "Installation of software on operational systems", "Only authorized people can install software."),
    ("A.8.20", "Networks security", "Protect network infrastructure with firewalls and segmentation."),
    ("A.8.21", "Segregation of networks", "Separate networks to limit breach impact."),
    ("A.8.22", "Web filtering", "Filter web traffic to block malicious sites."),
    ("A.8.23", "Use of cryptography", "Use encryption for data confidentiality and integrity."),
    ("A.8.24", "Secure development life cycle", "Apply security from design to deployment in development."),
    ("A.8.25", "Application security requirements", "Define security requirements for applications."),
    ("A.8.26", "Secure system architecture and engineering principles", "Design systems with security in mind."),
    ("A.8.27", "Secure coding", "Developers should follow secure coding standards."),
    ("A.8.28", "Security testing in development", "Test applications for security vulnerabilities during development."),
    ("A.8.29", "Security testing in acceptance", "Test applications before deploying to production."),
    ("A.8.30", "Outsourced development", "Ensure third-party developers follow security standards."),
    ("A.8.31", "Separation of development, test and production environments", "Keep development, test, and production environments separate."),
    ("A.8.32", "Change management", "Control and document all system changes."),
    ("A.8.33", "Test information", "Protect test data and avoid using production data in tests."),
    ("A.8.34", "Protection of information systems during audit testing", "Protect systems during security audits and tests."),
]


def seed_controls_to_pinecone(framework_name: str = "ISO 27001:2022"):
    """
    Seed all 93 controls into Pinecone knowledge base.
    """
    db = SessionLocal()
    
    try:
        # Get framework - try multiple name variations
        framework = db.query(Framework).filter(
            Framework.name.ilike("%ISO 27001%")
        ).first()
        
        if not framework:
            # Try without "ISO" prefix
            framework = db.query(Framework).filter(
                Framework.name.ilike("%27001%")
            ).first()
        
        if not framework:
            print(f"✗ ISO 27001 framework not found. Please seed the framework first.")
            return
        
        print(f"\n{'='*60}")
        print(f"Seeding Controls to Pinecone Knowledge Base")
        print(f"Framework: {framework.name} (ID: {framework.id})")
        print(f"Total Controls: {len(CONTROLS_DATA)}")
        print(f"{'='*60}\n")
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        # Process each control
        for idx, (control_code, control_name, description) in enumerate(CONTROLS_DATA, 1):
            print(f"\n[{idx}/{len(CONTROLS_DATA)}] Processing: {control_code} - {control_name}")
            
            # Extract control group code (e.g., "A.5" from "A.5.1")
            group_code = control_code.rsplit('.', 1)[0] if '.' in control_code else control_code.split('.')[0]
            
            # Find control group
            control_group = db.query(ControlGroup).filter(
                ControlGroup.code == group_code,
                ControlGroup.framework_id == framework.id
            ).first()
            
            if not control_group:
                print(f"  ⚠️  Control group '{group_code}' not found. Skipping...")
                skipped_count += 1
                continue
            
            # Find control in database
            control = db.query(Control).filter(
                Control.code == control_code,
                Control.control_group_id == control_group.id
            ).first()
            
            if not control:
                print(f"  ⚠️  Control '{control_code}' not found in database. Creating...")
                control = Control(
                    name=control_name,
                    description=description,
                    code=control_code,
                    control_group_id=control_group.id,
                    order_index=idx,
                    is_active=True
                )
                db.add(control)
                db.flush()
                print(f"  ✓ Control created in database (ID: {control.id})")
            else:
                # Update description if it exists
                if control.description != description:
                    control.description = description
                    db.flush()
                    print(f"  ✓ Control found (ID: {control.id}), description updated")
                else:
                    print(f"  ✓ Control found (ID: {control.id})")
            
            # Index control in Pinecone
            try:
                metadata = {
                    "framework_id": framework.id,
                    "control_group_id": control_group.id,
                    "control_group_code": group_code,
                }
                
                success = index_control_embedding(
                    control_id=control.id,
                    control_code=control_code,
                    control_name=control_name,
                    control_description=description,
                    framework_id=framework.id,
                    control_group_id=control_group.id,
                    metadata=metadata
                )
                
                if success:
                    indexed_count += 1
                    print(f"  ✓✓✓ Successfully indexed in Pinecone!")
                else:
                    skipped_count += 1
                    print(f"  ⚠️  Indexing returned False")
                    
            except Exception as e:
                error_count += 1
                print(f"  ✗✗✗ ERROR indexing: {str(e)}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
        
        # Commit database changes
        db.commit()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SEEDING SUMMARY")
        print(f"{'='*60}")
        print(f"Total controls processed: {len(CONTROLS_DATA)}")
        print(f"✓ Successfully indexed: {indexed_count}")
        print(f"⚠️  Skipped: {skipped_count}")
        print(f"✗ Errors: {error_count}")
        print(f"{'='*60}\n")
        
        if indexed_count > 0:
            print(f"🎉 Successfully indexed {indexed_count} controls in Pinecone!")
            print(f"\nControls are now available for:")
            print(f"  ✓ AI Chat Assistant queries")
            print(f"  ✓ Gap Analysis")
            print(f"  ✓ Control searches\n")
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"\n✗✗✗ FATAL ERROR: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_controls_to_pinecone()

