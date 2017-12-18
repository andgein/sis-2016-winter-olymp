import datetime
import collections

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User

from ejudge.database import EjudgeDatabase, RunStatus
from ejudge.models import Contest
from map.models import AbstractTile, Problem


class Monitor:
    def __init__(self, solved_problems, tries, scores, is_frozen):
        self.solved_problems = solved_problems
        self.tries = tries
        self.scores = scores
        self.is_frozen = is_frozen

        self.sorted_users_ids = sorted(self.scores.keys(),
                                       key=lambda u: (-self.scores[u], -len(self.solved_problems[u]), u))
        self.users_names = {
            u.info.ejudge_user_id: (u.last_name + ' ' + u.first_name).strip()
            for u in User.objects.filter(info__ejudge_user_id__in=self.sorted_users_ids)
        }


class MonitorBuilder:
    def __init__(self):
        self.contest = Contest(settings.EJUDGE_SERVE_CFG)
        self.ejudge_database = EjudgeDatabase()

    def get_user_score(self, user):
        runs = self.ejudge_database.get_runs_by_user(user)
        monitor = self._build_monitor_by_runs(runs)

        return monitor.scores[user.info.ejudge_user_id]

    def build(self, freeze_if_frozen=True):
        time = datetime.datetime.now()
        if freeze_if_frozen and self.contest.fog_time <= time < self.contest.unfog_time:
            time = self.contest.fog_time
        runs = self.ejudge_database.get_runs(time)

        monitor = self._build_monitor_by_runs(runs)
        if not freeze_if_frozen:
            monitor.is_frozen = False
        return monitor

    def _build_monitor_by_runs(self, runs):
        tiles_by_short_name = {t.ejudge_short_name: t for t in AbstractTile.objects.all()}
        scores = collections.defaultdict(int)
        solved_problems = collections.defaultdict(list)
        tries = collections.defaultdict(int)
        for run in runs:
            if run.problem_id in solved_problems[run.user_id]:
                continue
            if run.status != RunStatus.OK:
                tries[(run.user_id, run.problem_id)] += 1
                continue

            solved_problems[run.user_id].append(run.problem_id)
            ejudge_problem = self.contest.problems[run.problem_id]

            # We don't have tail for this ejudge problem
            if ejudge_problem.short_name not in tiles_by_short_name:
                continue

            tile = tiles_by_short_name[ejudge_problem.short_name]
            if isinstance(tile, Problem):
                penalty = tile.wrong_penalty * tries[(run.user_id, run.problem_id)]
                penalty = min(penalty, int(settings.MAXIMUM_PENALTY * tile.solved_award))
                scores[run.user_id] += tile.solved_award - penalty
        is_frozen = self.contest.fog_time <= datetime.datetime.now() < self.contest.unfog_time
        return Monitor(solved_problems, tries, scores, is_frozen)


def index(request):
    builder = MonitorBuilder()
    if request.user.is_staff:
        freeze = False
    else:
        freeze = True
    monitor = builder.build(freeze)
    return render(request, 'monitor/monitor.html', {
        'monitor': monitor
    })


@login_required
def admin_monitor(request):
    if not request.user.is_staff:
        return HttpResponseNotFound()
    monitor = MonitorBuilder().build(False)
    return render(request, 'monitor/monitor.html', {
        'monitor': monitor
    })
