"""Explicit multilabel units and undefined-denominator policy; no empirical constants."""
from collections import Counter, defaultdict

LABELS = ('CAPABILITY','POTENTIAL_ACCESS','ACTUAL_ACCESS','POTENTIAL_TRANSMISSION','DISCLOSURE_INCONSISTENCY','UNNECESSARY_PERMISSION')
EVALUATION_VERSION = 'privacy-evaluation-1.0'


def ratios(counts):
    tp, fp, fn, tn = (counts[key] for key in ('TP','FP','FN','TN'))
    divide = lambda a,b: a/b if b else None
    return {**counts, 'precision':divide(tp,tp+fp), 'recall':divide(tp,tp+fn),
            'f1':divide(2*tp,2*tp+fp+fn), 'false_positive_rate':divide(fp,fp+tn), 'false_negative_rate':divide(fn,fn+tp)}


def evaluate_units(units):
    """One unit = version × finding label × data category, for ONE configuration."""
    if len({(row['version_id'],row['finding_category'],row['data_category']) for row in units}) != len(units):
        raise ValueError('Duplicate evaluation unit.')
    groups = defaultdict(lambda: dict.fromkeys(('TP','FP','FN','TN'),0))
    total = dict.fromkeys(('TP','FP','FN','TN'),0)
    rows = []
    for original in units:
        row = dict(original)
        group = groups[(row['finding_category'],row['data_category'])]
        if row['truth'] == 'UNCERTAIN':
            row['classification'] = 'EXCLUDED_UNCERTAIN'
        elif row['truth'] in {'POSITIVE','NEGATIVE'} and type(row['predicted']) is bool:
            truth = row['truth'] == 'POSITIVE'
            outcome = ('TP' if truth else 'FP') if row['predicted'] else ('FN' if truth else 'TN')
            row['classification'] = outcome
            total[outcome] += 1; group[outcome] += 1
        else:
            raise ValueError('Invalid truth decision or prediction.')
        rows.append(row)
    if not sum(total.values()):
        raise ValueError('Ground truth is insufficient: no determinate evaluation units.')
    per_label = [{'finding_category':key[0], 'data_category':key[1], **ratios(value)} for key,value in sorted(groups.items())]
    macro = {}
    for metric in ('precision','recall','f1','false_positive_rate','false_negative_rate'):
        values = [row[metric] for row in per_label if row[metric] is not None]
        macro[metric] = {'value':sum(values)/len(values) if values else None, 'defined_labels':len(values), 'total_labels':len(per_label)}
    return {'units':rows,'micro':ratios(total),'macro':macro,'per_label':per_label,
            'evaluated_units':sum(total.values()),'uncertain_units':len(rows)-sum(total.values()),
            'undefined_policy':'Zero denominators are null/N/A; macro averages only defined label-category metrics and reports coverage.'}


def cohen_kappa(first, second):
    """Unweighted agreement for POSITIVE/NEGATIVE/UNCERTAIN on paired units."""
    if len(first) != len(second):
        raise ValueError('Agreement requires matched units.')
    n = len(first)
    if n < 2:
        return {'kappa':None,'paired_units':n,'reason':'At least two paired units are required.'}
    a,b = Counter(first),Counter(second)
    observed = sum(x==y for x,y in zip(first,second))/n
    expected = sum(a[key]*b[key] for key in set(a)|set(b))/(n*n)
    return {'kappa':(observed-expected)/(1-expected) if expected < 1 else None,'paired_units':n,
            'observed_agreement':observed,'chance_agreement':expected,
            'reason':None if expected < 1 else 'Degenerate marginals: kappa is undefined.'}
