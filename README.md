# Daily Finance Briefing

GitHub Actions를 이용해 **매일 오전 10시(KST)** 전일 시장 요약 HTML을 자동 생성/저장하는 예시입니다.

## 동작 방식
- 워크플로우: `.github/workflows/daily-market-summary.yml`
- 스케줄: 평일 UTC 01:00 (KST 10:00)
- 실행 스크립트: `scripts/generate_daily_market_summary.py`
- 결과 파일: `reports/daily/market_summary_YYYY-MM-DD.html`

## 로컬 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_daily_market_summary.py
```

## 확장 포인트
- 거래일 캘린더(공휴일) 정교화
- 심볼/표시명 매핑 테이블 분리(JSON/YAML)
- 실패 시 Slack/이메일 알림
