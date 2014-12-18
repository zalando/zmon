var P = protractor.getInstance();
var Auth = function() {};

Auth.prototype.login = function(cb) {
    browser.ignoreSynchronization = true;

    browser.get('/login.jsp');
    // element(by.className('auth-action')).click();

    element(by.css('[name="j_username"]')).sendKeys('elauria');
    element(by.css('[name="j_password"]')).sendKeys('Test12345');
    element(by.css('button')).click().then(function() {
        if(cb) cb(true);
        browser.ignoreSynchronization = false;
    });
};

Auth.prototype.logout = function(cb) {
    browser.ignoreSynchronization = true;

    element(by.css('.auth-user')).click().then(function() {
        element(by.css('a[href$="logout"]')).click().then(function() {
            if(cb) cb(true);
            browser.ignoreSynchronization = false;
        });
    });
};

module.exports = Auth;
