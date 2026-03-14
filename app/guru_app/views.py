import os
import sys
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# ── Ensure project root is on sys.path so config/api/utils are importable ─────
ROOT = Path(__file__).resolve().parent.parent.parent.parent  # project root
for p in [str(ROOT), str(ROOT / 'app')]:
    if p not in sys.path:
        sys.path.insert(0, p)

from config import FILE_PATHS, TRANSCRIPTS, MAX_CONTEXT_TOKENS
from api.generate_response import generate_response
from api.retrieve_context import retrieve_transcripts
from utils.token import count_tokens, trim_to_token_limit

# ── Load transcript data once at startup ──────────────────────────────────────
_file_paths: list = []
_transcripts: list = []
_data_loaded = False


def _load_data():
    global _file_paths, _transcripts, _data_loaded
    if _data_loaded:
        return
    try:
        with open(FILE_PATHS, 'rb') as f:
            _file_paths = pickle.load(f)
        with open(TRANSCRIPTS, 'rb') as f:
            _transcripts = pickle.load(f)
        _data_loaded = True
        logger.info('Loaded %d transcripts', len(_transcripts))
    except Exception as exc:
        logger.error('Failed to load transcript data: %s', exc)


_load_data()


# ── Views ──────────────────────────────────────────────────────────────────────

def index(request):
    history = request.session.get('chat_history', [])
    return render(request, 'guru/index.html', {'history': history})


@csrf_exempt
@require_http_methods(['POST'])
def ask(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    query = (data.get('query') or '').strip()
    if not query:
        return JsonResponse({'error': 'Query cannot be empty'}, status=400)

    if not _data_loaded:
        return JsonResponse(
            {'error': 'Transcript data not loaded. Please check server logs.'},
            status=503
        )

    try:
        retrieved = retrieve_transcripts(query, _file_paths, _transcripts, top_k=15)
        if not retrieved:
            return JsonResponse({'error': 'No relevant transcripts found'}, status=404)

        full_context = ' '.join(retrieved)
        limited_context = trim_to_token_limit(full_context, MAX_CONTEXT_TOKENS)
        answer = generate_response(query, limited_context)

        logger.info('Query: %s | Tokens: %d', query, count_tokens(limited_context))

        # ── Save to DB log ─────────────────────────────────────────────────────
        try:
            from guru_app.models import QueryLog
            QueryLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=query,
                answer=answer,
                tokens_used=count_tokens(limited_context),
            )
        except Exception as log_exc:
            logger.warning('Failed to save query log: %s', log_exc)

        # ── Save to session history ────────────────────────────────────────────
        history = request.session.get('chat_history', [])
        history.append({
            'query': query,
            'answer': answer,
            'timestamp': datetime.now().strftime('%d %b %Y, %H:%M'),
        })
        request.session['chat_history'] = history[-50:]
        request.session.modified = True

        return JsonResponse({
            'answer': answer,
            'query': query,
            'timestamp': datetime.now().strftime('%d %b %Y, %H:%M'),
        })

    except Exception as exc:
        logger.exception('Error processing query: %s', exc)
        return JsonResponse({'error': 'Internal server error. Please try again.'}, status=500)


@require_http_methods(['GET'])
def history(request):
    return JsonResponse({'history': request.session.get('chat_history', [])})


@csrf_exempt
@require_http_methods(['POST'])
def clear_history(request):
    request.session['chat_history'] = []
    request.session.modified = True
    return JsonResponse({'status': 'cleared'})