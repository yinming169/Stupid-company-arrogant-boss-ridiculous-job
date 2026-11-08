"""铜排分段计算：输入各真实或明确假设的下料段，输出可追溯净长和净重。"""
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from common import read_json, write_json, setup_stdout


def calculate(doc):
    segments = doc.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('必须提供非空 segments；未知段不能按零计入')
    if doc.get('voltage_class') != '低压':
        raise ValueError('本计算仅适用于低压，需明确 voltage_class=低压')
    seen, result, totals = set(), [], defaultdict(lambda: [Decimal(0), Decimal(0)])
    for s in segments:
        ident = str(s.get('id', '')).strip()
        if not ident or ident in seen:
            raise ValueError('每段必须提供唯一 id')
        seen.add(ident)
        if s.get('status') not in ('已确认', '估算') or not str(s.get('basis', '')).strip():
            raise ValueError(f'{ident}: 必须填写状态及依据')
        if s.get('material') != '铜' or not s.get('category') or not s.get('cabinet') or not s.get('phase'):
            raise ValueError(f'{ident}: 必须填写铜材、用途、柜号或公共项及相别')
        def number(key):
            try: v = Decimal(str(s[key]))
            except (KeyError, InvalidOperation): raise ValueError(f'{ident}: 缺少有效 {key}')
            if not v.is_finite() or v <= 0: raise ValueError(f'{ident}: {key} 必须大于零')
            return v
        width, thick, length, count, strands = [number(k) for k in ('width_mm','thickness_mm','length_m','pieces','parallel')]
        if count != count.to_integral() or strands != strands.to_integral(): raise ValueError(f'{ident}: 件数和并联片数必须为整数')
        net = length * count * strands
        weight = width * thick * net * Decimal('0.00896')
        key = (str(width), str(thick))
        totals[key][0] += net; totals[key][1] += weight
        result.append({**s, 'net_length_m': float(net), 'weight_kg': float(weight)})
    return {'voltage_class':'低压', 'segments':result, 'by_spec':[{'spec':f'TMY-{w}×{t}', 'net_length_m':float(v[0]), 'weight_kg':float(v[1])} for (w,t),v in totals.items()], 'total_weight_kg':float(sum((v[1] for v in totals.values()),Decimal(0))), 'complete': doc.get('complete') is True, 'warning':'计算仅覆盖已输入段；未输入段、损耗及排样不含在内，选型和温升须另核。'}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('input'); p.add_argument('--out',required=True); a=p.parse_args()
    try: write_json(a.out,calculate(read_json(a.input)))
    except ValueError as e: raise SystemExit(str(e))
if __name__ == '__main__':
    setup_stdout(); main()
