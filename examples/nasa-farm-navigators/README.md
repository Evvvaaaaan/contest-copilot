# NASA Farm Navigators 회고 예제

2025 NASA Space Apps의 실제 주제와 공개 수상 기록을 조사하고, 작은 프로토타입을 검증하는 예제입니다. **종료된 대회를 이용한 AI 작성 예시**이며 사용자님의 실제 아이디어, 참가 기록, 승인 또는 NASA의 보증을 뜻하지 않습니다. 문서·코드·설정 데이터와 게임 규칙은 AI가 작성했습니다. 실제 농업 관측 데이터는 포함하지 않습니다.

## 확인한 근거

- [공식 과제](https://www.spaceappschallenge.org/2025/challenges/nasa-farm-navigators-using-nasa-data-exploration-in-agriculture/)의 Summary·Objectives는 NASA 공개 데이터를 활용한 농업 교육 게임을 요구합니다. Resources에는 농업·물 관리 자료 안내와 Earthdata Search 등이 있습니다. 현재 페이지에 2025년 대회 종료가 명시돼 있습니다.
- [공식 심사 지침 PDF](https://spaceapps-v2-staging.s3.amazonaws.com/media/documents/Final_Space_Apps_2025_Judging_Guidelines_for_web.pdf) 1쪽은 최소 요건을 먼저 확인하고 종합적으로 1~5점을 평가하도록 합니다. 2~3쪽은 영향, 창의성, 타당성, 주제 적합성, 발표를 설명합니다. 이 문서에서 항목별 가중치는 확인되지 않았습니다.
- [공식 시상 안내](https://www.spaceappschallenge.org/2025/awards/)는 10개 글로벌 상을 설명합니다. 상의 이름을 심사 배점으로 취급하지 않습니다.
- [NASA의 2025년 수상 발표](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/)는 이 과제의 Zumorroda-X가 Art & Technology 상을 받았다고 밝힙니다. 여러 환경 문제를 다루는 농업 미니 게임으로 소개하지만, 비공개 점수나 수상의 인과적 이유는 알 수 없습니다.

조사일은 2026-10-12입니다. `research.json`에 출처 위치, 확인 범위, 일부 원자료 SHA-256, 판단과 미확인 사항을 기록했습니다. 원문 전체를 복제하지 않았습니다. 국내외 경쟁작 전체, 수상작의 실제 코드·학습 효과, 모든 참가 자격까지 조사한 예제는 아닙니다.

## 실행

저장소 루트에서 실행합니다. Python 3.9 이상이면 외부 패키지나 API 키가 필요하지 않습니다.

```bash
cd examples/nasa-farm-navigators
python3 catalog.py irrigation
python3 farm_game.py
```

게임은 작물 유형을 고르고 두 차례 관개 또는 절약 행동을 선택합니다. 물·예산과 설명이 바뀌며 마지막에 결과를 표시합니다. 터미널의 질문 없이 재현하려면 다음처럼 실행합니다.

```bash
python3 farm_game.py --crop drought_tolerant --actions irrigate conserve
python3 -m unittest discover -s . -p 'test_*.py' -v
```

작물은 `--crop`으로 선택하며 기본값은 `drought_tolerant`입니다. 시작 자원은 물 4, 예산 3 게임 단위입니다. `irrigate`는 내건성 작물에서 물 1, 물 요구량이 큰 `water_demanding`에서 물 2를 사용하며, 두 작물 모두 예산 1을 사용합니다. `conserve`는 자원을 유지합니다. 첫 턴의 합성 날씨는 `dry`, 둘째 턴은 `wet`이며 각각 관개와 절약을 선택하면 학습 점수 1점을 받습니다. 각 행동의 설명은 `history[].explanation`, 종료 설명은 `summary`에 표시됩니다.

건조·습윤 날씨, 자원 단위와 점수는 모두 교육용으로 만든 합성 규칙입니다. 실제 수확량이나 물 절약 효과를 추정하지 않습니다. 카탈로그는 공식 과제에 소개된 자료의 메타데이터만 검색합니다. 연결된 데이터 제품 자체의 기능·최신성·접근 가능성까지 확인했다는 뜻은 아닙니다.

## 앱과 반복 검증에서 사용

`contract.json`은 이 프로토타입의 실행 기준입니다. 실제 참가에 사용하려면 사용자의 의도·기준을 별도로 합의해야 합니다. 이 예제 기준을 통과해도 공식 제출 자격과 모든 과제 요구가 충족되는 것은 아닙니다. `research.json`의 `official_submission_ready`는 false로 유지합니다.

`simulation-plan.json`은 2명의 가상 참여자가 2라운드 동안 사용성과 자료 출처를 논의하는 구성입니다. 저장소의 `Simulation` 스키마와 호환됩니다. 행동은 실행 중인 AI가 생성하며, 이 파일에는 성공 결과나 가상의 사용자 승인이 미리 들어 있지 않습니다. 두 명의 가상 반응을 실제 사용자 만족도나 채택률로 해석할 수 없습니다.

```bash
python3 ../../contest-copilot/scripts/simulate.py --workspace /tmp/farm-example create --config simulation-plan.json
```

출력된 실행 ID로 참여자 관찰·행동을 진행합니다. 예제 테스트는 게임·검색·출처 연결을 검증하며, 별도 AI 개발·검토 실행의 성공을 대신하지 않습니다.

## 공식 제출까지 남은 부분

실제 NASA 관측 데이터의 의미 있는 통합, 해상도·관측 깊이·불확실성 검토, 학습 효과와 과학적 타당성 검증이 남아 있습니다. 공식 심사 지침의 언어·시연 분량·공개 링크·AI 사용 표시와 참가 및 제출 조건도 별도로 확인해야 합니다. 이 프로토타입의 간단한 점수는 공식 심사 점수와 관련이 없습니다.

실제 Codex 및 브라우저 통합 검증 기록은 [validation.md](validation.md)를 참고하세요.
