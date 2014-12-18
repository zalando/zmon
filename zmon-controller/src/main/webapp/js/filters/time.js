angular.module('zmon2App').filter('time', ['$filter', function($filter) {
    return function(val) {
        return $filter('date')( new Date(val*1000), 'HH:mm');
    };
}]);
