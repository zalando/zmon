angular.module('zmon2App').directive('priority', function() {
    return {
        restrict: 'E',
        templateUrl: 'templates/priority.html',
        replace: true,
        scope: {
            prio: '='
        },
        link: function(elem, attrs, scope) {

        }
    };
});