angular.module('zmon2App').directive('status', function() {
    return {
        restrict: 'E',
        templateUrl: 'templates/status.html',
        replace: true,
        scope: {
            status: '='
        },
        link: function(elem, attrs, scope) {

        }
    };
});