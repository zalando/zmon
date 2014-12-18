angular.module('zmon2App').filter('markdown', function ($sanitize) {
    var converter = new Showdown.converter();
    return function (value) {
        var html = converter.makeHtml(value || '');
        html = '<div class="markdown">' + html + '</div>';
        return $sanitize(html);
    };
});
