// Karma configuration
// Generated on Thu Mar 20 2014 11:24:18 GMT+0100 (CET)

module.exports = function(config) {
    config.set({

        // base path, that will be used to resolve files and exclude
        basePath: '../',


        // frameworks to use
        frameworks: ['jasmine'],


        // list of files / patterns to load in the browser
        files: [
            'lib/jquery/jquery.min.js',
            'lib/angularjs/angular.min.js',
            'lib/angularjs/angular-mocks.js',
            'lib/angularjs/angular-route.min.js',
            'lib/angularjs/angular-cookies.min.js',
            'lib/angularjs/angular-sanitize.min.js',
            'lib/angular-local-storage/angular-local-storage.min.js',
            'lib/bootstrap/bootstrap.min.js',
            'lib/ui-bootstrap/ui-bootstrap.min.js',
            'lib/lodash/lodash.min.js',
            'js/app.js',
            'js/filters/*.js',
            'js/services/*.js',
            'js/directives/*.js',
            'js/controllers/*.js',
            'test/unit/*.spec.js'
        ],

        plugins: [
            'karma-chrome-launcher',
            'karma-firefox-launcher',
            'karma-jasmine',
            'karma-phantomjs-launcher',
            'karma-junit-reporter'
        ],

        // list of files to exclude
        exclude: [
        ],

        // test results reporter to use
        // possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
        reporters: ['progress', 'junit'],

        junitReporter: {
            outputFile: 'test/ci/test-results.xml',
            suite: ''
        },

        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel: config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: false,


        // Start these browsers, currently available:
        // - Chrome
        // - ChromeCanary
        // - Firefox
        // - Opera (has to be installed with `npm install karma-opera-launcher`)
        // - Safari (only Mac; has to be installed with `npm install karma-safari-launcher`)
        // - PhantomJS
        // - IE (only Windows; has to be installed with `npm install karma-ie-launcher`)
        browsers: ['PhantomJS'],


        // If browser does not capture in given timeout [ms], kill it
        captureTimeout: 60000,


        // Continuous Integration mode
        // if true, it capture browsers, run tests and exit
        singleRun: true
    });
};
