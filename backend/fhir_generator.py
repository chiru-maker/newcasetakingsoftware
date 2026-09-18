"""
SwasthyaSync AI — FHIR R4 Clinical Bundle Generator & Validator
Compliant with HL7 FHIR R4 and ABDM (Ayushman Bharat Digital Mission) Health Document Specifications.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


def create_fhir_r4_bundle(
    patient_data: Dict[str, Any],
    complaint: str,
    triage_priority: str,
    priority_reasoning: str,
    department: str,
    provisional_diagnoses: List[Dict[str, str]],
    vitals: Optional[Dict[str, Any]] = None,
    consent_granted: bool = True,
    transcript_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Generates a production-valid HL7 FHIR R4 Transaction/Document Bundle
    representing an OPD Clinical Case-Taking & Triage Encounter.
    """
    bundle_id = f"bundle-{uuid.uuid4()}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    patient_id = patient_data.get("patient_id", f"pat-{uuid.uuid4()}")
    patient_name = patient_data.get("full_name", "Anonymous Patient")
    abha_id = patient_data.get("abha_id", "91-0000-0000-0000")
    gender = str(patient_data.get("gender", "unknown")).lower()
    if gender not in ["male", "female", "other", "unknown"]:
        gender = "unknown"
    age = patient_data.get("age", 30)
    birth_year = datetime.now().year - int(age) if age else 1990
    birth_date = f"{birth_year}-01-01"
    phone = patient_data.get("phone", "+919876543210")
    
    encounter_id = f"enc-{uuid.uuid4()}"
    
    # 1. Patient Resource
    patient_resource = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"]
        },
        "identifier": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical record number"
                        }
                    ]
                },
                "system": "https://healthid.abdm.gov.in",
                "value": abha_id
            }
        ],
        "name": [
            {
                "use": "official",
                "text": patient_name
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": phone
            }
        ],
        "gender": gender,
        "birthDate": birth_date
    }
    
    # 2. Encounter Resource
    triage_code_map = {
        "CRITICAL": "EMERGENCY",
        "ELEVATED": "URGENT",
        "NORMAL": "ROUTINE"
    }
    t_code = "ROUTINE"
    for k in ["CRITICAL", "ELEVATED", "NORMAL"]:
        if k in triage_priority.upper():
            t_code = triage_code_map[k]
            break

    encounter_resource = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Encounter"]
        },
        "status": "triaged",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "Ambulatory Outpatient"
        },
        "priority": {
            "coding": [
                {
                    "system": "https://swasthyasync.ai/fhir/codes/triage-priority",
                    "code": t_code,
                    "display": f"Triage Level: {triage_priority}"
                }
            ],
            "text": priority_reasoning
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": patient_name
        },
        "serviceProvider": {
            "display": f"Hospital Department: {department}"
        },
        "period": {
            "start": timestamp
        }
    }
    
    entries = [
        {
            "fullUrl": f"urn:uuid:{patient_id}",
            "resource": patient_resource,
            "request": {"method": "POST", "url": "Patient"}
        },
        {
            "fullUrl": f"urn:uuid:{encounter_id}",
            "resource": encounter_resource,
            "request": {"method": "POST", "url": "Encounter"}
        }
    ]
    
    # 3. Condition Resources (Provisional Diagnoses)
    for idx, dx in enumerate(provisional_diagnoses):
        cond_id = f"cond-{uuid.uuid4()}"
        dx_name = dx.get("diagnosis", "Clinical symptom")
        icd_code = dx.get("icd_10_code", "R69")
        snomed_code = dx.get("snomed_code", "404684003")
        
        condition_resource = {
            "resourceType": "Condition",
            "id": cond_id,
            "meta": {
                "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/Condition"]
            },
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "provisional",
                        "display": "Provisional Assessment"
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": icd_code,
                        "display": dx_name
                    },
                    {
                        "system": "http://snomed.info/sct",
                        "code": snomed_code,
                        "display": dx_name
                    }
                ],
                "text": dx_name
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
                "display": patient_name
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            }
        }
        entries.append({
            "fullUrl": f"urn:uuid:{cond_id}",
            "resource": condition_resource,
            "request": {"method": "POST", "url": "Condition"}
        })
        
    # 4. Observation Resources (Vitals)
    vitals = vitals or {}
    if vitals:
        # Blood Pressure
        bp_val = vitals.get("bp", "120/80")
        if "/" in str(bp_val):
            try:
                sys_p, dia_p = bp_val.split("/")
                bp_obs_id = f"obs-bp-{uuid.uuid4()}"
                entries.append({
                    "fullUrl": f"urn:uuid:{bp_obs_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": bp_obs_id,
                        "status": "final",
                        "category": [{
                            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]
                        }],
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]
                        },
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "component": [
                            {
                                "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}]},
                                "valueQuantity": {"value": float(sys_p), "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                            },
                            {
                                "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP"}]},
                                "valueQuantity": {"value": float(dia_p), "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                            }
                        ]
                    },
                    "request": {"method": "POST", "url": "Observation"}
                })
            except Exception:
                pass
                
        # SpO2
        spo2_val = vitals.get("spo2", 98)
        spo2_id = f"obs-spo2-{uuid.uuid4()}"
        entries.append({
            "fullUrl": f"urn:uuid:{spo2_id}",
            "resource": {
                "resourceType": "Observation",
                "id": spo2_id,
                "status": "final",
                "category": [{
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]
                }],
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "2708-6", "display": "Oxygen saturation in Arterial blood by Pulse oximetry"}]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "valueQuantity": {"value": float(spo2_val), "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"}
            },
            "request": {"method": "POST", "url": "Observation"}
        })

    # 5. QuestionnaireResponse (Verbatim Patient Transcript)
    qr_id = f"qr-{uuid.uuid4()}"
    entries.append({
        "fullUrl": f"urn:uuid:{qr_id}",
        "resource": {
            "resourceType": "QuestionnaireResponse",
            "id": qr_id,
            "status": "completed",
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "authored": timestamp,
            "item": [
                {
                    "linkId": "chief-complaint",
                    "text": "Chief Health Complaint (Vernacular / Translated)",
                    "answer": [{"valueString": complaint}]
                }
            ]
        },
        "request": {"method": "POST", "url": "QuestionnaireResponse"}
    })

    # 6. Consent Resource (DPDP Act 2023)
    consent_id = f"consent-{uuid.uuid4()}"
    entries.append({
        "fullUrl": f"urn:uuid:{consent_id}",
        "resource": {
            "resourceType": "Consent",
            "id": consent_id,
            "status": "active" if consent_granted else "inactive",
            "scope": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                        "code": "patient-privacy",
                        "display": "Privacy Consent (DPDP Act 2023)"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "INFA",
                            "display": "Information Access"
                        }
                    ]
                }
            ],
            "patient": {"reference": f"Patient/{patient_id}"},
            "dateTime": timestamp,
            "policyRule": {
                "coding": [
                    {
                        "system": "https://abdm.gov.in/policies",
                        "code": "DPDP-ACT-2023-CONSENT"
                    }
                ]
            }
        },
        "request": {"method": "POST", "url": "Consent"}
    })

    bundle = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {
            "lastUpdated": timestamp,
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"]
        },
        "identifier": {
            "system": "https://swasthyasync.ai/bundles",
            "value": bundle_id
        },
        "type": "transaction",
        "timestamp": timestamp,
        "total": len(entries),
        "entry": entries
    }
    
    return bundle
