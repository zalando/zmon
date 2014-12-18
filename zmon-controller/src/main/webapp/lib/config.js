require.config({
    optimizeCss: 'none',
    baseUrl: '/app',

    packages: [{
        name: 'zalandoComponents',
        location: '../lib/zalando-components'
    }],

    paths: {
        jquery: '../lib/jquery/jquery.min',
        angular: '../lib/angularjs/angular',
        angularSanitize: '../lib/angularjs/angular-sanitize',
        uiBootstrap: '../lib/ui-bootstrap/ui-bootstrap',
        domReady: '../lib/requirejs/domReady',
        angularResource: '../lib/angularjs/angular-resource',
        angularRoute: '../lib/angularjs/angular-route',
        angularAnimate: '../lib/angularjs/angular-animate',
        zalandoRpc: '../lib/zalando-rpc/zalando-rpc',
        spin: '../lib/directives/spin',
        moment: '../lib/moment/moment'
    },

    shim: {
        angular: {
            deps: ['jquery'],
            exports: 'angular'
        },
        uiBootstrap: {
            deps: ['angular']
        },
        angularResource: {
            deps: ['angular'],
            exports: 'ngResource'
        },
        angularSanitize: {
            deps: ['angular']
        },
        angularRoute: {
            deps: ['angular'],
            exports: 'ngRoute'
        },
        angularAnimate: {
            deps: ['angular'],
            exports: 'ngAnimate'
        },
        zalandoRpc: {
            deps: ['angular']
        }
    }
});
