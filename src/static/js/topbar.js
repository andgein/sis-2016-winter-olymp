$(document).ready(function(){
    var $topbar = $('.topbar');
    var $sidebar = $('.sidebar');

    $topbar.find('.button__logout').click(function(){
       window.location.replace($(this).data('url'));
    });

    $topbar.find('.button__monitor').click(function(){
        var url = $(this).data('url');

        $sidebar.find('> div').hide();
        $sidebar.find('> .sidebar__loading').show();
        $.get(url, {}, function(monitor){
            $sidebar.find('> div').hide();
            $sidebar.find('> .sidebar__monitor').show();
            $sidebar.find('.sidebar__monitor .monitor').html(monitor);
        });
    });
});
