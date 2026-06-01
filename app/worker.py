import asyncio
import httpx
from random import uniform
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.models import Request as RequestModel
from app.models import AttemptHistory
from app.database import SessionLocal as AsyncSessionLocal


def _now():
    return datetime.now(timezone.utc)

def _calc_backoff(backoff_ms: int, attempt_count: int):
    wait = backoff_ms * (2 ** attempt_count)
    jitter = uniform(0.8, 1.2)
    return int(wait * jitter)

def _schedule_retry(request: RequestModel):
    delay = _calc_backoff(request.backoffMs, request.attemptCount - 1)
    request.nextRetryAt = _now() + timedelta(milliseconds=delay)
    request.status = "retrying"

def _fail(request: RequestModel):
    request.status = "failed"
    request.nextRetryAt = None

def _complete(request: RequestModel) -> None:
    request.status = "completed"
    request.nextRetryAt = None


async def _make_http_call(request: RequestModel, client: httpx.AsyncClient):
    try:
        headers = {"Content-Type": "application/json"} if request.body else {}
        response = await client.request(
            method=request.method,
            url=request.url,
            content=request.body.encode() if request.body else None,
            headers=headers,
        )
        return response.status_code, response.text
    except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
        return None, str(e)


async def record_attempt(request: RequestModel, db, status: str):
    attempt = AttemptHistory(
        request_id=request.id,
        attemptNumber=request.attemptCount,
        executedAt=_now(),
        status=status,
        error=request.lastError,
        result=request.result,
    )
    db.add(attempt)


async def process_request(request: RequestModel, db, client: httpx.AsyncClient):
    status_code, body_or_error = await _make_http_call(request, client)

    if status_code is not None and 200 <= status_code < 300:
        request.attemptCount += 1
        request.result = body_or_error
        request.lastError = None
        _complete(request)

    elif status_code is not None and 400 <= status_code < 500:
        request.attemptCount += 1
        request.lastError = f"HTTP {status_code}: {body_or_error[:500]}"
        _fail(request)

    else:
        request.attemptCount += 1

        if status_code is not None:
            request.lastError = f"HTTP {status_code}: {body_or_error[:500]}"
        else:
            request.lastError = body_or_error

        if request.attemptCount >= request.maxRetries:
            _fail(request)
        else:
            _schedule_retry(request)

    await record_attempt(request, db, request.status)


async def process_requests():
    async with AsyncSessionLocal() as db:
        now = _now()
        stmt = (
            select(RequestModel)
            .where(
                RequestModel.status.in_(["pending", "retrying"]),
                (RequestModel.nextRetryAt == None) | (RequestModel.nextRetryAt <= now),
            )
            .limit(10)
        )
        result = await db.execute(stmt)
        requests = list(result.scalars().all())

        async with httpx.AsyncClient(timeout=30) as client:
            for req in requests:
                await process_request(req, db, client)

        await db.commit()


async def run_worker_loop():
    while True:
        try:
            await process_requests()
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[worker] tick failed: {e}")