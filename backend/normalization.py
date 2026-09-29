"""Strict normalization of six source families before any fusion inference.

Claim/category annotations are inputs with explicit provenance, not ground truth.
The normalizer checks their evidence anchors; it cannot certify analyst honesty.
"""
from datetime import datetime
import ipaddress
import json
import re
from xml.etree import ElementTree

from privacy_ontology import Source, DataCategory, Behavior, Claim, PERMISSIONS, API_CATEGORIES, digest


def required_text(record, key):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must contain source evidence.")
    return value


def domain_name(value):
    value = value.strip().lower().rstrip('.')
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        if not re.fullmatch(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", value) or '..' in value:
            raise ValueError("Expected a hostname or IP address, not a URL.")
        return value


def json_pointer(document, pointer):
    if not pointer.startswith('/'):
        raise ValueError("Payload pointer must identify a specific field.")
    value = document
    try:
        for token in pointer[1:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            value = value[int(token)] if isinstance(value, list) else value[token]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("Payload pointer does not resolve in captured payload.") from exc
    if value is None or value == '' or value == [] or value == {} or isinstance(value, bool):
        raise ValueError("Payload field must contain an observed value.")
    return value


def normalize(record):
    if not isinstance(record, dict):
        raise ValueError('Each evidence record must be an object.')
    source = Source(record.get("source")).value
    raw = required_text(record, "raw_evidence")
    reference = required_text(record, "file_reference")
    description = required_text(record, "description")
    kind = required_text(record, "kind")
    category, behavior, claim, attributes = "UNKNOWN", None, None, {}
    if source == "MANIFEST":
        if kind != "permission":
            raise ValueError("Manifest normalization accepts permission declarations only; SDK signatures use SDK source.")
        # The legacy extractor serializes an XML declaration without namespace binding.
        try:
            element = ElementTree.fromstring(raw.replace('android:name=', 'name='))
            permission = element.attrib.get('name', '')
            if element.tag not in {"uses-permission", "uses-permission-sdk-23"} or not permission:
                raise ValueError("Not a permission declaration.")
        except ElementTree.ParseError as exc:
            raise ValueError("Malformed manifest declaration.") from exc
        prefix, _, short = permission.rpartition('.')
        if prefix == "android.permission" and short != "AD_ID":
            category = PERMISSIONS.get(short, "UNKNOWN")
        elif permission == "com.google.android.gms.permission.AD_ID":
            category = "ADVERTISING_IDENTIFIER"
        behavior = Behavior.PERMISSION_REQUESTED.value
        attributes = {"permission": permission, "necessity": "unknown"}
        if record.get("necessity") in {"excessive", "unnecessary"}:
            attributes.update(necessity=record["necessity"], necessity_basis=required_text(record, "necessity_basis"),
                              necessity_analyzer=required_text(record, "necessity_analyzer"))
    elif source == "CODE":
        if kind != "api_reference":
            raise ValueError("Static code normalization cannot assert runtime API_ACCESS.")
        indicator = required_text(record, "indicator")
        if indicator.lower() not in raw.lower():
            raise ValueError("API indicator is absent from raw evidence.")
        category = API_CATEGORIES.get(indicator, "UNKNOWN")
        behavior, attributes = Behavior.API_REFERENCE.value, {"indicator": indicator, "execution": "not_established"}
    elif source == "SDK":
        if kind != "sdk_presence":
            raise ValueError("SDK presence cannot assert THIRD_PARTY_ACCESS.")
        signature = required_text(record, "signature")
        if signature not in raw:
            raise ValueError("SDK signature is absent from raw evidence.")
        behavior = Behavior.SDK_PRESENT.value
        attributes = {"sdk_name": required_text(record, "sdk_name"), "signature": signature}
    elif source == "NETWORK":
        if kind not in {"domain_observation", "payload_observation"}:
            raise ValueError("Unknown network observation kind.")
        try:
            captured = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Network evidence must be a structured captured request.") from exc
        if not isinstance(captured, dict):
            raise ValueError("Network evidence must be an object.")
        attributes = {"domain": domain_name(required_text(captured, "domain"))}
        behavior = Behavior.CONTACTS_DOMAIN.value
        if kind == "payload_observation":
            if captured.get("direction") != "outbound":
                raise ValueError("Transmission requires an outbound observation.")
            category = DataCategory(record.get("data_category")).value
            if category == "UNKNOWN":
                raise ValueError("Payload category attribution must be explicit.")
            pointer = required_text(record, "payload_pointer")
            value = json_pointer(captured.get("payload"), pointer)
            capture_hash = required_text(record, "capture_sha256")
            if not re.fullmatch(r"[0-9a-f]{64}", capture_hash):
                raise ValueError("Capture SHA-256 is required.")
            captured_at = datetime.fromisoformat(required_text(record, "captured_at").replace('Z', '+00:00'))
            if captured_at.tzinfo is None:
                raise ValueError("Capture timestamp must include timezone.")
            attributes.update(payload_pointer=pointer, observed_value=value, category_basis=required_text(record, "category_basis"),
                              annotated_by=required_text(record, "annotated_by"), capture_sha256=capture_hash,
                              captured_at=captured_at.isoformat(), scope="collection")
            behavior = Behavior.DATA_TRANSMISSION.value
    else:
        if kind == "document":
            claim = Claim.UNKNOWN.value
        elif kind == "claim":
            category = DataCategory(record.get("data_category")).value
            if category == "UNKNOWN" or record.get("scope") != "collection":
                raise ValueError("Claims need an explicit category and collection scope.")
            state = record.get("claim_state")
            if state not in {"collects", "denies", "not_mentioned", "unknown"}:
                raise ValueError("Unsupported claim state.")
            if state in {"collects", "denies"}:
                quote = required_text(record, "quote")
                if quote not in raw:
                    raise ValueError("Claim quote must occur exactly in the retained document.")
                # LLM-only annotations are not accepted as validated claims.
                if record.get("annotation_method") != "manual_evidence_review":
                    raise ValueError("An evidence-backed manual claim annotation is required.")
                claim = source + ("_CLAIMS_COLLECTION" if state == "collects" else "_DENIES_COLLECTION")
                attributes = {"quote": quote, "scope": "collection", "annotated_by": required_text(record, "annotated_by"),
                              "annotation_method": record["annotation_method"]}
            else:
                claim = Claim.NOT_MENTIONED.value if state == "not_mentioned" else Claim.UNKNOWN.value
        else:
            raise ValueError("Unsupported disclosure evidence kind.")
    value = {"source": source, "data_category": category, "behavior": behavior, "claim": claim,
             "raw_evidence": raw, "file_reference": reference, "description": description, "attributes": attributes}
    return {"id": digest(value), **value}


def normalize_sources(records, enabled_sources):
    """Filter before normalization; excluded evidence cannot affect a configuration."""
    unique = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Each evidence record must be an object.')
        source = Source(record.get("source")).value
        if source in enabled_sources:
            item = normalize(record)
            unique[item["id"]] = item
    return [unique[key] for key in sorted(unique)]
