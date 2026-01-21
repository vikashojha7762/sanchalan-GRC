"""
Seed script for ISO 27001:2022 framework with control groups A.5, A.6, A.7, A.8
"""
from sqlalchemy.orm import Session
from app.models import Framework, ControlGroup, Control


def seed_iso27001(db: Session):
    """
    Seed ISO 27001:2022 framework with control groups A.5, A.6, A.7, A.8
    """
    # Create or get ISO 27001 framework
    framework = db.query(Framework).filter(
        Framework.name.ilike("%ISO 27001%")
    ).first()
    
    if not framework:
        framework = Framework(
            name="ISO 27001:2022",
            description="Information Security Management System - International Standard",
            version="2022",
            category="Security",
            is_active=True
        )
        db.add(framework)
        db.flush()
    else:
        # Don't delete existing groups - use get_or_create pattern to preserve IDs
        # This ensures control IDs remain stable across seed operations
        print(f"[Seed ISO27001] Framework exists (ID: {framework.id}), using get_or_create pattern")
        db.flush()
    
    # A.5 - Organizational controls (37 controls)
    # Use get_or_create to preserve existing group and control IDs
    a5_group = db.query(ControlGroup).filter(
        ControlGroup.framework_id == framework.id,
        ControlGroup.code == "A.5"
    ).first()
    
    if not a5_group:
        a5_group = ControlGroup(
            name="A.5 - Organizational controls",
            description="Policies for information security, roles and responsibilities, segregation of duties, management responsibilities, contact with authorities, contact with special interest groups, threat intelligence, information security in project management, inventory of information and other associated assets, acceptance of information and other associated assets, return of assets, classification of information, labelling of information, information transfer, access control, identity management, authentication information, access rights, information security in supplier relationships, addressing information security within supplier agreements, managing information security in the ICT supply chain, monitoring, review and change management of supplier services, information security for use of cloud services, information security incident management planning and preparation, assessment and decision on information security events, response to information security incidents, learning from information security incidents, collection of evidence, information security during disruption, information and communication technology readiness for business continuity, legal, statutory, regulatory and contractual requirements, intellectual property rights, protection of records, privacy and protection of PII, independent review of information security, compliance with policies, rules and standards for information security, documented operating procedures",
            code="A.5",
            framework_id=framework.id,
            order_index=5,
            is_active=True
        )
        db.add(a5_group)
        db.flush()
        print(f"[Seed ISO27001] Created A.5 group (ID: {a5_group.id})")
    else:
        print(f"[Seed ISO27001] A.5 group exists (ID: {a5_group.id})")
        a5_group.is_active = True  # Ensure it's active
    
    # A.5 controls (37 controls)
    a5_controls = [
        ("A.5.1", "Policies for information security"),
        ("A.5.2", "Roles and responsibilities"),
        ("A.5.3", "Segregation of duties"),
        ("A.5.4", "Management responsibilities"),
        ("A.5.5", "Contact with authorities"),
        ("A.5.6", "Contact with special interest groups"),
        ("A.5.7", "Threat intelligence"),
        ("A.5.8", "Information security in project management"),
        ("A.5.9", "Inventory of information and other associated assets"),
        ("A.5.10", "Acceptance of information and other associated assets"),
        ("A.5.11", "Return of assets"),
        ("A.5.12", "Classification of information"),
        ("A.5.13", "Labelling of information"),
        ("A.5.14", "Information transfer"),
        ("A.5.15", "Access control"),
        ("A.5.16", "Identity management"),
        ("A.5.17", "Authentication information"),
        ("A.5.18", "Access rights"),
        ("A.5.19", "Information security in supplier relationships"),
        ("A.5.20", "Addressing information security within supplier agreements"),
        ("A.5.21", "Managing information security in the ICT supply chain"),
        ("A.5.22", "Monitoring, review and change management of supplier services"),
        ("A.5.23", "Information security for use of cloud services"),
        ("A.5.24", "Information security incident management planning and preparation"),
        ("A.5.25", "Assessment and decision on information security events"),
        ("A.5.26", "Response to information security incidents"),
        ("A.5.27", "Learning from information security incidents"),
        ("A.5.28", "Collection of evidence"),
        ("A.5.29", "Information security during disruption"),
        ("A.5.30", "Information and communication technology readiness for business continuity"),
        ("A.5.31", "Legal, statutory, regulatory and contractual requirements"),
        ("A.5.32", "Intellectual property rights"),
        ("A.5.33", "Protection of records"),
        ("A.5.34", "Privacy and protection of PII"),
        ("A.5.35", "Independent review of information security"),
        ("A.5.36", "Compliance with policies, rules and standards for information security"),
        ("A.5.37", "Documented operating procedures"),
    ]
    
    for idx, (code, name) in enumerate(a5_controls, 1):
        # Use get_or_create to preserve existing control IDs
        control = db.query(Control).filter(
            Control.control_group_id == a5_group.id,
            Control.code == code
        ).first()
        
        if not control:
            control = Control(
                name=name,
                description=f"ISO 27001:2022 Control {code}",
                code=code,
                control_group_id=a5_group.id,
                order_index=idx,
                is_active=True
            )
            db.add(control)
            db.flush()
            print(f"[Seed ISO27001] Created control {code} (ID: {control.id})")
        else:
            # Update existing control to ensure it's active and has correct data
            control.name = name
            control.description = f"ISO 27001:2022 Control {code}"
            control.order_index = idx
            control.is_active = True
            print(f"[Seed ISO27001] Control {code} exists (ID: {control.id})")
    
    # A.6 - People controls (8 controls)
    a6_group = db.query(ControlGroup).filter(
        ControlGroup.framework_id == framework.id,
        ControlGroup.code == "A.6"
    ).first()
    
    if not a6_group:
        a6_group = ControlGroup(
            name="A.6 - People controls",
            description="Screening, terms and conditions of employment, information security awareness, education and training, disciplinary process, termination or change of employment responsibilities, confidentiality or non-disclosure agreements, remote working",
            code="A.6",
            framework_id=framework.id,
            order_index=6,
            is_active=True
        )
        db.add(a6_group)
        db.flush()
        print(f"[Seed ISO27001] Created A.6 group (ID: {a6_group.id})")
    else:
        print(f"[Seed ISO27001] A.6 group exists (ID: {a6_group.id})")
        a6_group.is_active = True
    
    # A.6 controls (8 controls)
    a6_controls = [
        ("A.6.1", "Screening"),
        ("A.6.2", "Terms and conditions of employment"),
        ("A.6.3", "Information security awareness, education and training"),
        ("A.6.4", "Disciplinary process"),
        ("A.6.5", "Termination or change of employment responsibilities"),
        ("A.6.6", "Confidentiality or non-disclosure agreements"),
        ("A.6.7", "Remote working"),
        ("A.6.8", "Information security event reporting"),
    ]
    
    for idx, (code, name) in enumerate(a6_controls, 1):
        control = db.query(Control).filter(
            Control.control_group_id == a6_group.id,
            Control.code == code
        ).first()
        
        if not control:
            control = Control(
                name=name,
                description=f"ISO 27001:2022 Control {code}",
                code=code,
                control_group_id=a6_group.id,
                order_index=idx,
                is_active=True
            )
            db.add(control)
            db.flush()
            print(f"[Seed ISO27001] Created control {code} (ID: {control.id})")
        else:
            control.name = name
            control.description = f"ISO 27001:2022 Control {code}"
            control.order_index = idx
            control.is_active = True
            print(f"[Seed ISO27001] Control {code} exists (ID: {control.id})")
    
    # A.7 - Physical and environmental controls (14 controls)
    a7_group = db.query(ControlGroup).filter(
        ControlGroup.framework_id == framework.id,
        ControlGroup.code == "A.7"
    ).first()
    
    if not a7_group:
        a7_group = ControlGroup(
            name="A.7 - Physical and environmental controls",
            description="Physical security perimeters, physical entry, securing offices, rooms and facilities, physical security monitoring, protecting against physical and environmental threats, working in secure areas, supporting utilities, cabling security, equipment maintenance, secure disposal or re-use of equipment, clear desk and clear screen, equipment siting and protection, storage media, supporting utilities, cabling security",
            code="A.7",
            framework_id=framework.id,
            order_index=7,
            is_active=True
        )
        db.add(a7_group)
        db.flush()
        print(f"[Seed ISO27001] Created A.7 group (ID: {a7_group.id})")
    else:
        print(f"[Seed ISO27001] A.7 group exists (ID: {a7_group.id})")
        a7_group.is_active = True
    
    # A.7 controls (14 controls)
    a7_controls = [
        ("A.7.1", "Physical security perimeters"),
        ("A.7.2", "Physical entry"),
        ("A.7.3", "Securing offices, rooms and facilities"),
        ("A.7.4", "Physical security monitoring"),
        ("A.7.5", "Protecting against physical and environmental threats"),
        ("A.7.6", "Working in secure areas"),
        ("A.7.7", "Supporting utilities"),
        ("A.7.8", "Cabling security"),
        ("A.7.9", "Equipment maintenance"),
        ("A.7.10", "Secure disposal or re-use of equipment"),
        ("A.7.11", "Clear desk and clear screen"),
        ("A.7.12", "Equipment siting and protection"),
        ("A.7.13", "Storage media"),
        ("A.7.14", "Supporting utilities"),
    ]
    
    for idx, (code, name) in enumerate(a7_controls, 1):
        control = db.query(Control).filter(
            Control.control_group_id == a7_group.id,
            Control.code == code
        ).first()
        
        if not control:
            control = Control(
                name=name,
                description=f"ISO 27001:2022 Control {code}",
                code=code,
                control_group_id=a7_group.id,
                order_index=idx,
                is_active=True
            )
            db.add(control)
            db.flush()
            print(f"[Seed ISO27001] Created control {code} (ID: {control.id})")
        else:
            control.name = name
            control.description = f"ISO 27001:2022 Control {code}"
            control.order_index = idx
            control.is_active = True
            print(f"[Seed ISO27001] Control {code} exists (ID: {control.id})")
    
    # A.8 - Technological controls (34 controls)
    a8_group = db.query(ControlGroup).filter(
        ControlGroup.framework_id == framework.id,
        ControlGroup.code == "A.8"
    ).first()
    
    if not a8_group:
        a8_group = ControlGroup(
            name="A.8 - Technological controls",
            description="User endpoint devices, privilege management, information access restriction, access to source code, secure authentication, capacity management, protection against malware, management of technical vulnerabilities, configuration management, information deletion, data masking, data leakage prevention, backup, redundancy, logging, monitoring activities, clock synchronization, use of privileged utility programs, installation of software on operational systems, networks security, segregation of networks, web filtering, use of cryptography, secure development life cycle, application security requirements, secure system architecture and engineering principles, secure coding, security testing in development, security testing in acceptance, outsourced development, separation of development, test and production environments, change management, test information, protection of information systems during audit testing",
            code="A.8",
            framework_id=framework.id,
            order_index=8,
            is_active=True
        )
        db.add(a8_group)
        db.flush()
        print(f"[Seed ISO27001] Created A.8 group (ID: {a8_group.id})")
    else:
        print(f"[Seed ISO27001] A.8 group exists (ID: {a8_group.id})")
        a8_group.is_active = True
    
    # A.8 controls (34 controls)
    a8_controls = [
        ("A.8.1", "User endpoint devices"),
        ("A.8.2", "Privilege management"),
        ("A.8.3", "Information access restriction"),
        ("A.8.4", "Access to source code"),
        ("A.8.5", "Secure authentication"),
        ("A.8.6", "Capacity management"),
        ("A.8.7", "Protection against malware"),
        ("A.8.8", "Management of technical vulnerabilities"),
        ("A.8.9", "Configuration management"),
        ("A.8.10", "Information deletion"),
        ("A.8.11", "Data masking"),
        ("A.8.12", "Data leakage prevention"),
        ("A.8.13", "Backup"),
        ("A.8.14", "Redundancy"),
        ("A.8.15", "Logging"),
        ("A.8.16", "Monitoring activities"),
        ("A.8.17", "Clock synchronization"),
        ("A.8.18", "Use of privileged utility programs"),
        ("A.8.19", "Installation of software on operational systems"),
        ("A.8.20", "Networks security"),
        ("A.8.21", "Segregation of networks"),
        ("A.8.22", "Web filtering"),
        ("A.8.23", "Use of cryptography"),
        ("A.8.24", "Secure development life cycle"),
        ("A.8.25", "Application security requirements"),
        ("A.8.26", "Secure system architecture and engineering principles"),
        ("A.8.27", "Secure coding"),
        ("A.8.28", "Security testing in development"),
        ("A.8.29", "Security testing in acceptance"),
        ("A.8.30", "Outsourced development"),
        ("A.8.31", "Separation of development, test and production environments"),
        ("A.8.32", "Change management"),
        ("A.8.33", "Test information"),
        ("A.8.34", "Protection of information systems during audit testing"),
    ]
    
    for idx, (code, name) in enumerate(a8_controls, 1):
        control = db.query(Control).filter(
            Control.control_group_id == a8_group.id,
            Control.code == code
        ).first()
        
        if not control:
            control = Control(
                name=name,
                description=f"ISO 27001:2022 Control {code}",
                code=code,
                control_group_id=a8_group.id,
                order_index=idx,
                is_active=True
            )
            db.add(control)
            db.flush()
            print(f"[Seed ISO27001] Created control {code} (ID: {control.id})")
        else:
            control.name = name
            control.description = f"ISO 27001:2022 Control {code}"
            control.order_index = idx
            control.is_active = True
            print(f"[Seed ISO27001] Control {code} exists (ID: {control.id})")
    
    db.commit()
    print(f"[Seed ISO27001] ✓ Seeding complete for framework {framework.id}")
    return framework
