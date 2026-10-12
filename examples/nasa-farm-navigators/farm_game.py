#!/usr/bin/env python3
"""AI-authored two-turn teaching sketch with synthetic, non-agronomic game units."""
import argparse
from copy import deepcopy
import json
from catalog import search

CROPS = {'drought_tolerant': 1, 'water_demanding': 2}
WEATHER = ['dry', 'wet']
LIMITATION = 'AI-generated toy rules and synthetic weather; no NASA observations or validated crop yields. Not farm advice.'


def start(crop):
    if crop not in CROPS:
        raise ValueError('Choose drought_tolerant or water_demanding.')
    return {'crop': crop, 'turn': 0, 'water_units': 4, 'budget_units': 3,
            'learning_points': 0, 'history': [], 'status': 'playing',
            'disclosure': LIMITATION}


def play(state, action):
    if state['status'] != 'playing':
        raise ValueError('The two-turn game is complete.')
    if action not in ('irrigate', 'conserve'):
        raise ValueError('Choose irrigate or conserve.')
    needed = CROPS[state['crop']]
    if action == 'irrigate' and (state['water_units'] < needed or state['budget_units'] < 1):
        raise ValueError('Insufficient game resources.')
    result = deepcopy(state)
    weather = WEATHER[state['turn']]
    if action == 'irrigate':
        result['water_units'] -= needed
        result['budget_units'] -= 1
    matched = (weather == 'dry' and action == 'irrigate') or (weather == 'wet' and action == 'conserve')
    result['learning_points'] += int(matched)
    explanation = (
        f"합성 날씨 {weather}에서는 {'irrigate' if weather == 'dry' else 'conserve'}를 선택하면 "
        f"학습 점수 1점을 받는 교육용 규칙입니다. 선택: {action}, 획득 점수: {int(matched)}. "
        f"작물 {state['crop']}의 관개 비용은 물 {needed}, 예산 1입니다. "
        f"이번 행동으로 물 {state['water_units']} → {result['water_units']}, "
        f"예산 {state['budget_units']} → {result['budget_units']} 게임 단위가 되었습니다."
    )
    result['history'].append({'turn': state['turn'] + 1, 'synthetic_weather': weather,
                              'action': action, 'matched_toy_rule': matched,
                              'explanation': explanation,
                              'lesson': 'Before applying this simplified rule to real data, inspect soil depth, spatial resolution and local crop needs.',
                              'resource': search('irrigation')['results'][0]})
    result['turn'] += 1
    result['status'] = 'complete' if result['turn'] == len(WEATHER) else 'playing'
    if result['status'] == 'complete':
        result['summary'] = (
            f"2턴 종료: 학습 점수 {result['learning_points']}/2, "
            f"남은 물 {result['water_units']}, 예산 {result['budget_units']} 게임 단위. "
            "합성 규칙의 결과이며 실제 농업 측정값이나 수확량 예측이 아닙니다. "
            "NASA 자료는 오프라인 출처 메타데이터만 사용하며 공식 제출 준비를 뜻하지 않습니다."
        )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crop', choices=tuple(CROPS), default='drought_tolerant')
    parser.add_argument('--actions', nargs=2, choices=('irrigate', 'conserve'), help='Omit for interactive play.')
    args = parser.parse_args()
    current = start(args.crop)
    if not args.actions:
        print(LIMITATION)
    while current['status'] == 'playing':
        index = current['turn']
        action = args.actions[index] if args.actions else input(f"Turn {index + 1}, synthetic weather={WEATHER[index]}, water={current['water_units']}, budget={current['budget_units']}. irrigate/conserve: ").strip()
        try:
            current = play(current, action)
        except ValueError as error:
            if args.actions:
                parser.error(str(error))
            print(error)
    print(json.dumps(current, indent=2, ensure_ascii=False))
