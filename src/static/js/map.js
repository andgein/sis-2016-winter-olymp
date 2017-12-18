$(document).ready(function(){
    var $sidebar = $('.sidebar');

    var showTile = function (tile) {
        $sidebar.find('> div').hide();
        $sidebar.find('> .sidebar__tile').show().html(tile);
    };

    $('.map .tile:not(.empty)').click(function(){
        var $tile = $(this);

        if ($('.map').hasClass('select-tile'))
        {
            var tileId = $tile.data('id');
            var url = $('.map').data('url').replace('ID', tileId);
            $.getJSON(url, {}, function(data){
               if (data.status == 'ok') {
                   $('.map').removeClass('select-tile');
               }
               $('.bonus-status').text(data.message)
            });

            return;
        }

        $sidebar.find('> div').hide();
        $sidebar.find('> .sidebar__loading').show();
        $.get($tile.data('readUrl'), {}, function (tileInfo){
            showTile(tileInfo);
        });
    });

    $sidebar.on('click', '.bonus-button', function(){
        var isTileSelection = $(this).data('tileSelection');
        var url = $(this).data('url');
        if (! isTileSelection) {
            $.get(url, function (data) {
                $sidebar.find('.bonus-status').html(data);
            });
        } else {
            $('.map').addClass('select-tile');
            $('.bonus-status').html('Кликните на закрытой задаче, чтобы открыть её');
            $('.map').data('url', url);
        }
    });
});
