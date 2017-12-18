from django.db import models
from django.db.transaction import atomic
import django.db.migrations.writer
from django.conf import settings
from django.contrib.auth import models as auth_models

import telegram
import djchoices
import polymorphic.models
from relativefilepathfield.fields import RelativeFilePathField


class AbstractTile(polymorphic.models.PolymorphicModel):
    row = models.PositiveIntegerField(help_text='Номер строки')

    column = models.PositiveIntegerField(help_text='Номер колонки')

    ejudge_short_name = models.CharField(db_index=True, max_length=255)

    name = models.CharField(max_length=255)

    statement_file_name = RelativeFilePathField(
        path=django.db.migrations.writer.SettingsReference(
            settings.PROBLEMS_STATEMENTS_DIR,
            'PROBLEMS_STATEMENTS_DIR'
        ),
        match='.*\.pdf'
    )

    automatic_open_time = models.PositiveIntegerField(
        help_text='Время в минутах, после которого задача откроется автоматически. Если NULL, то не откроется',
        null=True,
        blank=True,
        default=None
    )

    def _add_status(self, user, status):
        qs = TileStatus.objects.filter(user=user, tile=self, status=status)
        if qs.exists():
            return
        TileStatus(user=user, tile=self, status=status).save()

    def open_for_user(self, user):
        return self._add_status(user, TileStatusEnum.OPENED)

    def mark_as_read_by_user(self, user):
        return self._add_status(user, TileStatusEnum.READ)

    def mark_as_tried_by_user(self, user):
        if TileStatus.get_tile_status(self, user) == TileStatusEnum.CLOSED:
            return
        return self._add_status(user, TileStatusEnum.TRIED)

    def mark_as_solved_by_user(self, user):
        if TileStatus.get_tile_status(self, user) == TileStatusEnum.CLOSED:
            return
        return self._add_status(user, TileStatusEnum.SOLVED)


class Problem(AbstractTile):
    solved_award = models.PositiveIntegerField(help_text='Приз за правильное решение задачи')

    wrong_penalty = models.PositiveIntegerField(help_text='Штраф за неправильную попытку')

    def __str__(self):
        return 'Problem %s at (%d, %d)' % (self.ejudge_short_name, self.row, self.column)


class AbstractBonus(AbstractTile):
    def use_bonus(self, user, selected_tile_id):
        try:
            telegram_text = 'Команда %s воспользовался бонусом №%d (%s)' % (
                (user.first_name + ' ' + user.last_name + ', ' + user.username),
                self.id,
                self.get_real_instance_class().__name__
            )

            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot.sendMessage(chat_id=settings.TELEGRAM_CHAT_ID, text=telegram_text)
        except:
            pass
        return True

    def __str__(self):
        return 'Bonus %s at (%d, %d)' % (self.get_real_instance_class().__name__, self.row, self.column)


class OpenAnyTileBonus(AbstractBonus):
    def get_description(self):
        return 'открыть любой шестиугольник'

    def get_used_description(self):
        return 'Задача открыта. Обновите страницу'

    def use_bonus(self, user, selected_tile_id):
        tile = AbstractTile.objects.filter(pk=selected_tile_id).first()
        if tile is None:
            return False
        status = TileStatus.get_tile_status(tile, user)
        if status != TileStatusEnum.CLOSED:
            return False

        tile.open_for_user(user)
        return True


class GetTangerinesBonus(AbstractBonus):
    def get_description(self):
        return 'получить мандаринки на всю команду'

    def get_used_description(self):
        return 'Скоро вам принесут мандаринки :-)'


class GetAnyTestBonus(AbstractBonus):
    pass


class CallMasterBonus(AbstractBonus):
    def get_description(self):
        return 'проконсультироваться с Андреем Сергеевичем по любой задаче и любому вопросу'

    def get_used_description(self):
        return 'Андрей Сергеевич скоро подойдёт.'


class OpenWideLocalityBonus(AbstractBonus):
    pass


class TileStatusEnum(djchoices.DjangoChoices):
    CLOSED = djchoices.ChoiceItem(0, 'Closed')
    OPENED = djchoices.ChoiceItem(1, 'Opened')
    READ = djchoices.ChoiceItem(2, 'Read')
    TRIED = djchoices.ChoiceItem(3, 'Tried')
    SOLVED = djchoices.ChoiceItem(4, 'Solved')


class TileStatus(models.Model):
    tile = models.ForeignKey(AbstractTile, related_name='statuses')

    user = models.ForeignKey(auth_models.User, related_name='tiles_statuses')

    status = models.PositiveIntegerField(
        choices=TileStatusEnum.choices,
        validators=[TileStatusEnum.validator],
        db_index=True
    )

    class Meta:
        ordering = ['status']

    @classmethod
    def get_tile_status(cls, tile, user):
        qs = cls.objects.filter(tile=tile, user=user)
        if qs.exists():
            return qs.aggregate(models.Max('status'))['status__max']
        return TileStatusEnum.CLOSED


class RetrievedBonus(models.Model):
    user = models.ForeignKey(auth_models.User, related_name='bonuses')

    bonus = models.ForeignKey(AbstractBonus, related_name='retrieved')

    used = models.BooleanField(default=False, help_text='Использован ли бонус командой')

    @classmethod
    def user_retrieved_bonus(cls, user, bonus):
        with atomic():
            qs = cls.objects.filter(user=user, bonus=bonus)
            if qs.exists():
                return
            bonus = cls(user=user, bonus=bonus)
            bonus.save()
        return bonus

    class Meta:
        unique_together = ('user', 'bonus')
