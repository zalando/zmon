angular.module('zmon2App').filter('timespan', function() {
    /*
         * Converts a time range in ms to a human readable string
         * E.g. 10.000 => 10 seconds
         */
        return function(val, unit) {
            var milliseconds;
            if (unit == 's') {
                milliseconds = val * 1000;
            } else {
                milliseconds = val;
            }
            var temp = milliseconds / 1000;
            var years = Math.floor(temp / 31536000);
            if (years) {
                return years + 'y';
            }
            var days = Math.floor((temp %= 31536000) / 86400);
            if (days) {
                return days + 'd';
            }
            var hours = Math.floor((temp %= 86400) / 3600);
            if (hours) {
                return hours + 'h';
            }
            var minutes = Math.floor((temp %= 3600) / 60);
            if (minutes) {
                return minutes + 'm';
            }
            var seconds = Math.floor(temp % 60);
            if (seconds) {
                return seconds + 's';
            }
            return milliseconds.toFixed(0) + 'ms'; //'just now'
        };

});