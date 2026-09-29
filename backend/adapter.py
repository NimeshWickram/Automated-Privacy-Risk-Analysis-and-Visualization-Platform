"""Compatibility adapter. Legacy fused descriptions/confidence are never inputs to rules."""


def adapt_legacy_records(records):
    result = []
    for record in records:
        source = record['source_type']
        item = {key: record.get(key, '') for key in ('raw_evidence', 'file_reference', 'description')}
        if source == 'manifest' and record['evidence_category'] == 'sdk_presence':
            item.update(source='SDK', kind='sdk_presence', sdk_name=record['data_type'], signature=record['raw_evidence'])
        elif source == 'manifest':
            item.update(source='MANIFEST', kind='permission')
            # Legacy necessity explanations depend on SDK attribution and an
            # assumed app category. Do not leak these into manifest-only runs.
        elif source == 'decompiled_code':
            # Scanner provides a structured indicator; do not parse English descriptions.
            item.update(source='CODE', kind='api_reference', indicator=record.get('matched_indicator', ''))
        elif source == 'privacy_policy' and record['evidence_category'] == 'policy_document':
            item.update(source='POLICY', kind='document')
        else:
            raise ValueError('Legacy claim/network heuristics cannot be promoted to canonical evidence.')
        result.append(item)
    return result
