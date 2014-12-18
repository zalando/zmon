angular.module('zmon2App').filter('downtimeReasons', function($filter) {
	var now = new Date().getTime() / 1000;
	return function(downtimes) {
		var reasons = '';
		_.each(downtimes, function(nextDowntime) {
			if (nextDowntime.start_time <= now && now <= nextDowntime.end_time) {
				reasons += '[' + $filter('epochToDate')(nextDowntime.start_time) + ' > ' + $filter('epochToDate')(nextDowntime.end_time) + ']: ' + nextDowntime.comment + '; ';
			}
		});
		return reasons;
	};
});