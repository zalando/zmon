angular.module('zmon2App').filter('prettify', function() {
    /*
         * Given a value, which could be an object, it transforms it as follows:
         *  if it's an object, stringify it and then proceed with one of the following
         *  if it's an integer, it is returned intact
         *  if it's a float, it gets trancuated to DEFAULT_NUMBER_DECIMALS precision
         *  if it's a string, truncate it to DEFAULT_MAX_LENGTH if it's larger than that
         */
        var DEFAULT_MAX_LENGTH = 100;
        var DEFAULT_NUMBER_DECIMALS = 2;
        return function(value, length) {
            if (typeof value === 'undefined') {
                return '';
            }

            if (typeof length === 'undefined') {
                length = DEFAULT_MAX_LENGTH;
            }

            // Convert to string in case of object
            if (typeof value === 'object') {
                value = JSON.stringify(value);
            } else if (typeof value === 'number') {

                // It's a number; if integer return as is,
                if (value % 1 === 0) {
                    return value;
                }
                return parseFloat(value).toFixed(DEFAULT_NUMBER_DECIMALS);

            } else if(typeof value === 'boolean'){
                return value.toString();

            }
            
            if (value.length <= length) {
                // It's a string but shorter than max allowed length; no truncate; return intact;
                return value;

            } else {
                value = value.substr(0, length);
                return value + '...';
            }
        };
});