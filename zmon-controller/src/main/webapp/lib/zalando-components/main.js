define('zalandoXComponentsModule', [
        'angular'
    ],
    function (angular) {
        return angular.module('zalandoXComponents', []);
    }
);

define('zalandoComponents', [
        'zalandoXComponentsModule',
        './zalando-x-components'
    ],
    function (module) {
        return module;
    }
);
