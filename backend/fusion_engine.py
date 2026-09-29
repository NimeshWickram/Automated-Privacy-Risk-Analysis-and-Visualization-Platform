"""Pure deterministic rules over normalized evidence. Scores are not probabilities."""
from privacy_ontology import Finding, RULE_VERSION, configuration, digest


def fuse(evidence, config):
    if config != configuration(config.get("preset")):
        raise ValueError("Unrecognized or modified analysis configuration.")
    for item in evidence:
        if item["source"] not in config["enabled_sources"] or digest({k: v for k, v in item.items() if k != 'id'}) != item['id']:
            raise ValueError("Fusion input must be intact normalized evidence from enabled sources.")
    evidence = sorted({item['id']: item for item in evidence}.values(), key=lambda item: item['id'])
    findings = []
    weights = config['base_strength_points']

    def emit(category, data, interpretation, rule, supports, corroborates=(), contradicts=(), domain=None, strength=None, severity='moderate'):
        links = [(item['id'], 'SUPPORTS') for item in supports]
        links += [(item['id'], 'CORROBORATES') for item in corroborates]
        links += [(item['id'], 'CONTRADICTS') for item in contradicts]
        value = {'category': category.value, 'data_category': data, 'interpretation': interpretation,
                 'rule_id': RULE_VERSION + ':' + rule, 'domain': domain, 'severity': severity,
                 'evidence_strength_score': strength / 100, 'links': sorted(set(links))}
        findings.append({'semantic_id': digest(value), **value})

    categories = sorted({item['data_category'] for item in evidence} - {'UNKNOWN'})
    for data in categories:
        items = [item for item in evidence if item['data_category'] == data]
        manifests = [item for item in items if item['behavior'] == 'PERMISSION_REQUESTED']
        code = [item for item in items if item['behavior'] == 'API_REFERENCE']
        payloads = [item for item in items if item['behavior'] == 'DATA_TRANSMISSION']
        unnecessary = [item for item in manifests if item['attributes']['necessity'] in {'excessive', 'unnecessary'}]
        if unnecessary:
            emit(Finding.UNNECESSARY_PERMISSION, data, 'A declared permission is flagged by the recorded context heuristic as potentially unnecessary. This does not establish collection or runtime use.', 'permission-context', unnecessary, strength=weights['MANIFEST'])
        elif manifests and not code:
            emit(Finding.CAPABILITY, data, 'Manifest evidence indicates capability only. Necessity, access, collection and transmission are not established.', 'permission-capability', manifests, strength=weights['MANIFEST'], severity='low')
        if code:
            emit(Finding.ACCESS, data, 'Static API references suggest potential sensitive data access. Execution and runtime collection are not established. Manifest corroboration concerns capability only.', 'static-potential-access', code, manifests,
                 strength=min(100, weights['CODE'] + (config['capability_corroboration_points'] if manifests else 0)))
        for domain in sorted({item['attributes']['domain'] for item in payloads}):
            matches = [item for item in payloads if item['attributes']['domain'] == domain]
            emit(Finding.TRANSMISSION, data, 'An outbound captured payload contains a field annotated as this data category. The retained annotation and payload support potential transmission to this domain; category attribution requires review.', 'payload-transmission', matches, domain=domain, strength=weights['NETWORK'], severity='high')
        denials = [item for item in items if item['claim'] in {'POLICY_DENIES_COLLECTION', 'DATA_SAFETY_DENIES_COLLECTION'}]
        positives = [item for item in items if item['claim'] in {'POLICY_CLAIMS_COLLECTION', 'DATA_SAFETY_CLAIMS_COLLECTION'}]
        # Permission/API references and SDK presence do NOT establish collection.
        if denials and payloads:
            emit(Finding.DISCLOSURE, data, 'A captured outbound payload attributed to this category potentially conflicts with an explicit collection denial. Review category attribution, policy applicability, exemptions and collection scope; no legal violation is concluded.', 'payload-vs-denial', payloads, contradicts=denials,
                 strength=min(weights['NETWORK'], min(weights[item['source']] for item in denials)), severity='high')
        if denials and positives:
            emit(Finding.DISCLOSURE, data, 'Explicit retained collection claims disagree for this category. This is a potential disclosure inconsistency, not proof of collection or a legal conclusion.', 'claim-vs-claim', positives, contradicts=denials,
                 strength=min(weights[item['source']] for item in denials + positives))
    for sdk_name in sorted({item['attributes']['sdk_name'] for item in evidence if item['behavior'] == 'SDK_PRESENT'}):
        matches = [item for item in evidence if item['behavior'] == 'SDK_PRESENT' and item['attributes']['sdk_name'] == sdk_name]
        emit(Finding.SDK_PRESENCE, 'UNKNOWN', f'SDK signature present: {sdk_name}. Access and transmission have not been observed.', 'sdk-presence', matches, strength=weights['SDK'], severity='low')
    return sorted(findings, key=lambda item: item['semantic_id'])
