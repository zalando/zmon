exports.config = {
    // The address of a running selenium server.
    seleniumAddress: 'http://localhost:4444/wd/hub',

    // Capabilities to be passed to the webdriver instance.
    // If you want to use PhantomJS as browser please intall PhantomJS globally
    // npm install -g phantomjs
    capabilities: {
        'browserName': 'chrome'
    },

    // Spec patterns are relative to the location of the spec file. They may
    specs: ['./e2e/**/*.spec.js'],

    // URL of project
    baseUrl: 'http://localhost:8080/',

    // Options to be passed to Jasmine-node.
    jasmineNodeOpts: {
        showColors: true,
        isVerbose: true,
        defaultTimeoutInterval: 60000
    }
};
