var P = protractor.getInstance();
var LoginPage = function() {};

LoginPage.prototype.J_USER_NAME = 'hjacobs'
LoginPage.prototype.J_PASSWORD = 'test'

LoginPage.prototype.login = function() {
    browser.ignoreSynchronization = true;

    browser.get('/login.jsp');

    element(by.css('[name="j_username"]')).sendKeys(this.J_USER_NAME);
    element(by.css('[name="j_password"]')).sendKeys(this.J_PASSWORD);
    element(by.css('button')).click();
};

LoginPage.prototype.logout = function() {
    browser.ignoreSynchronization = true;

    element(by.css('.auth-user')).click().then(function() {
        element(by.css('a[href$="logout"]')).click();
    });
};

module.exports = LoginPage;