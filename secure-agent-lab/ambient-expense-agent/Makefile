.PHONY: install playground ambient stop stop-ambient stop-playground

install:
	uv sync

playground:
	uv run adk web expense_agent --host 127.0.0.1 --port 8000 --reload_agents

ambient:
	uv run uvicorn app.main:app --host 127.0.0.1 --port 8080

stop: stop-ambient stop-playground

stop-ambient:
	powershell -Command 'Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $$_ -Force }'

stop-playground:
	powershell -Command 'Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $$_ -Force }'
