angular.module('zmon2App').filter('encodeUri', function() {
    return function (val) {
        if (val != null && (typeof val === 'object' || typeof val === 'array')) {
            val = JSON.stringify(val, null, 0);
        }

        return window.encodeURI(val);
    }
});

angular.module('zmon2App').filter('encodeUriComponent', function() {
    return function (val) {
        if (val != null && (typeof val === 'object' || typeof val === 'array')) {
            val = JSON.stringify(val, null, 0);
        }

        return window.encodeURIComponent(val);
    }
});