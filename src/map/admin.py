from django.contrib import admin

from . import models


class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'row', 'column',
                    'ejudge_short_name', 'name', 'statement_file_name',
                    'solved_award', 'wrong_penalty', 'automatic_open_time'
                    )


admin.site.register(models.Problem, ProblemAdmin)


class AbstractTailAdmin(admin.ModelAdmin):
    list_display = ('id', 'row', 'column',
                    'ejudge_short_name', 'name', 'statement_file_name',
                    'automatic_open_time'
                    )


admin.site.register(models.AbstractBonus, AbstractTailAdmin)
admin.site.register(models.OpenAnyTileBonus, AbstractTailAdmin)
admin.site.register(models.GetTangerinesBonus, AbstractTailAdmin)
admin.site.register(models.CallMasterBonus, AbstractTailAdmin)


class RetrievedBonusAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bonus', 'used')


admin.site.register(models.RetrievedBonus, RetrievedBonusAdmin)


class TileStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'tile', 'user', 'status')
    search_fields = ('user__username', )
    list_filter = ('status', )

admin.site.register(models.TileStatus, TileStatusAdmin)

