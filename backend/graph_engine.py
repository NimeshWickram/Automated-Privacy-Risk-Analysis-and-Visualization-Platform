"""Deterministic evidence graph projection. No runtime behavior is inferred.

All graph relations are interpreted from retained evidence; OBSERVED identifies
source/entity nodes, not independent verification of their supplied artifacts.
"""
from privacy_ontology import canonical_json, digest, DataCategory

GRAPH_VERSION = 'privacy-graph-1.0'
LAYERS = {'EVIDENCE_SOURCE': 'OBSERVED', 'SDK': 'OBSERVED', 'DOMAIN': 'OBSERVED',
          'DATA_CATEGORY': 'DERIVED', 'RISK_FINDING': 'DERIVED'}
EDGE_TYPES = {
    'INDICATES_CAPABILITY': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),
    'REFERENCES_API_FOR': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),
    'ACCESSES_DATA': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),  # Reserved for a future runtime adapter.
    'ATTRIBUTED_TO': ('EVIDENCE_SOURCE', 'SDK'),
    'CONTACTS': ('EVIDENCE_SOURCE', 'DOMAIN'),
    'HAS_PAYLOAD_CATEGORY': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),
    'TRANSMITTED_TO': ('DATA_CATEGORY', 'DOMAIN'),
    'CLAIMS_COLLECTION': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),
    'DENIES_COLLECTION': ('EVIDENCE_SOURCE', 'DATA_CATEGORY'),
    'SUPPORTED_BY': ('RISK_FINDING', 'EVIDENCE_SOURCE'),
    'CONTRADICTED_BY': ('RISK_FINDING', 'EVIDENCE_SOURCE'),
}


def _project(evidence, findings):
    nodes, edges = {}, {}

    def node(kind, key, label, data):
        identity = kind + ':' + key
        nodes[identity] = {'id': identity, 'type': kind, 'layer': LAYERS[kind], 'label': label, 'data': data}
        return identity

    def edge(start, relation, end, evidence_id, qualification):
        value = {'source': start, 'relation': relation, 'target': end,
                 'evidence_id': evidence_id, 'qualification': qualification}
        identity = digest(value)
        edges[identity] = {'id': identity, **value}

    source_nodes = {}
    for item in sorted(evidence, key=lambda item: item['id']):
        source = node('EVIDENCE_SOURCE', item['id'], item['source'] + ': ' + (item['behavior'] or item['claim']), item)
        source_nodes[item['id']] = source
        category = item['data_category']
        data = node('DATA_CATEGORY', category, category, {'category': category}) if category != 'UNKNOWN' else None
        behavior, attributes = item['behavior'], item['attributes']
        if behavior == 'PERMISSION_REQUESTED' and data:
            edge(source, 'INDICATES_CAPABILITY', data, item['id'], 'permission_only; access and collection unverified')
        elif behavior == 'API_REFERENCE' and data:
            edge(source, 'REFERENCES_API_FOR', data, item['id'], 'static_reference_only; execution and runtime access unverified')
        elif behavior == 'SDK_PRESENT':
            target = node('SDK', digest(attributes['sdk_name']), attributes['sdk_name'], {'name': attributes['sdk_name']})
            edge(source, 'ATTRIBUTED_TO', target, item['id'], 'signature_match_only; SDK access and transmission unverified')
        elif behavior in {'CONTACTS_DOMAIN', 'DATA_TRANSMISSION'}:
            domain = attributes['domain']
            target = node('DOMAIN', digest(domain), domain, {'domain': domain})
            edge(source, 'CONTACTS', target, item['id'], 'retained_network_observation; domain alone does not establish sensitive transmission')
            if behavior == 'DATA_TRANSMISSION' and data:
                edge(source, 'HAS_PAYLOAD_CATEGORY', data, item['id'], 'captured_payload_annotation; category attribution requires review')
                edge(data, 'TRANSMITTED_TO', target, item['id'], 'outbound_payload_annotation; potential transmission, capture authenticity and category require review')
        if item['claim'] in {'POLICY_CLAIMS_COLLECTION', 'DATA_SAFETY_CLAIMS_COLLECTION'}:
            edge(source, 'CLAIMS_COLLECTION', data, item['id'], 'explicit_developer_claim; not observed collection')
        elif item['claim'] in {'POLICY_DENIES_COLLECTION', 'DATA_SAFETY_DENIES_COLLECTION'}:
            edge(source, 'DENIES_COLLECTION', data, item['id'], 'explicit_developer_denial; applicability requires review')
    for finding in sorted(findings, key=lambda item: item['semantic_id']):
        source = node('RISK_FINDING', finding['semantic_id'], finding['category'] + ': ' + finding['data_category'], finding)
        for evidence_id, role in finding['links']:
            edge(source, 'CONTRADICTED_BY' if role == 'CONTRADICTS' else 'SUPPORTED_BY', source_nodes[evidence_id], evidence_id,
                 role + '; ' + ('capability corroboration only' if role == 'CORROBORATES' else 'limited to the recorded finding interpretation'))
    connected = {value[key] for value in edges.values() for key in ('source', 'target')}
    omitted = [{'evidence_id': key, 'reason': 'No justified graph relation; retained in Phase 2 provenance.'}
               for key, value in sorted(source_nodes.items()) if value not in connected]
    return {'graph_version': GRAPH_VERSION, 'nodes': [nodes[key] for key in sorted(connected)],
            'edges': [edges[key] for key in sorted(edges)], 'omitted_evidence': omitted}


def validate_graph(graph, evidence, findings):
    """Central structural and semantic gate, used before persistence and on reads.

The caller supplies independently verified Phase 2 canonical evidence/findings.
Exact projection validation also prevents validly-shaped but unsupported edges.
"""
    if graph.get('graph_version') != GRAPH_VERSION:
        raise ValueError('Unsupported graph version.')
    nodes = {node['id']: node for node in graph['nodes']}
    if len(nodes) != len(graph['nodes']):
        raise ValueError('Duplicate graph node.')
    sources = {item['id']: item for item in evidence}
    for node in nodes.values():
        if node['type'] not in LAYERS or node['layer'] != LAYERS[node['type']]:
            raise ValueError('Invalid graph node type/layer.')
        if node['type'] == 'DATA_CATEGORY' and node['label'] not in {value.value for value in DataCategory if value.value != 'UNKNOWN'}:
            raise ValueError('Invalid graph data category.')
    connected, seen = set(), set()
    for edge in graph['edges']:
        if edge['id'] in seen:
            raise ValueError('Duplicate graph edge.')
        seen.add(edge['id'])
        if edge['source'] not in nodes or edge['target'] not in nodes:
            raise ValueError('Dangling graph edge.')
        pair = (nodes[edge['source']]['type'], nodes[edge['target']]['type'])
        if EDGE_TYPES.get(edge['relation']) != pair:
            raise ValueError('Invalid graph edge endpoints for relation.')
        item = sources.get(edge['evidence_id'])
        if item is None:
            raise ValueError('Graph edge lacks supporting evidence from this run.')
        if edge['relation'] == 'ACCESSES_DATA':
            raise ValueError('ACCESSES_DATA requires a supported runtime adapter; static references cannot establish access.')
        if edge['relation'] == 'TRANSMITTED_TO' and item['behavior'] != 'DATA_TRANSMISSION':
            raise ValueError('Transmission requires an annotated outbound payload, not a domain.')
        if edge['relation'] == 'INDICATES_CAPABILITY' and item['behavior'] != 'PERMISSION_REQUESTED':
            raise ValueError('Capability requires a manifest declaration.')
        if edge['relation'] == 'REFERENCES_API_FOR' and item['behavior'] != 'API_REFERENCE':
            raise ValueError('API reference relation requires static code evidence.')
        connected.update((edge['source'], edge['target']))
    if set(nodes) != connected:
        raise ValueError('Orphan graph nodes are not permitted.')
    if canonical_json(graph) != canonical_json(_project(evidence, findings)):
        raise ValueError('Graph differs from the evidence-backed deterministic projection.')
    return graph


def build_graph(evidence, findings):
    return validate_graph(_project(evidence, findings), evidence, findings)


def explain_graph(graph):
    """Templates only. Co-occurring code/category/network is NOT source-to-sink proof."""
    nodes = {node['id']: node for node in graph['nodes']}
    explanations = []
    for edge in graph['edges']:
        start, end = nodes[edge['source']], nodes[edge['target']]
        text = f"[{start['layer']}] {start['label']} → [RELATION] {edge['relation']} → [{end['layer']}] {end['label']}. {edge['qualification']}."
        explanations.append({'edge_ids': [edge['id']], 'evidence_ids': [edge['evidence_id']], 'text': text})
        if edge['relation'] == 'TRANSMITTED_TO':
            incoming = next(value for value in graph['edges'] if value['relation'] == 'HAS_PAYLOAD_CATEGORY'
                            and value['evidence_id'] == edge['evidence_id'] and value['target'] == edge['source'])
            observed = nodes[incoming['source']]
            explanations.append({'edge_ids': [incoming['id'], edge['id']], 'evidence_ids': [edge['evidence_id']],
                'text': f"[OBSERVED] {observed['label']} → [RELATION] HAS_PAYLOAD_CATEGORY → [DERIVED] {start['label']} → [RELATION] TRANSMITTED_TO → [OBSERVED] {end['label']}. Potential transmission based on this payload annotation; not a proven code-to-network data flow."})
    return explanations
