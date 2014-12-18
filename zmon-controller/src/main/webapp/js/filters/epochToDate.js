angular.module('zmon2App').filter('epochToDate', ['$filter', function($filter) {
    return function(epochSecs) {
        var epochStart = new Date(0); // 1 Jan 1970 00:00:00 UTC
        epochStart.setUTCSeconds(epochSecs);
        return $filter('date')(epochStart, 'yyyy-MM-dd HH:mm:ss');
    };
}]);
