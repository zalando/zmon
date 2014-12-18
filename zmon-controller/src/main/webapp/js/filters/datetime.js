angular.module('zmon2App').filter('datetime', ['$filter', function($filter) {
        return function(val) {
            return $filter('date')( new Date(val*1000), 'yyyy-MM-dd HH:mm');
        };
}]);