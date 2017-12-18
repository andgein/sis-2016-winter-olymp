import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse, HttpResponseNotFound, HttpResponse
from django.shortcuts import render, get_object_or_404

from ejudge.database import EjudgeDatabase, RunStatus
from ejudge.models import Contest
from map.models import AbstractTile, TileStatusEnum
from monitor.views import MonitorBuilder
from . import models


@login_required
def index(request):
    update_tile_statuses(request.user)

    tiles = models.AbstractTile.objects.all()

    tile_statuses = get_tile_statuses(request.user, tiles)

    max_row = max((tile.row for tile in tiles), default=0)
    map = []
    for row in range(max_row + 1):
        map.append([])
        tiles_on_row = list(filter(lambda t: t.row == row, tiles))
        max_column = max((tile.column for tile in tiles_on_row), default=0)
        tiles_by_columns = {tile.column: tile for tile in tiles_on_row}
        for column in range(max_column + 1):
            if column in tiles_by_columns:
                tile = tiles_by_columns[column]
                tile.status = tile_statuses[tile.id]

                if tile.status == TileStatusEnum.CLOSED:
                    open_time = settings.CONTEST_START_TIME + datetime.timedelta(minutes=tile.automatic_open_time)
                    # TODO: check date format
                    tile.html_title = 'Откроется автоматически в ' + open_time.strftime('%H:%m')

                map[-1].append(tile)
            else:
                map[-1].append(None)

    score = MonitorBuilder().get_user_score(request.user)

    return render(request, 'map/map.html', {
        'map': map,
        'score': score,
    })


def get_tile_statuses(user, tiles):
    tile_statuses = {status.tile_id: status.status for status in models.TileStatus.objects.filter(user=user)}
    return {tile.id: tile_statuses.get(tile.id, models.TileStatusEnum.CLOSED) for tile in tiles}


def open_locality(user, tile):
    neighbors = [(0, -1), (0, 1)]
    if tile.row % 2 == 0:
        neighbors.extend([(-1, -1), (-1, 0), (1, -1), (1, 0)])
    else:
        neighbors.extend([(-1, 0), (-1, 1), (1, 0), (1, 1)])

    for neighbor in neighbors:
        neighbor_row = tile.row + neighbor[0]
        neighbor_column = tile.column + neighbor[1]
        qs = AbstractTile.objects.filter(row=neighbor_row, column=neighbor_column)
        if qs.exists():
            n = qs.first()
            if n is not None:
                n.open_for_user(user)


def update_tile_statuses(user):
    update_tile_statuses_from_ejudge_runs(user)
    update_tile_statuses_from_automatic_opens(user)


def update_tile_statuses_from_ejudge_runs(user):
    contest = Contest(settings.EJUDGE_SERVE_CFG)
    ejudge_database = EjudgeDatabase()
    tiles_by_short_name = {t.ejudge_short_name: t for t in AbstractTile.objects.all()}
    for run in ejudge_database.get_runs_by_user(user):
        if run.status == RunStatus.IGNORED:
            continue
        # We don't have tile for this ejudge problem
        if contest.problems[run.problem_id].short_name not in tiles_by_short_name:
            continue
        tile = tiles_by_short_name[contest.problems[run.problem_id].short_name]
        tile.mark_as_tried_by_user(user)
        if run.status == RunStatus.OK:
            tile.mark_as_solved_by_user(user)
            if isinstance(tile, models.AbstractBonus):
                models.RetrievedBonus.user_retrieved_bonus(user, tile)
            open_locality(user, tile)


def update_tile_statuses_from_automatic_opens(user):
    current_minute = (datetime.datetime.now() - settings.CONTEST_START_TIME).total_seconds() // 60
    for tile in AbstractTile.objects.filter(automatic_open_time__lte=current_minute):
        tile.open_for_user(user)


@login_required
def read_tile(request, tile_id):
    tile = get_object_or_404(models.AbstractTile, pk=tile_id)

    if models.TileStatus.get_tile_status(tile, request.user) == models.TileStatusEnum.CLOSED:
        return HttpResponseNotFound()

    tile.mark_as_read_by_user(request.user)

    tile = tile.get_real_instance()

    if type(tile) is models.Problem:
        tile_type = 'problem'
    elif isinstance(tile, models.AbstractBonus):
        tile_type = 'bonus'
        tile.is_retrieved = tile.retrieved.filter(user=request.user).first()
        tile.is_tile_selection = isinstance(tile, models.OpenAnyTileBonus)
    else:
        raise Exception('Unknown tile_type for %s' % tile)

    return render(request, 'map/tile.html', {
        'tile': tile,
        'type': tile_type
    })


@login_required
def read_statement(request, tile_id):
    tile = get_object_or_404(models.AbstractTile, pk=tile_id)

    if models.TileStatus.get_tile_status(tile, request.user) == models.TileStatusEnum.CLOSED:
        return HttpResponseNotFound()

    tile.mark_as_read_by_user(request.user)

    statement_path = tile.get_statement_file_name_abspath()
    with open(statement_path, 'rb') as statement_file:
        statement_content = statement_file.read()
        return HttpResponse(statement_content, content_type='application/pdf')


@login_required
def use_bonus(request, tile_id, selected_tile_id):
    tile = get_object_or_404(models.AbstractTile, pk=tile_id)

    if not isinstance(tile, models.AbstractBonus):
        return HttpResponseNotFound()

    qs = models.RetrievedBonus.objects.filter(user=request.user, bonus=tile)
    if not qs.exists():
        return HttpResponseNotFound()

    bonus = qs.first()
    is_used = bonus.used
    if not is_used:
        bonus_used = tile.use_bonus(request.user, selected_tile_id)
        if bonus_used:
            bonus.used = True
            bonus.save()
            if isinstance(tile, models.OpenAnyTileBonus):
                return JsonResponse({
                    'status': 'ok',
                    'message': tile.get_used_description()
                })
        else:
            return JsonResponse({
                'status': 'fail',
                'message': 'Эта зачача уже открыта для вас. Выберите другую'
            })
    else:
        if isinstance(tile, models.OpenAnyTileBonus):
            return JsonResponse({
                'status': 'ok',
                'message': 'Вы уже воспользовались этим бонусом'
            })

    return render(request, 'map/use_bonus.html', {
        'is_used': is_used,
        'tile': tile
    })
