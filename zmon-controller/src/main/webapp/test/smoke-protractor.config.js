exports.config = {
    // The address of a running selenium server.
    seleniumAddress: 'http://z-selenium-hub.zalando:4444/wd/hub',

    // Capabilities to be passed to the webdriver instance.
    // If you want to use PhantomJS as browser please intall PhantomJS globally
    // npm install -g phantomjs
    capabilities: {
        'browserName': 'chrome'
    },

    // Testing framework
    framework: 'jasmine',

    // Exporting results of test to JUnit XML format

    // jasmine.JUnitXmlReporter(savePath, consolidate, useDotNotation, filePrefix):

    // @param {string} savePath
    //      where to save the files
    // @param {boolean} consolidate
    //      whether to save nested describes within the same file as their parent; default: true
    // @param {boolean} useDotNotation
    //      whether to separate suite names with dots rather than spaces (ie "Class.init" not "Class init"); default: true
    // @param {string} filePrefix
    //      is the string value that is prepended to the xml output file; default: 'TEST-'

    onPrepare: function() {
        require('jasmine-reporters');
        reporter = new jasmine.JUnitXmlReporter('./test/ci/', true, true, 'ZMON2-SMOKE');
        jasmine.getEnv().addReporter(reporter);
    },

    // Spec patterns are relative to the location of the spec file. They may
    // include glob patterns.
    specs: ['./smoke/**/*.spec.js'],

    // URL of project
    baseUrl: 'http://localhost:33400/',

    // Options to be passed to Jasmine-node.
    jasmineNodeOpts: {
        showColors: true,
        isVerbose: true,
        defaultTimeoutInterval: 360000
    }
};
